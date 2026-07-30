---
created: 2026-07-30 10:00
status: Implemented
project: "[[10_Projects/sapo-invoice/README]]"
---

# Epic #65 — Hiển thị chi tiết đơn hàng thất bại trong popup Auto Invoice

Repo: `invoice-app` (Spring Boot 3.3 / Java 17 + React 18 TS). GitLab epic gid `8887`, group `sapo-money/sapo-invoice`, child issue tạo ở project `sapo-invoice-admin-service` (xem convention chung).

## Trạng thái hiện tại (đã kiểm tra code, KHÔNG phải giả định)

- FE (`AutoInvoiceSummaryModal.tsx`) đã có sẵn phần expand cấp 2 "Chi tiết" theo từng lý do lỗi, hiển thị danh sách đơn bị lỗi trong box có scroll (`OrderListBox`, max-height 120px, overflow-y auto).
- Link mở đơn hàng dùng `sapo:/orders/{orderId}` — đúng convention đã dùng ở khắp nơi trong app (`InvoiceListPage.tsx`, `TableCreateInvoice.tsx`, ...).
- Vấn đề còn lại: FE đang hiển thị **mã đơn giả** `SO${orderId}` (xem comment trong `AutoInvoiceSummaryModal.tsx`) vì BE **chưa có field order_name**. Đây là phần việc thật sự còn thiếu của epic.
- Đã xác nhận: field `orderName` **có sẵn tại mọi điểm gọi save-failure** (`OrderResponse.getName()` ở luồng tạo hoá đơn, `Invoice.getOrderName()` ở luồng phát hành) → không cần gọi thêm API Order nào cho các bản ghi mới.

## ⚠️ Đính chính CLAUDE.md của invoice-app

CLAUDE.md ghi "no formal migrations - Hibernate auto-DDL", nhưng code thực tế (`infrastructure/config/DataSourceConfig.java:71`) set `hibernate.hbm2ddl.auto = "none"` tường minh — Hibernate KHÔNG tự tạo/sửa cột. Repo có thư mục `src/main/resources/db/migration/V*.sql` đặt tên kiểu Flyway nhưng **Flyway không được wire vào** (không có dependency trong `build.gradle`, không có config trong `application*.yml`) — các file này chỉ để record lại SQL đã chạy tay, không tool nào tự thực thi. Mọi thay đổi schema đều phải tự chạy ALTER TABLE thủ công trên từng môi trường.

## Migration đã chuẩn bị sẵn

Đã verify với DB thật: `invoices.order_name` là VARCHAR(50) (khớp `@Size(max = 50)` trên `Invoice.java:62`). Đã tạo file `invoice-app/src/main/resources/db/migration/V9__add_order_name_to_auto_invoice_results.sql`:

```sql
ALTER TABLE auto_invoice_results
ADD COLUMN order_name VARCHAR(50) NULL COMMENT 'Mã đơn hàng (order.name), NULL với các bản ghi cũ chưa backfill' AFTER order_id;
```

Cần chạy tay trên dev/staging/production trước hoặc cùng lúc deploy code có field `orderName` mới.

---

## Issue 1 — Bổ sung order_name thật cho popup Auto Invoice (BE + FE, cùng issue, cùng repo)

### Backend

0. Chạy ALTER TABLE thủ công trước (xem trên) — bắt buộc vì `ddl-auto=none`.
1. `domain/autoinvoice/model/AutoInvoiceResult.java` — thêm field `private String orderName;`
2. `application/model/autoinvoice/AutoInvoiceResultResponse.java` — thêm field `private String orderName;` (tự map thành `order_name` trong JSON, project có auto snake_case↔camelCase).
3. `application/service/autoinvoice/AutoInvoiceResultService.java`
   - Thêm tham số `String orderName` vào `saveSuccess`, `saveFailure`, `saveCreatedFailure`, cascade xuống `doSaveResult`.
   - Trong `doSaveResult`: `result.setOrderName(orderName)` mỗi lần save, kể cả khi update lại record cũ (qua `findOrCreate`), để order_name luôn mới nhất.
4. Cập nhật 4 nơi gọi (order name **đã có sẵn tại chỗ**, không cần gọi thêm API nào):
   - `application/service/invoice/DraftInvoiceWriteService.java`, hàm `saveAutoInvoiceFailure(...)`: truyền `order.getName()`.
   - `application/service/invoice/AdjustmentInvoiceWriteService.java`, 2 chỗ gọi `saveCreatedFailure`: truyền `order.getName()`.
   - `infrastructure/job/rabbit/AutoPublishRetryConsumer.java`: biến `invoice` đã load qua `invoiceCommonService.getById(...)` đầu hàm `handleRetry` → truyền `invoice.getOrderName()`.
   - `infrastructure/job/kafka/InvoiceAutoPublishedConsumer.java`: biến `domain` trong các hàm này chính là kiểu `Invoice` (xem `unmarshalInvoice`) → truyền `domain.getOrderName()`.
5. Unit test `AutoInvoiceResultService` cho cả nhánh created_fail và published_fail, cả case insert mới và update record cũ.

### Frontend

1. `frontend/src/pages/types.ts` — thêm `order_name?: string;` vào type `AutoInvoiceResult`.
2. `frontend/src/pages/components/AutoInvoiceSummaryModal.tsx`
   - `AutoInvoiceErrorSummary`: đổi `orderIds: number[]` thành `orders: { orderId: number; orderName?: string }[]`.
   - `summarizeErrors`: lấy thêm `result.order_name` khi push order.
   - `buildOrderItems`: `displayName = item.orderName || \`SO${item.orderId}\`` — **giữ nguyên fallback**, không phải dead code, cần cho trường hợp mở lại link email thông báo cũ (xem phần "Issue 2 đã bỏ" bên dưới).

### Test thủ công trên staging

- Trigger 1 bản ghi created_fail và 1 published_fail mới, xác nhận `order_name` trả về đúng mã đơn thật.
- Xác nhận click mã đơn mở đúng trang chi tiết đơn hàng, tab mới.
- Test 1 lý do lỗi có >5 đơn để xác nhận scroll trong box.

---

## ~~Issue 2 — Backfill order_name cho dữ liệu cũ~~ — ĐÃ BỎ (2026-07-30)

**Quyết định:** không làm backfill. Lý do (rà lại kỹ Epic #65 gốc — GitLab issue [#70](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/work_items/70), đã comment giải thích và đề nghị đóng, nhưng GitLab API lỗi 502 lúc thao tác — cần tự đóng issue thủ công):

1. Epic #65 gốc **không hề yêu cầu backfill** — chỉ yêu cầu lưu `order_name` cho bản ghi mới. Yêu cầu backfill trước đây là do tự đề xuất lúc BA Q&A (Q5), không phải từ epic.
2. Popup mặc định chỉ query dữ liệu **trong ngày hiện tại** (`startOfToday` → `currentTime`) — bản ghi cũ (ngày trước) không bao giờ hiển thị lại qua đường này.
3. Đường duy nhất có thể hiển thị dữ liệu ngày cũ: link trong **email thông báo tự động** (`AutoInvoiceNotificationMailService.java`), nhúng sẵn khoảng ngày tại thời điểm gửi email (`summary.getStartTime()/getEndTime()`) — nếu merchant mở lại email cũ (gửi trước deploy) sau khi deploy, có thể gặp `order_name = null`.
4. Trường hợp (3) **không vỡ UI** — FE đã có fallback `SO{order_id}` khi `order_name` null (xem AC trong issue #69: "Bản ghi cũ order_name=null → không crash, fallback đúng"), đây là hành vi đã được chấp nhận từ đầu.

→ Giữ nguyên fallback `SO${orderId}` trong `buildOrderItems` (không xoá) — vẫn cần cho trường hợp (3), dù không còn kế hoạch backfill chủ động.

---

## Ngoài phạm vi 2 issue này (đã confirm với BA)

- FE expand cấp 2 + scroll box + link mở đơn: đã code sẵn, không làm lại.
- Không tách issue nhỏ hơn — BE+FE chung 1 issue vì cùng repo, chỉ tách riêng backfill.

---

## Cursor prompt — Issue 1 (BE + FE order_name)

```
Implement Epic #65 "Hiển thị chi tiết đơn hàng thất bại trong popup Auto Invoice" — Issue 1 (BE + FE, order_name thật thay cho mã giả SO+orderId).

Migration SQL đã có sẵn tại `src/main/resources/db/migration/V9__add_order_name_to_auto_invoice_results.sql` (ALTER TABLE thêm cột `order_name VARCHAR(50) NULL` vào `auto_invoice_results`). File này KHÔNG tự chạy (không có Flyway wired trong project) — chỉ để record lại, mình sẽ tự chạy tay trên DB. Không cần đụng vào file này, chỉ cần biết cột đã/sẽ tồn tại.

Việc cần làm:

1. `src/main/java/vn/sapo/app/invoice/domain/autoinvoice/model/AutoInvoiceResult.java`
   - Thêm field `private String orderName;`

2. `src/main/java/vn/sapo/app/invoice/application/model/autoinvoice/AutoInvoiceResultResponse.java`
   - Thêm field `private String orderName;` (project có auto snake_case↔camelCase, tự map thành `order_name` trong JSON, không cần `@JsonProperty`)

3. `src/main/java/vn/sapo/app/invoice/application/service/autoinvoice/AutoInvoiceResultService.java`
   - Thêm tham số `String orderName` vào `saveSuccess(...)`, `saveFailure(...)`, `saveCreatedFailure(...)` và cascade xuống `saveResult`/`doSaveResult`.
   - Trong `doSaveResult`: `result.setOrderName(orderName);` — set mỗi lần save, kể cả khi update lại record đã tồn tại (tại findOrCreate trả về record cũ), để order_name luôn là bản mới nhất.
   - Cập nhật tất cả overload liên quan cho khớp signature mới, kiểm tra kỹ tất cả các call site sau khi đổi (biên dịch phải pass).

4. Cập nhật 4 nơi gọi các hàm trên — order name ĐÃ có sẵn tại các điểm này, KHÔNG cần gọi thêm API nào:
   - `application/service/invoice/DraftInvoiceWriteService.java`, hàm `saveAutoInvoiceFailure(...)`: truyền `order.getName()` (biến `order` là `OrderResponse` đã có sẵn trong scope).
   - `application/service/invoice/AdjustmentInvoiceWriteService.java`, 2 chỗ gọi `saveCreatedFailure(...)`: truyền `order.getName()`.
   - `infrastructure/job/rabbit/AutoPublishRetryConsumer.java`, các chỗ gọi `saveSuccess`/`saveFailure`: dùng `invoice.getOrderName()` — biến `invoice` đã được load qua `invoiceCommonService.getById(...)` ngay đầu hàm `handleRetry`.
   - `infrastructure/job/kafka/InvoiceAutoPublishedConsumer.java`, các chỗ gọi `saveSuccess`/`saveFailure`: biến `domain` trong các hàm này CHÍNH LÀ kiểu `Invoice` (xem `unmarshalInvoice`) → dùng `domain.getOrderName()`.

5. Thêm/update unit test cho `AutoInvoiceResultService` xác nhận `orderName` được set đúng ở cả nhánh created_fail và published_fail (test cả case insert mới và case update lại record cũ qua `findOrCreate`).

6. Frontend — `frontend/src/pages/types.ts`:
   - Thêm `order_name?: string;` vào type `AutoInvoiceResult`.

7. Frontend — `frontend/src/pages/components/AutoInvoiceSummaryModal.tsx`:
   - Type `AutoInvoiceErrorSummary`: đổi field `orderIds: number[]` thành mảng object giữ cả tên, ví dụ `orders: { orderId: number; orderName?: string }[]` (đổi tên cho phù hợp, giữ logic dùng key theo error message y như cũ).
   - `summarizeErrors`: khi push order vào summary, lấy thêm `result.order_name` cùng `result.order_id`.
   - `buildOrderItems`: `displayName = item.orderName || \`SO${item.orderId}\`` — GIỮ NGUYÊN fallback `SO${orderId}`, đây không phải dead code, nó cần thiết cho các bản ghi cũ chưa chạy job backfill (issue riêng, không thuộc phạm vi này) hoặc trường hợp order_name null vì lý do khác.
   - Không đổi phần UI/style khác (box scroll, link mở đơn `sapo:/orders/{orderId}`) — phần đó đã đúng yêu cầu, không cần sửa.

Ràng buộc:
- Theo code style Java của project: constructor injection, Palantir format (Spotless), log lỗi có context (storeId/orderId), không dùng exception cho luồng bình thường.
- Theo code style TS/React của project: không dùng `any`, giữ nguyên pattern component hiện có, không refactor thêm ngoài phạm vi trên.
- Không tự ý thêm migration script mới, không tự chạy ALTER TABLE — đã có sẵn file V9, mình tự chạy tay.
- Sau khi sửa xong, chạy `./gradlew spotlessJavaApply` (backend) và `pnpm lint:fix` (frontend) để đảm bảo format đúng chuẩn.
```

## Checklist

- [x] Chạy `V9__add_order_name_to_auto_invoice_results.sql` trên dev
- [x] Cursor implement Issue 1 (BE + FE)
- [x] Review code Issue 1 — không phát hiện lỗi (đã dọn thêm field `invoiceCount` chết)
- [x] Commit + tạo MR #224 (→ staging) và #225 (→ master, Draft)
- [x] Merge Issue 1 vào staging (theo chiều ngược, xem [[merge-feature-branch-vao-staging-truoc-master]]) — commit `2346b9f1`
- [ ] Đóng MR #224 thủ công (đã lên staging, không merge qua GitLab nữa)
- [ ] Đóng GitLab issue #70 (backfill) thủ công — đã comment giải thích lý do bỏ, nhưng bị lỗi 502 lúc gọi API, cần tự đóng
- [ ] Chạy migration V9 trên staging (nếu MR #224 merge có kèm, hoặc tự chạy tay)
- [ ] Test thủ công trên staging (created_fail, published_fail, scroll, click order)
- [ ] Chuyển MR #225 từ Draft sang Ready sau khi test staging xong
- [ ] Chạy migration + deploy Issue 1 lên production
- ~~[ ] Implement Issue 2 (backfill endpoint)~~ — đã bỏ, xem lý do ở trên
- ~~[ ] Đưa endpoint backfill cho leader chạy trên production~~ — đã bỏ
