---
created: 2026-08-11 08:30
status: Implemented
project: "[[10_Projects/sapo-invoice/README]]"
---

# Điều tra sự cố auto-invoice trên prod (sapo-einvoice-service)

Repo [[10_Projects/sapo-invoice/omni-einvoice-service-tong-quan|sapo-einvoice-service]] có sẵn skill `einvoice-investigate` (`.claude/skills/einvoice-investigate/`) — user gõ câu ngắn kiểu *"tại sao đơn {code} tenant {tenantId} không xuất hóa đơn tự động"*, agent tự chọn playbook và truy DB qua MCP read-only. Note này giữ **phần tri thức vận hành không nằm trong code**, để dùng được cả khi không mở repo.

Phạm vi skill: **chỉ điều tra + đề xuất**. Không Edit/Write code, không INSERT/UPDATE/DELETE.

## Playbook hiện có

| Triệu chứng | File |
|---|---|
| Đơn không được xuất hóa đơn tự động (HĐ mới) | `playbooks/auto-invoice-not-issued.md` |
| Đơn trả hàng/hủy không ra hóa đơn điều chỉnh tự động | `playbooks/auto-adjustment-invoice-not-issued.md` |

## MCP server & mapping shard — quy tắc tuyệt đối

| Server | Dùng cho |
|---|---|
| `db_einvoice_prod_readonly` | DB einvoice prod — **không chia shard** |
| `db_einvoice_staging` | DB einvoice staging |
| `db_order_prod_shard1/2/3` | DB order, **chọn theo `tenantId`** |

| Shard | Khoảng `tenantId` |
|---|---|
| shard1 | 0 – 549 999 |
| shard2 | 550 000 – 759 999 |
| shard3 | 760 000 – 2 000 000 |

⛔ **Một tenant chỉ nằm trên đúng 1 shard.** Query shard suy ra mà rỗng thì **không** được dò 2 shard còn lại — rỗng nghĩa là `code`/`orderId`/`tenantId` sai (hay gặp: CSKH đưa nhầm mã đơn) → dừng, hỏi lại user.

## Quy tắc truy DB

- **Chỉ SELECT**, luôn lọc `TenantId`, luôn có `WHERE` + `TOP`/`ORDER BY`
- **Luôn query theo index.** Cột không index (`orders.ModifiedOn`, `Status`, khoảng thời gian) không được làm điều kiện lọc chính; chỉ tinh chỉnh sau khi điều kiện index đã thu nhỏ kết quả. Không có cách đi qua index → dừng, xin thêm `orderId`/`Id` thay vì chạy liều (dễ timeout / quét bảng).
- Bảng order dùng cột **PascalCase**: `Id`, `TenantId`, `Code`, `RootId`, `Data`, `CreatedOn`
- Nhận diện định danh **theo đúng chữ user dùng**: nói "code" → tra `orders.Code`, nói "order id" → tra `orders.Id`, không rõ → hỏi lại. `Code` không có format cố định (18 chữ số, `260802A8BE3KF0`, số ngắn…) nên **không được suy "chuỗi này trông không giống Code" rồi tra cột khác**. Query rỗng → dừng, **không** thử `ReferenceNumber`/`Token`/`LIKE '%...%'`.

## ⚠️ Múi giờ — dễ sai 7 tiếng

- DB lưu **UTC** (`CreatedOn`/`ModifiedOn` khớp `GETUTCDATE()`)
- Đồng hồ OS server để **giờ VN** → `GETDATE()` = giờ VN, `GETUTCDATE()` = UTC
- So mốc "hiện tại" trong SQL: **luôn `GETUTCDATE()`**, không `GETDATE()`
- User nói theo giờ VN → lọc thời gian phải **trừ 7h**; báo cáo lại thì **cộng 7h** và ghi rõ "(giờ VN)"

(Khác với gotcha `UTC_TIMESTAMP()` bên `sapo-invoice-admin-service` — kia là MySQL, đây là SQL Server. Cùng bản chất "DB lưu UTC, đừng dùng hàm giờ local".)

## 9 "gate" khiến đơn không được xuất hóa đơn tự động

Duyệt theo thứ tự trong `service/autoinvoice/impl/AutoInvoiceExecutionServiceImpl.processAutoInvoiceWithRetry` (~dòng 87–216). Entry: `consumer/kafka/OrderConsumer.java:54`, chỉ chạy khi `ENABLE_ORDER_CONSUMER=true`.

| # | Gate | Vị trí | Dấu hiệu |
|---|---|---|---|
| 1 | Không có config / config tắt | `:96`, `:106` | `AutoInvoiceConfigs` rỗng hoặc `Enabled=0` |
| 2 | Config không khớp chi nhánh đơn | `:110–130` | `activeConfig=null` → return, **không ghi log** (khó thấy nhất) |
| 3 | Không bật đúng luồng | `resolveFlowContext :218` | đơn thường cần `AutoNewInvoiceEnabled=1`; đơn trả/hủy cần `AutoAdjustmentInvoiceEnabled=1` |
| 4 | Đã từng fail terminal | `:146` | `AutoInvoiceResults` đã có `*_fail` cho flow đó → skip (chống lặp vô hạn) |
| 5 | Chưa tới ngày áp dụng | `isFlowDateEligible :285` | `order.CreatedOn < OrderDateFrom`, hoặc ngày trả `< ReturnDateFrom` |
| 6 | Đơn đã có HĐ khác draft | `:176` | coi như đã xử lý → skip |
| 7 | Lệch template | `:183–195` | serial hiện có nhưng template không khớp config |
| 8 | Không thỏa điều kiện | `evaluateConditions :426` | **AND toàn bộ** điều kiện; điều kiện có `ConditionValue` rỗng thì bỏ qua |
| 9 | Thực thi nhưng fail | `executeAutoInvoice :569` | chưa kết nối SI (`validateSapoInvoiceConnection :1108`) → `created_fail`; dựng request lỗi / provider trả `FAILED` → retry 3 lần ngắn + hàng đợi 5 phút → `published_fail` |

### ⛔ Cạm bẫy `received_status` (gate #8)

**Không** được kết luận "đơn có `received_status = received` ⇒ thỏa". Phải đi đúng nhánh `evaluateReceivedStatus :517`:

1. Lấy `source_id` của đơn → xác định có phải **sàn TMĐT** không: `source.init == true` **và** tên nguồn chứa `shopee/tiki/lazada/tiktokshop` (`isEcommerce :531`)
2. **Là sàn** → dùng `checkReferenceStatusDelivered :539`: yêu cầu `fulfillments[].shipment.reference_status == "delivered"`, **bỏ qua** `received_status` nội bộ. `reference_status` null/khác `delivered` ⇒ **gate FAIL, không xuất** — kể cả khi đơn đã `completed` và `received_status = received`
3. **Không phải sàn** → mới so `received_status == "received"`

→ Khi đọc `OrderLogs.Data`, luôn trích **cả** `source_id` **và** `fulfillments[].shipment.reference_status`.

## Trình tự truy vấn

1. **Đơn** — shard theo `tenantId`, `dbo.orders`: lấy `Id`, `LocationId`, `Status`, `SourceId`, `CreatedOn`
2. **Lịch sử đơn** — `dbo.OrderLogs` theo `RootId = orderId`, **`ORDER BY CreatedOn`, KHÔNG `ORDER BY Id`** (Id chạm trần kiểu số sẽ được cấp tiếp bằng **giá trị âm** → không tăng đơn điệu theo thời gian). Đọc JSON `Data`: `status`, `payment_status`, `received_status`, `return_status`, `source_id`, `create_invoice`, `fulfillments[].shipment.reference_status`
3. **Cấu hình** — `db_einvoice_prod_readonly`, `dbo.AutoInvoiceConfigs` (+ điều kiện theo `ConfigId`, info config để biết chi nhánh & template)
4. **Audit log cấu hình** — ai/khi nào đổi config
5. **Kết quả đã ghi** — `AutoInvoiceResults` cho đơn này, cột `Description` chứa lý do fail

## Định dạng kết luận

Tóm tắt → Điều tra (query rút gọn + số liệu + trích `path:line`) → Nguyên nhân (**chặn ở gate số mấy**, mức độ chắc chắn) → Đề xuất + đánh đổi → Cần user xác nhận gì. Đụng DB thì nhắc "deploy DB trước rồi code", và **không tự chạy** trên prod.

## Liên kết

- [[10_Projects/sapo-invoice/omni-einvoice-service-tong-quan]]
- [[10_Projects/sapo-invoice/epic-65-auto-invoice-order-name]] — UI hiển thị đơn thất bại trong popup Auto Invoice
