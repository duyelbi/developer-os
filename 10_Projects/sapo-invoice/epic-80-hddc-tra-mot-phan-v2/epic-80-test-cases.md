---
created: 2026-08-25 08:30
status: Draft — dựng trước khi code chạy, chưa verify trên môi trường thật
project: "[[10_Projects/sapo-invoice/README]]"
---

# Test case Epic #80 — [V2] Tự động tạo & phát hành HĐ điều chỉnh cho đơn trả 1 phần

- SRS: `invoice-docs/docs/invoice-core-v2/tu-dong-tao-phat-hanh-hoa-don-dieu-chinh/srs.md` (v1.0) · Plan: [[epic-80-plan]]
- Repo: `sapo-einvoice-service` (BE) + `sapo-frontend-v3` (FE, page `EInvoice`)
- Dựng **trước khi code chạy**, theo UC-01→05 + BR-V2-1→12 + bảng §4.9 (đã có sẵn trong SRS, coi như index case). Số dòng/tên hàm là tham chiếu code hiện tại (branch `dev-money/feature/shipping-fee-invoice-v2-dev2-SM-0`), có thể lệch sau khi dev implement.
- Công cụ đối chiếu tiền độc lập: `hddc-tester-v2.html` (cùng thư mục SRS) — dán JSON HĐ gốc + đơn trả, so kết quả với response API thật.

> ⚠️ **Đọc [[epic-80-plan]] trước khi chạy nhóm 6-8** — các nhóm đó test những cơ chế mà SRS giả định "đã có" nhưng thực tế code **chưa có** (ledger, reconciliation job, STP snapshot). Nếu code chưa implement phần đó, case sẽ fail **không phải vì bug** mà vì scope chưa làm — đối chiếu với BE trước khi report.

---

## Nhóm 1 — Cấu hình khối HĐ điều chỉnh trên Auto Invoice V2 (UC-01)

| # | Precondition | Bước | Kỳ vọng | Ref |
|---|---|---|---|---|
| C1 | Tài khoản **thiếu** quyền Điều chỉnh + Phát hành theo MST | Mở màn Auto Invoice V2, thử cấu hình khối HĐ điều chỉnh | Chặn cấu hình + alert | UC-01 AC1 |
| C2 | Tài khoản đủ quyền | Bật `auto_adjustment_invoice_enabled`, **không** chọn tiêu chí điều kiện đơn hàng nào → Lưu | Chặn lưu — bắt buộc tối thiểu 1 tiêu chí | UC-01 AC2 |
| C3 | — | Để trống `reason` (lý do điều chỉnh) → Lưu | Chặn lưu, bắt buộc | UC-01 AC3 |
| C4 | — | Để trống `return_date_from` (ngày tạo đơn trả từ) → Lưu | Chặn lưu, bắt buộc | UC-01 AC3 |
| C5 | — | Nhập `reason` đúng 255 ký tự (biên) → Lưu | Lưu OK | UC-01 AC3 |
| C6 | — | Nhập `reason` 256 ký tự → Lưu | Chặn lưu | UC-01 AC3 |
| C7 IDOR | Store A đăng nhập | Gọi thẳng API cấu hình với `store_id`/config id của store B | **404**, không phải 403 | UC-01 AC4 |
| C8 | Khối HĐ điều chỉnh **tắt** (`auto_adjustment_invoice_enabled=false`), khối HĐ mới (`auto_new_invoice_enabled`) **bật** | Đơn phát sinh trả 1 phần | Không tạo HĐĐC — 2 toggle độc lập, không ảnh hưởng nhau | UC-01 AC2, §3 |
| C9 | Đủ quyền Điều chỉnh nhưng **thiếu** quyền Phát hành | Cấu hình cả HĐ mới + HĐ điều chỉnh | Check quyền theo **mức của HĐ điều chỉnh** (mức cao hơn) — thiếu → chặn toàn bộ, không chỉ chặn phần điều chỉnh | §3 "Quyền SI bắt buộc" |

---

## Nhóm 2 — UI: option mới cho "Trạng thái đơn hàng" (UC-01 §6.1, FE `sapo-frontend-v3`)

> ⚠️ **Cập nhật 2026-08-26 — Figma thật đã gắn vào epic, khác SRS.** Figma ([node 224:33410](https://www.figma.com/design/eB5jx4MxReLJuyrlptKhs2/SAPO-INVOICE-V2?node-id=224-33410)) đặt tên option mới là **"Đã hoàn trả toàn bộ và 1 phần"** (không phải "Đã hoàn trả một phần"), hiển thị như **option độc lập thứ 3** cạnh "Đã hoàn trả toàn bộ" — mockup **không** thể hiện hành vi auto-tick/khóa nào giữa 2 option. Helptext trong Figma vẫn giữ cụm "và đã hoàn tiền", **mâu thuẫn BR-V2-2** (V2 không yêu cầu hoàn tiền). Xem [[epic-80-plan]] mục "Cập nhật 2026-08-26". Các case U1-U5 dưới đây viết theo **cả 2 khả năng** — đánh dấu case nào áp dụng theo hướng nào, chỉ chạy nhánh đã được PO chốt.

| # | Bước | Kỳ vọng | Ref |
|---|---|---|---|
| U1 | Mở bộ lọc "Trạng thái đơn hàng" trong khối HĐ điều chỉnh | Thấy **option mới** — tên đúng theo bản đã chốt (Figma: "Đã hoàn trả toàn bộ và 1 phần" / SRS: "Đã hoàn trả một phần") | §6.1, Figma node 224:33410 |
| U2 🔴 quan trọng | Chọn option mới | Helptext hiện đúng **nguyên văn bản đã chốt** (không phải bản Figma hiện tại nếu PO đã yêu cầu sửa) — **verify KHÔNG còn cụm "và đã hoàn tiền"** nếu BR-V2-2 giữ nguyên (không yêu cầu hoàn tiền) | §6.1, BR-V2-2 — xem gap dưới |
| U3 (chỉ áp dụng nếu chốt theo SRS — 2 option + auto-lock) | Chọn option mới | "Đã hoàn trả toàn bộ" **tự động được tích** và **khóa** (không cho bỏ tích) | §6.1 |
| U4 (chỉ áp dụng nếu chốt theo SRS) | Đang ở trạng thái U3 | Thử bấm bỏ tích "Đã hoàn trả toàn bộ" | Không bỏ tích được — vẫn khóa | §6.1 |
| U5 (chỉ áp dụng nếu chốt theo SRS) | Đang ở trạng thái U3 | Bỏ tích option mới | "Đã hoàn trả toàn bộ" **mở khóa lại** | §6.1 (suy luận, verify với dev) |
| U3b (chỉ áp dụng nếu chốt theo Figma — 3 option độc lập) | Chọn option mới, không đụng "Đã hoàn trả toàn bộ" | **Không** có tick/khóa tự động nào xảy ra — 2 checkbox hoàn toàn độc lập | Figma node 224:33410 (quan sát trực tiếp mockup) |
| U6 | Chọn option gộp → Lưu → API | `condition_value` chứa **`partially_returned`** (không bắt buộc kèm `returned`). BE router: trả đủ lần đầu → Full; trả dở → Partial | Q2 đính chính 2026-09-08 |
| U7 | Sau khi Lưu, load lại trang | Trạng thái option (tích/khóa nếu có) khôi phục đúng theo config đã lưu | Regression cơ bản |
| U8 🆕 | So sánh copy đã build trên môi trường test với **cả SRS lẫn Figma** | Nếu lệch với **cả hai** (vd copy thứ 3 khác cả 2 nguồn) → báo ngay, khả năng cao dev tự diễn giải mà chưa hỏi PO | Đối chiếu nguồn |

---

## Nhóm 3 — Điều kiện kích hoạt đơn trả (UC-02 AC1-2, §4.3, BR-V2-2)

Precondition chung trừ khi ghi khác: `auto_adjustment_invoice_enabled=true`, đủ điều kiện đơn hàng khớp.

| # | Order/return input | Kỳ vọng | Ref |
|---|---|---|---|
| R1 | `order_return.status = "returned"`, `created_on ≥ return_date_from` | Tạo HĐĐC | BR-V2-2 |
| R2 | `order_return.status = "returned"`, `refund_status` **chưa** settled (`unpaid`/`partial`/null) | **KHÔNG** tạo HĐĐC (Q1 chốt theo Figma: phải đã hoàn tiền; Omni V2: `paid` hoặc `refunded`) | Q1, BR-V2-2 (đã chỉnh) |
| R3 | `order_return.status = "cancelled"` | Loại — không tạo HĐĐC, **không** cộng vào `Σ_returned` | BR-V2-2, §4.9 #20 |
| R4 | `order_return.status` đang xử lý (không phải `returned`/`cancelled`) | Loại, không tính vào `Σ_returned` | §4.9 #20 |
| R5 | `order_return.created_on <  return_date_from` | Loại — ngoài phạm vi cấu hình | §4.3 điểm 2 |
| R6 | Đơn trả đã có trong ledger (đã xử lý trước đó) | Skip — không tạo lại | §4.3 điểm 3, BR-V2-5 |
| R7 | Config có `partially_returned`, `Σ_returned < Σ_ordered` | Hoàn 1 phần → **PartialEngine** (1 HĐĐC / phiếu) | Bảng phân loại §4.3, Q2 đính chính 2026-09-08 |
| R8 | Config có `partially_returned` (± `returned`) hoặc chỉ `returned`; `Σ_returned = Σ_ordered`, **lần đầu** (chưa ledger partial) | **FullEngine** — không tạo qua luồng partial. Config **chỉ** `partially_returned` cũng Full (option gộp) | §4.3, §4.9 #6, Q2 đính chính 2026-09-08 |
| R9 | `Σ_returned = Σ_ordered`, **đã có** HĐĐC/ledger partial trước đó | Hoàn tất chuỗi → **PartialEngine** (vẫn 1 HĐĐC / phiếu còn lại) | §4.3, §4.9 #7 |
| R10 | `Σ_returned > Σ_ordered` | Bất thường — **không auto**, đánh dấu `returned_exceeds_ordered`, đưa vào thông báo xử lý tay | Bảng phân loại §4.3, §4.9 #8, UC-02 AC9 |
| R11 (A) | Đơn trả **trước** đó (`created_on ≥ return_date_from`) đang `deferred`/chưa xử lý | Đơn trả đang xét → **tạm hoãn** (`deferred`), tự thử lại sau | §4.3 bảng "2 loại", §4.9 #9 |
| R12 (B) | Đơn trả **trước** đó `created_on < return_date_from` (ngoài phạm vi cấu hình, không bao giờ xử lý được) | Chuỗi thiếu vĩnh viễn → **chặn**, không auto cho đơn đang xét | §4.3 bảng "2 loại", §4.9 #10 |
| R13 | Cùng 1 order có nhiều đơn trả `returned` cùng lúc (batch) | Xử lý **tuần tự** theo `(received_on, created_on, id)` tăng dần, khóa theo `order_id` | §4.2 bước 4, BR-V2-6 |
| R14 IDOR | Order/đơn trả thuộc store B | Store A xử lý được qua lỗ hổng nào đó (giả lập gọi thẳng) | Phải **404**, mọi truy vấn lọc `tenantId`/`store_id` từ session | §7 |

---

## Nhóm 4 — Map dòng HĐ gốc & combo (§4.4, §4.5, BR-V2-3/4)

| # | Precondition | Input | Kỳ vọng | Ref |
|---|---|---|---|---|
| M1 | HĐ gốc **đã có** `order_line_item_id` trên dòng (HĐ tạo sau uplive) | Đơn trả 1 dòng thường | Map **trực tiếp** qua `order_line_item_id`, không dùng fallback `variant_id` | BR-V2-3 |
| M2 | HĐ gốc **chưa có** `order_line_item_id` (tạo trước uplive, field = null) | Đơn trả 1 dòng thường | Fallback bắc cầu `order_line_item_id → order.order_line_items.variant_id → einvoice.line_items.item_id` | §4.4, §4.5 "Backfill: KHÔNG" |
| M3 ⚠️ | Order có **≥2 dòng cùng `variant_id`** khác giá/CK, HĐ gốc **chưa có** `order_line_item_id` (case M2) | Trả 1 trong 2 dòng đó | Đây là **rủi ro đã biết** của fallback (SRS §4.5 tự nêu) — verify map đúng dòng theo `item_code`/context, không phải random dòng đầu tiên khớp `variant_id`. Nếu sai dòng → phân bổ sai tiền, đây là bug nghiêm trọng nếu xảy ra | §4.5 "Hạn chế bắc cầu variant_id" |
| M4 | `einvoice_explode_composite_lines = false` (gộp), HĐ gốc có 1 dòng combo | Trả nguyên combo, `q` = số combo trả | Sinh **1 dòng HĐĐC**, số lượng = số combo trả | BR-V2-4, §4.9 #19 |
| M5 | `einvoice_explode_composite_lines = true` (tách), HĐ gốc có N dòng thành phần cùng `order_line_item_id` | Trả nguyên combo | Sinh **đúng N dòng HĐĐC** (mỗi thành phần 1 dòng); số lượng thành phần = (số combo trả) × (số lượng thành phần/combo) | BR-V2-4, §4.9 #19b |
| M6 | — | Thử trả **lẻ** 1 sản phẩm thành phần trong combo (không trả nguyên combo) | Theo ràng buộc đã xác nhận — **không hỗ trợ**; verify hệ thống báo lỗi/chặn phù hợp thay vì tính sai | §4.4 "Ràng buộc đã xác nhận" |
| M7 | Dòng trả **không map được** dòng HĐ gốc nào (cả native lẫn fallback đều fail) | — | Kết quả `unsupported` (terminal), báo lỗi đúng nguyên văn: *"Không xác định được dòng hóa đơn gốc tương ứng với hàng trả (dùng điều chỉnh toàn bộ)."* | BR-V2-8, §4.9 #19c |
| M8 | HĐ gốc **hỗn hợp** — có dòng khuyến mại/chiết khấu/ghi chú cấp HĐ (không phải dòng phí VC) | Trả 1 dòng products bình thường | **Không chặn** — chỉ tạo dòng HĐĐC ghi âm cho dòng được trả; dòng khuyến mại/CK/ghi chú không bị đụng | §4.9 #1 |

---

## Nhóm 5 — Công thức tính tiền & làm tròn (§4.7, §4.11, BR-V2-9) — dùng `hddc-tester-v2.html` đối chiếu

| # | Input | Kỳ vọng | Ref |
|---|---|---|---|
| F1 | Dòng HĐ gốc `amount=571.428,57`, `quantity=5`, STP=2. Trả `q=1` (chưa phải lượt cuối) | HĐĐC dòng đó: `amount = -114.285,71` (= round(571.428,57×1÷5, 2), đảo dấu) | §4.7.1 ví dụ, F. đơn giá giữ dương |
| F2 | Tiếp F1, trả tiếp `q=4` (lượt cuối, cộng dồn = 5 = Q) | HĐĐC dòng đó = **phần còn lại**: `-(571.428,57 − 114.285,71) = -457.142,86`, **không** làm tròn lại phép trừ | §4.7.1 bảng "lượt trả cuối" |
| F3 | Sau F1+F2 (2 lần trả hết dòng) | **Σ tuyệt đối** của 2 HĐĐC (bỏ dấu âm) = đúng `571.428,57` — sai số cộng dồn = 0đ | §4.11.1, NFR2 |
| F4 | HĐ gốc STP=2 (như trên), so với phương án sai "dùng STP hiện tại của store nếu đã đổi = 0" | Xác nhận hệ thống dùng **STP_gốc snapshot lúc phát hành HĐ gốc**, không dùng STP hiện tại của store — nếu merchant đã đổi STP sau khi phát hành HĐ gốc, HĐĐC vẫn ra đúng theo STP cũ | §4.11.1 bảng so sánh 2 phương án — ⚠️ xem [[epic-80-plan]] mục "STP snapshot" — **field này chưa tồn tại trên code hiện tại, case này sẽ fail tới khi dev bổ sung** |
| F5 | Đảo dấu | Trên HĐĐC: `quantity` âm, mọi trường tiền (`amount`, `discount_amount`, `amount_without_vat`, `tax_amount`, `amount_after_tax`, `tax_reduction_amount`) âm; **`unit_price` giữ dương** | BR-V2-9, bảng (b) §4.7.2 |
| F6 [BH] | Hóa đơn Bán hàng, dòng có `tax_reduction_amount` (giảm thuế NQ204) trên HĐ gốc | HĐĐC phân bổ `tax_reduction_amount` độc lập theo §4.7.1 (không tính lại % giảm thuế) | §4.11.3 #1, bảng (b) |
| F7 | Tổng hóa đơn (mục c) | `total_amount` **=** Σ dòng đã đảo dấu, **không** làm tròn lại tổng | §4.7.2 (c) |
| F8 | HĐ nhiều mức thuế (`tax_name` khác nhau) | Khối tổng theo thuế suất (mục d) tính đúng riêng từng mức, không gộp nhầm giữa các mức | §4.7.2 (d) |
| F9 | Order dùng combo tách (`explode=true`), 1 combo trả, nhiều thành phần | Mỗi dòng thành phần được phân bổ + làm tròn **độc lập** theo dòng gốc tương ứng của nó, gom cộng dồn theo cặp `(order_line_item_id, variant_id)` — không lẫn giữa 2 thành phần khác nhau | §4.7.1 "Gom số lượng theo dòng nào" |
| F10 | So sánh kết quả code thật vs `hddc-tester-v2.html` cho cùng 1 bộ JSON (HĐ gốc + order_return) | Khớp tuyệt đối từng field — nếu lệch, ưu tiên nghi ngờ code (tester đã được BA/dev xác nhận qua các ví dụ SRS) | Công cụ đối chiếu độc lập |

---

## Nhóm 6 — Ledger & chống trùng ⚠️ cơ chế đang được xây MỚI, chưa có sẵn (BR-V2-5, §4.2 bước 3, UC-02 AC3+8)

> Đọc [[epic-80-plan]] bảng gap trước khi chạy nhóm này — SRS mô tả như thể ledger `UNIQUE(store_id, order_return_id)` đã tồn tại (giống V3), nhưng code `sapo-einvoice-service` hiện chỉ có Redis lock **cấp order**, không phải cấp order_return. Các case dưới đây test cơ chế **mới sẽ được xây**, không phải cơ chế cũ.

| # | Kịch bản | Kỳ vọng | Ref |
|---|---|---|---|
| L1 | 1 đơn trả → trigger event Kafka **2 lần** (giả lập at-least-once/duplicate) | Chỉ **1** HĐĐC được tạo — lần 2 bị chặn ở bước claim ledger | BR-V2-5, UC-02 AC3 |
| L2 | 2 event xử lý gần như đồng thời (race) cho **cùng 1** `order_return_id` | Claim ledger phải là **atomic** (unique constraint ở DB, không phải check-rồi-insert riêng lẻ) — chỉ 1 thắng, 1 bị chặn/skip, không tạo 2 HĐĐC | BR-V2-5 |
| L3 | Cùng `order_return_id`, 2 event Kafka đến ở **2 pod khác nhau** | Vẫn chỉ 1 HĐĐC — ledger phải cross-instance (DB, không phải in-memory lock cục bộ 1 pod) | BR-V2-5, "Idempotency tổng" UC-02 AC8 |
| L4 | Idempotency key gửi SI = `order_return_id` | Verify SI nhận đúng key này khi tạo/phát hành, không phải key khác (vd order_id) | UC-02 AC5 |
| L5 (regression) | Luồng điều chỉnh **toàn bộ** hiện tại (đã có, không thuộc epic này) | Không bị ảnh hưởng bởi ledger mới thêm cho luồng partial — 2 luồng độc lập, không tranh chấp lock lẫn nhau | Regression |

---

## Nhóm 7 — Liên kết đơn trả ↔ hóa đơn: `order_return_ids` ⚠️ cơ chế MỚI, phụ thuộc chéo epic #64 (UC-03, §4.6, §4.10)

> Epic #64 (thiết kế `order_return_ids`) đang `state: opened` tại thời điểm viết test case này — **chưa merge ở đâu**, kể cả V3. Nhóm case này chỉ chạy được sau khi BE đã build cơ chế này cho V2 (xem [[epic-80-plan]] câu hỏi #3 — cần đồng bộ thiết kế với #64 trước).

| # | Kịch bản | Kỳ vọng | Ref |
|---|---|---|---|
| K1 | Tạo HĐĐC nháp từ 1 đơn trả | `order_return_ids` gắn **ngay khi tạo nháp**, mảng 1 phần tử `[order_return_id]` — kể cả **chưa phát hành** | UC-03 AC1 |
| K2 | 1 HĐĐC ứng với nhiều lần trả (nếu về sau hỗ trợ dồn — hiện tại epic này là 1:1) | **Một dòng = một hóa đơn**, không nhân bản dòng theo số đơn trả | UC-03 AC2, BR-V2-7 |
| K3 | HĐĐC đang ở trạng thái `draft`/`created` | Xóa nháp → gỡ liên kết + mở lại đơn trả (`unset` khỏi ledger) | UC-03 AC3, BR-V2-12 |
| K4 | HĐĐC đang `creating`/`publishing`/`deleting` | **Chặn** xóa nháp | BR-V2-12 |
| K5 | HĐĐC đã `published` trở lên | Không cho vào nhánh xóa nháp, giữ nguyên liên kết | BR-V2-12, UC-03 AC3 |
| K6 | HĐĐC nhận mã CQT (`provided`/`accepted`) | HĐ **gốc** chuyển trạng thái `modified` — không chặn tạo HĐĐC tiếp cho đơn trả khác của cùng order | BR-V2-7, §4.9 #12 |
| K7 | HĐ gốc đã `modified` (do 1 lần điều chỉnh trước) | Vẫn cho tạo HĐĐC tiếp cho đơn trả **khác** — guard chỉ chặn `replace`/`replaced`/`deleting`/`deleted`, không chặn `modified` | §4.9 #12, BR-V2-7 |
| K8 | Lọc hóa đơn theo `order_return_id` | 3 đường đều ra kết quả nhất quán: client tự lọc `order.invoices[]`, ES field top-level, DB filtered index kèm `IS NOT NULL` | UC-03 AC4, §4.6 "Consumer 3 đường" |
| K9 IDOR | Truy liên kết của store khác qua đoán id | **404**, không phải 403 | UC-03 AC5 |
| K10 | Callback CQT đến **trễ** hoặc **đảo thứ tự** (giả lập 2 callback gửi ngược thứ tự thời gian) | HĐĐC/HĐ gốc **không bị hạ cấp** trạng thái đã `accepted`/`provided` về trạng thái cũ hơn — xử lý idempotent theo message id | BR-V2-11, UC-03 AC6 |

---

## Nhóm 8 — Đối soát/miss-event ⚠️ SRS giả định job này "đã có" — thực tế KHÔNG có job nào

> Xem [[epic-80-plan]] — job đối soát cho luồng điều chỉnh toàn bộ **không tồn tại** trên code hiện tại (chỉ có `AutoInvoiceNotificationJob` gửi email). Chạy nhóm này **chỉ sau khi** chốt với BA/PO có làm job mới hay bỏ scope (xem câu hỏi #1 trong plan). Nếu chốt "bỏ scope MVP", đóng cả nhóm này thành known-limitation, không phải bug.

| # | Kịch bản | Kỳ vọng (NẾU có job đối soát) | Ref |
|---|---|---|---|
| J1 | Event Kafka cho 1 order_return bị **miss** (giả lập consumer downtime) | Job đối soát định kỳ phát hiện đơn trả `returned` chưa có trong ledger → tự trigger lại | §4.2 "Retry/đối soát" (giả định tái sử dụng) |
| J2 | Đơn trả `unsupported` (map fail) | Job đối soát **không** re-enqueue case này (terminal, cần xử lý tay) | UC-02 AC7 |

---

## Nhóm 9 — Phí vận chuyển `separate_line` (BR-V2-10, §4.9 #3/#4)

| # | Precondition | Kịch bản | Kỳ vọng | Ref |
|---|---|---|---|---|
| S1 | `auto_adjust_shipping_fee=true`, HĐ gốc có dòng `is_shipping_line`, đơn trả **hoàn tất chuỗi** (`Σ_returned = Σ_ordered`, đã có đơn trước) | Tạo HĐĐC cho lần trả cuối | **Thêm 1 dòng phí VC ghi âm** (giá trị nguyên dòng phí gốc, đảo dấu) — **không** qua công thức phân bổ §4.7 | BR-V2-10, §4.9 #3 |
| S2 | Như S1 nhưng đơn trả **chưa** hoàn tất chuỗi (còn dở dang) | Tạo HĐĐC cho lần trả giữa chừng | **Không** thêm dòng phí VC ở các lần trả trước, chỉ ở lần hoàn tất | §4.9 #3 "chỉ ở đơn trả hoàn tất chuỗi" |
| S3 | `auto_adjust_shipping_fee=false` hoặc `shipping_fee_mode=allocate` | Đơn trả hoàn tất chuỗi | **Không** xử lý phí VC ở luồng partial — `allocate` ngoài phạm vi epic này | BR-V2-10, §4.9 #4 |
| S4 | HĐ gốc **không** có dòng `is_shipping_line` | Đơn trả hoàn tất chuỗi | Không có gì để ghi âm, không lỗi | BR-V2-10 |

---

## Nhóm 10 — Thông báo & consent (UC-04)

| # | Bước | Kỳ vọng | Ref |
|---|---|---|---|
| N1 | Bật `notify_enabled`, để trống `notify_time_slots[]` → Lưu | Chặn lưu — bắt buộc ≥1 khung giờ nếu bật | UC-04 AC1 |
| N2 | Đến khung giờ cấu hình, có HĐĐC thành công + thất bại trong ngày | Thông báo giao diện + email đúng tổng số theo từng loại | UC-04 AC1 |
| N3 | Bấm Lưu, **không** tick "Tôi đã biết và đồng ý chịu hoàn toàn trách nhiệm" | Không lưu được | UC-04 AC2 |
| N4 | Tick + Lưu | `consent_date` = đúng thời điểm click Lưu, `enabled=true` | UC-04 AC2 |
| N5 | Consent chưa hợp lệ (chưa từng Lưu lần nào) | Luồng auto **không** được kích hoạt dù toggle bật trên UI | UC-04 AC3 |

---

## Nhóm 11 — Xóa cấu hình (UC-05)

| # | Precondition | Bước | Kỳ vọng | Ref |
|---|---|---|---|
| D1 | Config đang bật cả HĐ mới + HĐ điều chỉnh | Xóa cấu hình | Xóa **toàn bộ** (cả 2 khối), popup xác nhận + mô tả hệ quả | UC-05 AC1 |
| D2 | Thiếu quyền phát hành tại MST | Thử xóa | Chặn + alert | UC-05 AC2 |
| D3 IDOR | Store A | Gọi API xóa config id thuộc store B | **404** | UC-05 AC3 |
| D4 | Sau khi xóa | Đơn trả mới phát sinh | Không còn tự động tạo HĐĐC cho MST đó | FR5 |

---

## Nhóm 12 — Regression

| # | Case | Kỳ vọng | Ref |
|---|---|---|---|
| G1 | Luồng điều chỉnh **toàn bộ** hiện có (không phải epic này) | Hành vi giữ nguyên, không bị đổi bởi thay đổi gate `isFullyReturned()` | [[epic-80-plan]] mục thiết kế BE #4 |
| G2 | Order **không** có `order_return` nào | Auto invoice cho HĐ **mới** (`new_invoice`) chạy bình thường, không đụng logic mới | Baseline |
| G3 | Store chưa từng bật `auto_adjustment_invoice_enabled` | Không có gì thay đổi so với trước epic | Baseline |
| G4 | Chạy lại nhóm 5 (công thức) trên cả hóa đơn **GTGT** và **Bán hàng** | Kết quả đúng ở cả 2 loại; Bán hàng có thêm `tax_reduction_amount`, GTGT có `tax_amount` | §4.7.2 nhãn [GTGT]/[BH] |
| G5 | Publish HĐĐC lên SI | Response HĐ gốc **và** HĐĐC đều đúng trạng thái theo BR-V2-7, không có hóa đơn nào "kẹt" trạng thái trung gian nếu callback đến bình thường (không trễ) | UC-02 AC6 |
| G6 | HĐ gốc chưa đủ điều kiện (thiếu `series`/mã CQT) khi đơn trả tới | Tạm hoãn (`deferred`), chờ mẻ đối soát — không lỗi cứng | §4.9 #11 |

---

## Cách đối chiếu kết quả

**1. Response API** — đọc `line_items[]` của HĐĐC, lọc dòng có giá trị âm để soi nhanh; đối chiếu `original_invoice_*` trỏ đúng HĐ gốc.

**2. Công cụ độc lập** — `hddc-tester-v2.html` (tải trong `invoice-docs`, mở bằng trình duyệt): dán JSON HĐ gốc (einvoice) + đơn trả (order_return) → so từng field với response API thật (nhóm 5).

**3. DB (`sapo-einvoice-service`, SQL Server)** — sau khi migration ledger + `order_line_item_id` + STP snapshot chạy:
```sql
-- Ledger / chống trùng (nhóm 6) — tên bảng/cột thật tùy migration cuối cùng, đối chiếu lại khi code xong
SELECT TOP 30 * FROM AutoInvoiceResults
WHERE TenantId = <tenant_id> AND OrderReturnId IS NOT NULL
ORDER BY Id DESC;

-- order_line_item_id trên dòng HĐ gốc (nhóm 4)
SELECT TOP 30 Id, EInvoiceId, ItemId, OrderLineItemId
FROM EInvoiceLineItems
WHERE TenantId = <tenant_id> AND OrderLineItemId IS NOT NULL
ORDER BY Id DESC;
```

**4. `order.invoices[].order_return_ids`** (nhóm 7) — verify qua API order thật (Omni), không phải qua response SI/V2-Einvoice đơn thuần — đây là dữ liệu phía order-service, cần gọi đúng endpoint order để xác nhận field đã ghi.

## 📋 Bảng ghi kết quả

Tick khi chạy xong (chỉ chạy sau khi dev implement + migration đã lên môi trường test).

| Xong | Nhóm | Case | Ghi chú |
|---|---|---|---|
| [ ] | 1 — Cấu hình | C1–C9 | |
| [ ] | 2 — UI option mới | U1, U2, U7, U8 | |
| [ ] | 2 — UI option mới | **U3–U6** (phụ thuộc hướng chốt SRS/Figma) | Chờ PO chốt trước — xem plan |
| [ ] | 3 — Điều kiện kích hoạt | R1, R3–R14 | |
| [x] | 3 — Điều kiện kích hoạt | **R2** (bắt buộc hoàn tiền) | Q1 chốt: unpaid/partial → không HĐĐC |
| [ ] | 4 — Map dòng & combo | M1, M2, M4–M8 | |
| [ ] | 4 — Map dòng & combo | **M3** (rủi ro nhập nhằng variant_id) | Verify kỹ, khả năng cao là bug nếu sai |
| [ ] | 5 — Công thức tiền | F1–F3, F5–F10 | Đối chiếu `hddc-tester-v2.html` |
| [ ] | 5 — Công thức tiền | **F4** (STP snapshot) | Chờ dev bổ sung field, xem plan |
| [ ] | 6 — Ledger | L1–L5 | Chờ dev xây cơ chế mới |
| [ ] | 7 — order_return_ids | K1–K10 | Chờ đồng bộ thiết kế với epic #64 |
| [ ] | 8 — Đối soát | J1–J2 | Chờ chốt scope (có làm job hay không) |
| [ ] | 9 — Phí VC | S1–S4 | |
| [ ] | 10 — Thông báo/consent | N1–N5 | |
| [ ] | 11 — Xóa cấu hình | D1–D4 | |
| [ ] | 12 — Regression | G1–G6 | |

### Case cần verify/hỏi trước khi coi kết quả khác-kỳ-vọng là bug

- 🔴 **U2/U3–U6/R2 — mâu thuẫn SRS vs Figma, cần PO chốt trước khi build:** SRS nói V2 không yêu cầu hoàn tiền (BR-V2-2) + option mới là "Đã hoàn trả một phần" auto-lock "toàn bộ"; Figma (gắn 2026-08-25) đặt tên "Đã hoàn trả toàn bộ và 1 phần", helptext vẫn ghi "và đã hoàn tiền", không thấy auto-lock trong mockup. Đây **không phải case QA tự đoán được đúng/sai** — phải hỏi PO trước, xem [[epic-80-plan]] mục "Cập nhật 2026-08-26".
- **U6** — 2 option có dùng chung `condition_value: "returned"` không? Nếu có, BE phân biệt bằng gì lúc runtime?
- **M3** — rủi ro nhập nhằng khi fallback `variant_id` gặp ≥2 dòng cùng variant — SRS tự nhận đây là hạn chế đã biết, cần xác nhận mức độ chấp nhận được cho MVP (chỉ ảnh hưởng HĐ tạo trước uplive).
- **F4** — phụ thuộc field STP snapshot **chưa tồn tại** trên `EInvoice` ở code hiện tại — case này *sẽ* fail cho tới khi bổ sung, không phải bug mới.
- **Toàn bộ nhóm 6, 7, 8** — cơ chế mới hoàn toàn hoặc phụ thuộc epic khác chưa xong (#64). Xem [[epic-80-plan]] trước khi report bug ở các nhóm này.
- **U5** — chiều "bỏ tích một phần → mở khóa toàn bộ" là suy luận hợp lý từ SRS, không phải câu chữ tường minh — verify hành vi thật với dev trước.

## Liên kết

- [[epic-80-plan]] — plan + phân tích gap SRS-vs-code
- [[omni-einvoice-service-tong-quan]] / [[omni-frontend-v3-einvoice-tong-quan]]
- [[epic-61-phi-van-chuyen-hoa-don-v2/epic-61-test-cases]] — mẫu format + case phí VC gốc dùng lại ở nhóm 9
- GitLab epic [#80](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/80) · [#64](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/64) · [#69](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/69)
