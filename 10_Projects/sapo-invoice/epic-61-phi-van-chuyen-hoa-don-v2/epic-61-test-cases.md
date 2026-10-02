---
created: 2026-08-12 15:30
status: Draft — dựng trước khi Cursor implement, chưa chạy trên code thật
project: "[[10_Projects/sapo-invoice/README]]"
---

# Test case Epic #61 — Phí vận chuyển hóa đơn V2

- SRS: [[epic-61-phi-van-chuyen-hoa-don-v2]] (v0.6) · Prompt Cursor: [[epic-61-cursor-prompt-implement]]
- Dựng **trước khi code chạy** — theo đúng BR01–BR10 + AC của UC-01/UC-02 trong SRS v0.6. Chưa verify trên môi trường thật, số dòng/tên hàm trong "Cách đối chiếu" là tham chiếu code hiện tại, có thể lệch sau khi Cursor sửa.

> [!note] Tên field trên API là **`shipping_line`** (không phải `is_shipping_line` như SRS ≤ v0.6 ghi) — đổi 2026-08-20 cho khớp tên field Java `shippingLine`. Cột DB vẫn là `IsShippingLine`.

## ✅ B0 đã resolve (2026-08-20, BA) — `delivery_fee` là **object đơn**

**BA xác nhận: một đơn hàng chỉ có ĐÚNG MỘT phí giao hàng.** Kết luận ghi ngày 2026-08-12 ("là mảng, gộp Σ") **sai và đã bị phủ định**.

Hệ quả với bộ test này:
- **D2 (2 phí → gộp) bị BỎ** — kịch bản không tồn tại.
- **D12 đổi mục tiêu**: verify JSON `delivery_fee` thật từ order API đúng là **object đơn** (không phải mảng).
- `OrderResponse.deliveryFee` **giữ object đơn**, không đổi sang `List`.

---

## Nhóm 1 — Cấu hình cấp store (UC-01)

| # | Precondition | Bước | Kỳ vọng | Ref |
|---|---|---|---|---|
| C1 | Store dùng provider Sapo Invoice, chưa cấu hình gì | Mở màn Cài đặt tự động → Sapo Invoice | `shipping_fee_mode = none` (mặc định); field tên dòng phí + checkbox tự động điều chỉnh **ẩn** | UI Specs #1 |
| C2 | — | Chọn `separate_line` | Field "Tên dòng phí trên hóa đơn" hiện, autofill sẵn **"Phí giao hàng"**; checkbox "☐ Tự động điều chỉnh phí giao hàng" hiện, **mặc định bỏ tích**; 2 dòng cảnh báo pháp lý hiện đúng nguyên văn (mục Tuân thủ) | AC7, AC8, UI Specs #2-5 |
| C3 | `separate_line` đã chọn | Xóa trắng ô tên dòng phí → Lưu | Chặn lưu, lỗi nguyên văn: `Vui lòng nhập tên dòng phí trên hóa đơn.` | BR05, UI string |
| C4 | — | Nhập tên dòng phí **256 ký tự** → Lưu | Chặn lưu, lỗi nguyên văn: `Tên dòng phí tối đa 255 ký tự.` | BR05 |
| C5 | — | Nhập tên dòng phí đúng **255 ký tự** (biên) → Lưu | Lưu OK | BR05 |
| C6 | — | Nhập tên dòng phí có khoảng trắng đầu/cuối (`"  Phí ship  "`) → Lưu | ⚠️ **Chưa rõ trong SRS** — verify hệ thống có trim hay lưu nguyên bản; nếu không trim thì log lại là gap cần hỏi BA, không phải bug | BR05 (gap) |
| C7 | `separate_line` | Tích checkbox "Tự động điều chỉnh…" → Lưu → GET lại settings | `auto_adjust_shipping_fee = true` đúng như đã lưu | AC8 |
| C8 | Đang `separate_line` | Đổi về `none` → Lưu | Field tên dòng phí + checkbox ẩn lại; hóa đơn tạo **sau** thời điểm này không còn dòng phí (xem D5) | BR02 |
| C9 | Store dùng provider **khác** Sapo Invoice (meinvoice/sinvoice/vninvoice) | Mở màn cài đặt tự động của provider đó | Toàn bộ 5 dòng cấu hình phí VC **không hiển thị** | BR09 |
| C10 | Store A đăng nhập | Gọi thẳng API `GET/POST /invoice_providers/sapo_invoice/settings` với `store_id` của **store B** (không qua session hợp lệ của B) | **404**, không phải 403; không đọc/ghi được cấu hình của B | BR04 |
| C11 | `shipping_fee_mode=none`, tạo hóa đơn nháp từ order X (không có dòng phí) | Đổi cấu hình sang `separate_line` → mở lại hóa đơn nháp X cũ để sửa | Dòng phí VC **không** tự thêm vào hóa đơn X đã tạo trước đó — mốc tính theo thời điểm **tạo**, không phải thời điểm sửa | BR02 |
| C12 | `separate_line`, `shipping_fee_item_name="Phí giao hàng"`, đã tạo hóa đơn Y có dòng phí tên "Phí giao hàng" | Đổi cấu hình tên thành "Phí ship" → mở lại hóa đơn Y | Dòng phí trên hóa đơn Y **giữ nguyên** "Phí giao hàng" (snapshot lúc tạo), không đổi theo tên cấu hình mới | AC7, BR05 |

---

## Nhóm 2 — Dựng dòng phí khi tạo hóa đơn từ order (UC-02 AC1-9, AC11)

Precondition chung trừ khi ghi khác: provider = Sapo Invoice, `shipping_fee_mode = separate_line`.

| # | Order input | Kỳ vọng dòng phí VC trong `line_items[]` | Ref |
|---|---|---|---|
| D1 | 1 phí, `fee=10000` | Đúng 1 dòng: `item_type=1`, `shipping_line=true`, `item_name`=theo cấu hình, `quantity=1`, `tax_name=KCT`, `tax_amount=0`, `unit_price=amount=amount_without_vat=10000`, mọi field chiết khấu = 0 | BR01, BR03, BR05, BR10 |
| ~~D2~~ | ~~2 phí `8000` + `2000`~~ | **BỎ (2026-08-20)** — một đơn chỉ có một phí giao hàng, kịch bản nhiều phí không tồn tại | BR01 |
| D3 | 1 phí, `fee=0` | Vẫn tạo dòng phí, `amount=0`, `tax_name=KCT` (không bỏ qua vì giá trị 0) | BR07 |
| D4 | Order **không có** `delivery_fee` | `line_items[]` **không** có dòng phí VC nào | BR01 (điều kiện âm) |
| D5 | `shipping_fee_mode=none`, order có phí | **Không** tạo dòng phí — hành vi mặc định hiện tại giữ nguyên | Phạm vi §Out-of-scope hành vi cũ |
| D6 | Như D1 | Tổng hóa đơn: `total_sale_amount`/`total_amount_without_vat`/`total_amount` đều `+10000`; `total_vatamount +0`; khối tổng nhóm **KCT** `amount_without_vat +10000`, `tax_amount +0` | Domain Model §Ảnh hưởng tổng |
| D7 | 1 phí `fee=10000`, chạy 2 lần: `order.tax_treatment=inclusive` rồi `exclusive` | Kết quả dòng phí **giống hệt nhau** ở cả 2 lần — công thức không rẽ theo `tax_treatment` | BR03, ví dụ 1 SRS |
| D8 | Auto Invoice retry cùng 1 order nhiều lần (giả lập lỗi mạng/timeout) | Vẫn đúng **1** dòng phí trên hóa đơn cuối cùng, không nhân đôi/nhân ba | Idempotency (§AC gốc issue US-2 cũ) |
| D9 | Auto Invoice pipeline (`createDraft(OrderDomain, autoInvoiceConfigId)`) | Dòng phí dựng đúng như luồng thủ công (D1-D3) — cùng đi qua `setOrderData()` | Cursor prompt A4/A5 |
| D10 | Nếu có luồng preview riêng (`createDraftPreview`) | Dòng phí cũng xuất hiện đúng trong response preview, không chỉ khi save thật | — verify tồn tại luồng này trước |
| D11 IDOR | Order thuộc store B | Store A gọi API dựng draft cho order của B | **404** | BR04 |
| D12 | Order thật từ Omni (không phải data mock) | Gọi order API thật qua flow tạo draft, kiểm JSON `delivery_fee` nhận được đúng là **object đơn** `{shipping_cost_id, shipping_cost_name, fee}` — verify lần đầu deploy vì field này chưa từng chạy runtime thật trước epic này | B0 (verify runtime) |

---

## Nhóm 3 — Đổi provider khi sửa hóa đơn (UC-02 AC10, BR09)

| # | Precondition | Bước | Kỳ vọng | Ref |
|---|---|---|---|---|
| P1 | Hóa đơn đang có dòng phí VC (`F=10000`), provider=Sapo Invoice | Sửa hóa đơn, đổi provider → meinvoice/sinvoice/vninvoice → Lưu | Dòng phí biến mất khỏi `line_items[]`; tổng giảm đúng: `total_sale_amount`/`total_amount_without_vat`/`total_amount` đều `−10000`, `total_vatamount` không đổi; nhóm KCT giảm 10000 (biến mất nếu không còn dòng KCT khác) | BR09, bảng Δ trong Domain Model |
| P2 | Tiếp P1 | Đổi provider **quay lại** Sapo Invoice | Dòng phí được **dựng lại từ đầu** theo cấu hình **hiện tại** (không phải giá trị cũ đã mất) — nếu cấu hình đổi tên/mode giữa chừng thì phản ánh giá trị mới nhất | BR09 |
| P3 | `shipping_fee_mode=none` (không có dòng phí sẵn) | Đổi provider ra khỏi Sapo Invoice | Không có gì thay đổi liên quan phí VC, không lỗi | BR09 |
| P4 | Order không có `delivery_fee` | Đổi provider | Không có dòng phí để loại/dựng lại, không lỗi | BR09 |
| P5 | Như P1 | Thực hiện đổi provider | **Không** có dialog/cảnh báo xác nhận nào hiện ra dù dòng phí bị mất — hành vi khác với các cảnh báo mất-dữ-liệu khác trên form (nếu có) | BR09 "tự động, KHÔNG cảnh báo" |
| P6 BE guard | Hóa đơn có dòng phí, đổi provider ở FE | Gọi thẳng API edit, giữ nguyên payload có dòng `shipping_line=true` nhưng `publishing_provider != sapo_invoice` (bypass FE) | Server vẫn phải **loại bỏ** dòng phí — không tin client | BR09, Cursor prompt A7/B4 |
| P7 | Hóa đơn chỉ có 1 dòng KCT là dòng phí VC (không dòng KCT nào khác) | Đổi provider khỏi Sapo Invoice | Nhóm KCT **biến mất hoàn toàn** khỏi khối tổng theo thuế suất | Domain Model §Ảnh hưởng tổng |

---

## Nhóm 4 — Điều chỉnh hóa đơn tự động (BR08, AC8, AC11, BR10)

| # | Precondition | Bước | Kỳ vọng | Ref |
|---|---|---|---|---|
| A1 | `auto_adjust_shipping_fee = true`, hóa đơn gốc có dòng phí VC | Đơn bị trả/hủy → Auto Invoice tự tạo hóa đơn điều chỉnh | Hóa đơn điều chỉnh **có** dòng phí VC, giá trị **âm** cùng các dòng khác | BR08, AC8 |
| A2 | `auto_adjust_shipping_fee = false` (mặc định), hóa đơn gốc có dòng phí VC | Như A1 | Hóa đơn điều chỉnh **không** chứa dòng phí VC — bị loại khỏi baseline khi build adjustment | BR08, AC8 |
| A3 | Tiếp A1 | Kiểm dòng phí trong hóa đơn điều chỉnh | `shipping_line = true` vẫn giữ nguyên (copy từ baseline, không bị mất marker khi ghi âm) | BR10 |
| A4 | Hóa đơn gốc đã tạo lúc `auto_adjust_shipping_fee=false` | Đổi cấu hình sang `true` **sau đó**, rồi mới trigger điều chỉnh tự động | ✅ **Đã chốt (BA, 2026-08-20 — phương án A):** đọc cấu hình tại **thời điểm chạy điều chỉnh** → hóa đơn điều chỉnh **CÓ** ghi âm dòng phí. Đây là kỳ vọng đúng, **không phải bug** | BR08 (đã resolve) |
| A5 | `shipping_fee_mode=none` (hóa đơn gốc không có dòng phí) | Bật/tắt `auto_adjust_shipping_fee`, trigger điều chỉnh tự động | Không ảnh hưởng gì — không có dòng phí để điều chỉnh, không lỗi | BR08 |
| A6 | Hóa đơn gốc có dòng phí VC | User **tự tạo** hóa đơn điều chỉnh thủ công (không qua Auto Invoice) | ✅ **Đã xác minh bằng code (2026-08-20):** checkbox **chỉ áp cho Auto Invoice**. `createAdjustmentAutoDraft` là đường duy nhất dựng HĐ điều chỉnh từ baseline và chỉ được gọi từ `AutoInvoiceExecutionServiceImpl` → luồng thủ công không đi qua logic này | BR08 (đã resolve) |

---

## Nhóm 5 — Regression

| # | Case | Kỳ vọng | Ref |
|---|---|---|---|
| R1 | Store chưa từng đổi cấu hình (`shipping_fee_mode=none` mặc định) | Toàn bộ hành vi tạo/sửa/phát hành hóa đơn giống hệt trước khi có epic này | Baseline |
| R2 | Hóa đơn có dòng phí VC, user sửa 1 dòng hàng **thường** (không phải dòng phí) rồi lưu | Dòng phí VC **vẫn còn nguyên** trong `line_items[]` sau khi lưu — verify guard ở `edit()` không làm rớt dòng phí | Cursor prompt A7 |
| R3 | Hóa đơn có dòng phí VC | Xuất/in hóa đơn | Hiển thị đúng `item_name` (theo cấu hình) và `amount` | UI Specs |
| R4 | Publish hóa đơn có dòng phí VC sang Sapo Invoice | Payload gửi SI có dòng phí, `item_type="products"` — **known tech debt**: mọi dòng đều hardcode `"products"` (epic &46 chưa merge xong), không phải bug riêng của epic #61 | Cursor prompt A9, dependency &46 |
| R5 | Chạy lại D1-D3 (nhóm 2) trên cả hóa đơn **GTGT** và **Bán hàng** | Kết quả giống nhau ở cả 2 loại; hóa đơn Bán hàng: dòng KCT không sinh `tax_reduction_amount` | Phạm vi "áp cho cả GTGT và Bán hàng"; BR08 dòng cuối |
| R6 | Order có `exchange_rate != 1` (ngoại tệ) | ⚠️ **Verify hành vi** — SRS chỉ ghi "Chỉ hỗ trợ VND", không nói rõ ngoại tệ thì im lặng bỏ qua dòng phí hay báo lỗi. Cần hỏi BA nếu case này thực tế xảy ra | Mục tiêu §Phạm vi kênh (gap) |

---

## Cách đối chiếu kết quả

**1. Response API** — sau khi tạo/sửa hóa đơn, đọc thẳng `line_items[]` trong response, lọc `shipping_line=true` để soi nhanh dòng phí thay vì dò theo `item_name`.

**2. DB (`sapo-einvoice-service`, SQL Server — xem [[10_Projects/sapo-invoice/omni-einvoice-dieu-tra-su-co-prod]] về quy tắc UTC/shard nếu cần)**, sau khi migration `V8__add_is_shipping_line...` chạy:

```sql
SELECT TOP 30 e.Id, e.PublishingProvider, li.ItemName, li.ItemType, li.IsShippingLine,
       li.Amount, li.TaxAmount, li.TaxName
FROM EInvoiceLineItems li
JOIN EInvoices e ON e.Id = li.EInvoiceId AND e.TenantId = li.TenantId
WHERE li.TenantId = <tenant_id> AND li.IsShippingLine = 1
ORDER BY li.Id DESC;
```

**3. Settings** — `GET /invoice_providers/sapo_invoice/settings` sau khi đổi cấu hình, đối chiếu đúng 3 key `shipping_fee_mode`/`shipping_fee_item_name`/`auto_adjust_shipping_fee`.

## 📋 Bảng ghi kết quả

Tick khi chạy xong (chỉ chạy sau khi Cursor implement + migration `is_shipping_line` đã lên môi trường test).

| Xong | Nhóm | Case | Thực tế (nếu khác) |
|---|---|---|---|
| [ ] | 1 — Cấu hình | C1–C5, C7–C12 | |
| [ ] | 1 — Cấu hình | **C6** (trim khoảng trắng — gap) | |
| [ ] | 2 — Dựng dòng phí | D1–D11 | |
| [ ] | 2 — Dựng dòng phí | **D12** (verify shape thật từ order API lần đầu chạy) | |
| [ ] | 3 — Đổi provider | P1–P7 | |
| [ ] | 4 — Điều chỉnh tự động | A1, A2, A3, A5 | |
| [ ] | 4 — Điều chỉnh tự động | **A4, A6** (gap — cần verify với dev trước) | |
| [ ] | 5 — Regression | R1–R5 | |
| [ ] | 5 — Regression | **R6** (ngoại tệ — gap, hỏi BA nếu thực tế xảy ra) | |

### Case cần verify/hỏi trước khi coi kết quả khác-kỳ-vọng là bug

- **D12** — B0 đã resolve về nghiệp vụ (BA: object đơn, một phí), nhưng chưa có bằng chứng runtime thật (field `getDeliveryFee()` chưa từng chạy trước epic này) — verify JSON thật từ order API lần đầu deploy. Nếu payload thật lại ra mảng thì Jackson sẽ ném `MismatchedInputException` làm **hỏng cả luồng lấy order**, không chỉ mất dòng phí → đây là lý do D12 vẫn phải chạy dù nghiệp vụ đã chốt.
- **C6** — trim khoảng trắng tên dòng phí, SRS không ghi rõ.
- ~~**A4** — setting `auto_adjust_shipping_fee` đọc tại thời điểm nào.~~ ✅ Đã chốt 2026-08-20 (BA, phương án A): đọc lúc chạy điều chỉnh.
- ~~**A6** — phạm vi `auto_adjust_shipping_fee` có áp cho điều chỉnh thủ công không.~~ ✅ Đã xác minh 2026-08-20: chỉ áp cho Auto Invoice.
- **R6** — hành vi khi order không phải VND.

## Liên kết

- [[epic-61-phi-van-chuyen-hoa-don-v2]] — SRS v0.6
- [[epic-61-cursor-prompt-implement]] — prompt implement
- [[10_Projects/sapo-invoice/omni-einvoice-dieu-tra-su-co-prod]] — quy tắc truy DB/UTC khi đối chiếu
