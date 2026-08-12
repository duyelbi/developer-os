---
created: 2026-08-11 09:15
updated: 2026-08-12 10:45
status: Proposed
project: "[[10_Projects/sapo-invoice/README]]"
---

# Epic #61 — Cấu hình thể hiện phí vận chuyển trên hóa đơn V2 (shipping fee)

Work item: `https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/61`, module `invoice-core-v2`. Bản gốc SRS ở `invoice-docs/docs/invoice-core-v2/phi-van-chuyen-hoa-don/srs.md` — từ 2026-08-11 developer-os là nguồn chính (xem [[10_Projects/sapo-invoice/README]] mục "SRS, Decision, Bug"), nội dung SRS chép đầy đủ vào note này.

**Cập nhật 2026-08-12 — SRS v0.6 (MR `invoice-docs!105`, đã update mới nhất ở invoice-docs).** BA (Dung) tự xác nhận độc lập đúng 2 mâu thuẫn phát hiện qua Figma trước đó (xem mục "Lịch sử phát hiện" cuối note) — nội dung dưới đây đã theo v0.6, không còn open question.

## Mục tiêu

Cho phép merchant **cấu hình cách thể hiện phí vận chuyển của order lên hóa đơn V2** (`invoice-core-v2`), thay cho hành vi mặc định hiện tại (hóa đơn dựng từ order **không** lấy/không thể hiện phí vận chuyển). Ưu tiên chế độ **"Thêm 1 dòng phí vận chuyển"** (`separate_line`) — gộp toàn bộ phí giao hàng của order thành **một dòng** hàng hóa/dịch vụ (`item_type = 1`) trên hóa đơn, với **tên dòng cấu hình được** và **tùy chọn tự động điều chỉnh** khi có hóa đơn điều chỉnh tự động.

Phạm vi kênh: **Invoice Core V2** (lớp trung gian Sapo POS ↔ nhà cung cấp HĐĐT). Chỉ áp khi nhà cung cấp phát hành là **Sapo Invoice**. Áp cho cả hóa đơn **GTGT** và **Bán hàng**; cả lập thủ công từ order (`create_draft`) và **Auto Invoice**. Chỉ hỗ trợ **VND**.

## Bối cảnh — nguồn dữ liệu `order.delivery_fee`

- **Sapo POS/Omni** là nguồn order chứa phí vận chuyển, dạng `order.delivery_fee` — SRS mô tả là **mảng** `delivery_fee[]` (một order có thể có một hoặc nhiều phí), mỗi phần tử phẳng `{ shipping_cost_id, shipping_cost_name, fee }`.
- **Đại lượng nguồn:** `F = Σ delivery_fee[].fee` — tổng mọi phí của order.
- **KHÁC hệ "V3"** (`shipping_lines[]`, có thuế + chiết khấu + phân bổ, thuộc `invoice-app` — xem mục "Xác nhận chéo" bên dưới, hai hệ hoàn toàn tách biệt).
- **V2 không có thuế/chiết khấu cho phí vận chuyển:** `delivery_fee` không mang `tax_lines` và không mang `discount_allocations` → dòng phí VC: `tax_name=KCT`, `tax_amount=0`, `total_discount_amount=0`. Công thức **không** rẽ theo `order.tax_treatment` (inclusive/exclusive) — mỗi `fee` là giá cuối khách trả.
- Cấu hình (`shipping_fee_mode`, `shipping_fee_item_name`, `auto_adjust_shipping_fee`) là **cài đặt cấp store**, đọc/ghi theo `store_id`/`tenant_id` lấy từ **session server**, không từ client.
- Sapo Invoice (nhà cung cấp duy nhất áp dụng) **không tự suy ra phí VC** — nếu V2 không gửi dòng phí thì hóa đơn không có phí VC (hành vi mặc định hiện tại).

⚠️ **`B0` — vẫn còn mở, KHÁC với 2 mâu thuẫn đã resolve ở v0.6:** xem mục "Sai lệch chưa giải quyết" bên dưới — SRS giả định `delivery_fee` là mảng nhưng code thật (`sapo-einvoice-service`) hiện là object đơn. Đây là câu hỏi kỹ thuật riêng, chưa được MR 105 đề cập, vẫn cần xác nhận với BA/Omni trước khi merge thật.

## Phạm vi

**In-scope (MVP, v0.6):**
- Màn cấu hình cấp store trong Cài đặt tự động Sapo Invoice — 3 field:
  - `shipping_fee_mode` = `none` (mặc định) / `separate_line`
  - `shipping_fee_item_name` — tên dòng phí, autofill "Phí giao hàng", **bắt buộc**, **tối đa 255 ký tự**, chỉ áp khi `separate_line`
  - `auto_adjust_shipping_fee` — checkbox, **mặc định bỏ tích**, chỉ hiện khi `separate_line`
- Chỉ hỗ trợ nhà cung cấp Sapo Invoice — provider khác không hiển thị cấu hình, không dựng dòng phí.
- Dòng cảnh báo pháp lý hiển thị khi bật lấy phí VC (nguyên văn ở mục "Tuân thủ" bên dưới).
- `separate_line`: dựng hóa đơn từ order có `delivery_fee` → thêm đúng 1 dòng phí vận chuyển (`item_type=1`, `quantity=1`, `is_shipping_line=true`), tính theo Domain Model bên dưới; dòng phí tham gia tổng hóa đơn như dòng hàng hóa/dịch vụ bình thường.
- Áp cho cả `create_draft` thủ công và Auto Invoice.
- **Điều chỉnh hóa đơn tự động có điều kiện:** `auto_adjust_shipping_fee` tích → dòng phí VC bị ghi âm cùng các dòng khác khi hệ thống tự tạo hóa đơn điều chỉnh; bỏ tích → loại trừ dòng phí khỏi điều chỉnh.

**Out-of-scope (bản này):**
- Nhà cung cấp khác Sapo Invoice.
- Chế độ **phân bổ** (`allocate`) — phân bổ phí VC vào các dòng hàng hóa/dịch vụ, như V3. Để Future.
- Thuế/chiết khấu cho phí vận chuyển.
- Chỉnh sửa phí VC thủ công trên từng dòng sau khi đã dựng (đi theo luồng sửa dòng hàng hiện hữu).
- Backfill phí VC cho hóa đơn cũ.
- Bản thể hiện/XML CQT phía nhà cung cấp.

**Future:** chỉ còn chế độ `allocate`; cấu hình **đơn vị/tính chất** của dòng phí VC theo store. (Tùy biến **tên** dòng phí đã vào scope từ v0.6 — không còn ở Future.)

**Quyền:** không thêm quyền mới — theo quyền hiện hành của module V2 (`read_einvoice` mở form, `write_einvoice` tạo/sửa nháp, quyền phát hành của nhà cung cấp).

## User Stories (UC gốc trong SRS)

**UC-01 — Cấu hình chế độ thể hiện phí vận chuyển**
> Là kế toán/nhân viên lập hóa đơn, tôi muốn chọn cách phí vận chuyển của order được thể hiện trên hóa đơn, để hóa đơn phản ánh đúng phí đã thu khi có cung cấp dịch vụ vận chuyển.

AC đáng chú ý (v0.6, thêm mới):
- **AC7 — `shipping_fee_item_name`:** chỉ áp khi `separate_line`. Autofill mặc định "Phí giao hàng", user sửa được; **bắt buộc — không cho lưu rỗng**; **tối đa 255 ký tự**. Là `item_name` của dòng phí VC khi dựng hóa đơn. Đổi tên chỉ áp hóa đơn tạo **sau** thời điểm lưu (đồng bộ BR02) — hóa đơn đã tạo giữ tên đã lưu (snapshot).
- **AC8 — `auto_adjust_shipping_fee`:** checkbox mặc định bỏ tích, chỉ hiện khi `separate_line`. Tích → khi điều chỉnh hóa đơn, dòng phí VC bị ghi âm cùng các dòng khác (nhận biết qua `is_shipping_line`); bỏ tích → loại trừ dòng phí khỏi điều chỉnh.

**UC-02 — Thêm 1 dòng phí vận chuyển khi dựng hóa đơn từ order**
> Là kế toán lập hóa đơn từ order Sapo POS, tôi muốn hệ thống tự thêm một dòng phí vận chuyển vào hóa đơn khi dựng từ order, để không phải nhập tay và hóa đơn thể hiện đúng phí giao hàng đã thu.
>
> Preconditions: provider phát hành = Sapo Invoice; `shipping_fee_mode = separate_line`; order có ≥ 1 phí vận chuyển.

AC-2 (v0.6, viết lại): `item_name` của dòng phí VC **lấy từ cấu hình `shipping_fee_item_name`** (không còn cố định) — không lấy `delivery_fee.shipping_cost_name`.

AC-11 (v0.6, mới): dòng phí vận chuyển dựng ra mang cờ **`is_shipping_line = true`** — để hệ thống nhận biết/xử lý riêng dòng phí khi điều chỉnh hóa đơn (phục vụ AC8/BR08). Các dòng khác `is_shipping_line = false`/null.

(2 UC này đã từng breakdown thành 3 issue GitLab — US-1/US-2/US-3, đã bị xóa, xem mục "Trạng thái triển khai" bên dưới. Cursor prompt cần viết lại theo v0.6.)

## Business Rules (v0.6)

| ID | Quy tắc |
|----|---------|
| `BR01` | Gộp **toàn bộ** phí vận chuyển của order thành **đúng một** dòng phí VC (`item_type=1` products, `quantity=1`), `amount = Σ delivery_fee[].fee`. Điều kiện tạo dòng: order có ≥ 1 phí (không phụ thuộc giá trị — `Σ fee=0` vẫn tạo dòng 0đ, xem BR07); order không có phí → không tạo. |
| `BR02` | Đổi chế độ phí VC chỉ áp cho hóa đơn được tạo **sau** thời điểm lưu cấu hình; hóa đơn đã tạo trước đó (kể cả nháp, sau này mở sửa lại) **không** tự áp cấu hình mới — mốc tính theo thời điểm **tạo**, không phải thời điểm sửa. |
| `BR03` | Dòng phí VC **không thuế & không chiết khấu**: `tax_name=KCT` (`tax_rate=0`, `tax_amount=0`) — dùng `KCT` (không chịu thuế), không dùng `KKKNT`; mọi field chiết khấu = 0. Công thức không rẽ theo `tax_treatment`. |
| `BR04` | Mọi thao tác mở/sửa/phát hành HĐ và đọc/ghi cấu hình chỉ cho store hiện tại. `store_id`/`tenant_id` lấy từ session. Truy `invoice_id`/cấu hình không thuộc store → **404** (không 403). |
| `BR05` **(v0.6, viết lại)** | `item_name` của dòng phí VC **lấy từ cấu hình `shipping_fee_item_name`** của store (**không** lấy `delivery_fee.shipping_cost_name`). Cấu hình **autofill mặc định "Phí giao hàng"**, **bắt buộc — không cho lưu rỗng**, **tối đa 255 ký tự**. Đổi tên chỉ áp hóa đơn tạo sau (đồng bộ BR02); hóa đơn đã tạo giữ tên đã lưu. `unit_name` để trống. Chỉ áp mode `separate_line`. |
| `BR06` | Server **tính lại** trường tiền dòng phí VC trên giá trị **chưa làm tròn**, **làm tròn HALF_UP khi truyền sang nhà cung cấp** — không tin số client. Dòng phí cộng vào tổng hóa đơn như dòng `products`. |
| `BR07` | Dòng phí **0đ** (khi `Σ fee=0`) vẫn được tạo và phát hành bình thường; `tax_name` vẫn `KCT`. |
| `BR08` **(v0.6, viết lại)** | Dòng phí VC chịu **chung** logic/cấu hình cấp hóa đơn có sẵn (đổi ký hiệu, "không hiện chiết khấu theo nguồn đơn"...) — **trừ điều chỉnh hóa đơn, nay có điều kiện:** theo checkbox `auto_adjust_shipping_fee` (mặc định bỏ tích) — **tích** → khi điều chỉnh **toàn bộ** hóa đơn, dòng phí VC **bị ghi âm** cùng các dòng khác (nhận biết qua `is_shipping_line`, BR10); **bỏ tích** → **loại trừ** dòng phí khỏi điều chỉnh. Nếu store bật *Tự động tạo và phát hành hóa đơn điều chỉnh* thì diễn ra tự động. Dòng `KCT` không thuộc diện giảm thuế theo Nghị quyết. |
| `BR09` | **Giới hạn nhà cung cấp — chỉ Sapo Invoice:** cấu hình + dựng dòng phí VC chỉ áp khi `publishing_provider=sapo_invoice`. Đổi provider khỏi Sapo Invoice → dòng phí bị loại + tính lại tổng (tự động, KHÔNG cảnh báo); đổi lại → dựng lại theo cấu hình. |
| `BR10` **(v0.6, mới)** | **Marker nhận biết dòng phí VC (`is_shipping_line`):** dòng phí vận chuyển dựng ra mang cờ `is_shipping_line = true` để hệ thống **nhận biết** dòng phí khi điều chỉnh hóa đơn (phục vụ BR08). Các dòng khác `is_shipping_line = false`/null. Marker chỉ để nhận biết, **không** đổi logic thuế/tiền của dòng phí. |

## Domain Model — công thức dòng phí vận chuyển

Chỉ hỗ trợ VND (`exchange_rate=1`). Dòng phí VC là **một** dòng `item_type=1` (products), `is_shipping_line=true`, gộp toàn bộ phí vận chuyển của order.

**Nguyên tắc chung:** server tính lại trên giá trị **chưa làm tròn**; **làm tròn HALF_UP** chỉ áp khi truyền sang nhà cung cấp. V2 không có thuế/chiết khấu cho phí VC → dòng phí luôn `KCT`, không rẽ theo `tax_treatment`.

**Bảng dựng dòng** (điều kiện: order có ≥ 1 phí; `F = Σ delivery_fee[].fee`):

| Trường V2 (`line_items[i]`) | Giá trị dòng phí VC |
| :--- | :--- |
| `item_type` | `1` (products) |
| `is_shipping_line` | `true` *(BR10, marker nội bộ)* |
| `item_name` | Từ cấu hình `shipping_fee_item_name` (mặc định "Phí giao hàng") *(BR05)* |
| `unit_name` | Để trống |
| `quantity` | `1` |
| `tax_name` (+ `tax_rate`) | `KCT` (`tax_rate=0`) |
| `unit_price` | `= F` |
| `amount` (`= quantity × unit_price`) | `= F` |
| `unit_discount_amount`/`discount_rate` | `0` |
| `total_discount_amount` | `0` |
| `amount_without_vat` (`= amount − total_discount_amount`) | `= F` |
| `tax_amount` | `0` |
| Thành tiền sau thuế | `= F` |

**Ví dụ 1 (1 phí, order SON02820, `fee=10000`, `tax_treatment=inclusive`):** `F=10000` → dòng phí: `item_type=1`, `item_name` theo cấu hình (mặc định "Phí giao hàng"), `quantity=1`, `KCT`, `unit_price=amount=10000`, `amount_without_vat=10000`, `tax_amount=0`. Kết quả không đổi dù `inclusive`/`exclusive`.

**Ví dụ 2 (nhiều phí):** đơn có 2 phí `8000` + `2000` → `F=10000` → dòng phí gộp y hệt ví dụ 1, `quantity=1`.

**Ảnh hưởng tổng hóa đơn (dòng phí là `item_type=1` → cộng như dòng hàng hóa/dịch vụ):**
- `total_sale_amount += F`, `total_discount_amount += 0`, `total_amount_without_vat += F`, `total_vatamount += 0` (KCT), `total_amount += F`.
- Khối tổng theo thuế suất: nhóm **`KCT`** — `amount_without_vat(KCT) += F`, `tax_amount(KCT) += 0`.
- Hóa đơn Bán hàng: dòng `KCT` **không** thuộc diện giảm thuế theo Nghị quyết → không sinh `tax_reduction_amount`.

**Đổi provider Sapo Invoice → khác (order SON02820, `F=10000`, ký hiệu `X_*` = tổng các dòng hàng khác không đổi):**

| Trạng thái | `total_sale_amount` | `total_amount_without_vat` | `total_vatamount` | `total_amount` | Nhóm `KCT` |
| --- | ---: | ---: | ---: | ---: | ---: |
| A · provider=Sapo Invoice | `X_sale+10.000` | `X_nwv+10.000` | `X_vat+0` | `X_amt+10.000` | `(khác)+10.000` |
| B · đổi sang provider khác | `X_sale` | `X_nwv` | `X_vat` | `X_amt` | `(khác)` |
| Δ (B−A) | −10.000 | −10.000 | 0 | −10.000 | −10.000 |

Hành vi A→B: (1) loại dòng phí VC khỏi `line_items[]`, không gửi payload; (2) tính lại toàn bộ tổng + khối tổng theo thuế suất trên tập dòng còn lại; (3) nếu không còn dòng `KCT` khác → nhóm `KCT` biến mất khỏi khối tổng; (4) tự động, KHÔNG cảnh báo, cấu hình phí VC cũng ẩn. Đổi ngược B→A: dựng lại dòng phí theo cấu hình hiện tại (không khôi phục "thủ công").

## UI Specs (v0.6)

**Màn cấu hình** (Cài đặt tự động — Quản lý kết nối Sapo Invoice, chỉ hiện khi provider=Sapo Invoice):

| STT | Trường | API field | Mô tả |
| :-: | --- | --- | --- |
| 1 | Chế độ phí vận chuyển | `shipping_fee_mode` | `none` (mặc định) / `separate_line`. (`allocate` để Future, chưa hiển thị.) |
| 2 | **Tên dòng phí trên hóa đơn** | `shipping_fee_item_name` | Chỉ hiện/áp khi `separate_line`. Autofill sẵn "Phí giao hàng", sửa được; **bắt buộc**; **tối đa 255 ký tự**. Là `item_name` của dòng phí VC *(BR05)*. |
| 3 | ☐ Tự động điều chỉnh phí giao hàng | `auto_adjust_shipping_fee` | Checkbox, **mặc định bỏ tích**, chỉ hiện khi `separate_line`. Tích → ghi âm dòng phí khi điều chỉnh HĐ; bỏ tích → loại trừ *(BR08, BR10)*. |
| 4 | Cảnh báo pháp lý | — | Hiện khi chọn `separate_line` (nguyên văn ở mục "Tuân thủ") |
| 5 | Cảnh báo khi điều chỉnh hóa đơn | — | Hiện khi chọn `separate_line` (nguyên văn ở mục "Tuân thủ") |

**Chuỗi UI trường "Tên dòng phí trên hóa đơn" (nguyên văn — dùng làm expected string cho FE/QA):**
- Nhãn trường: `Tên dòng phí trên hóa đơn`
- Giá trị autofill mặc định (trong ô): `Phí giao hàng`
- Placeholder (khi ô trống): `Nhập tên dòng phí…`
- Helptext (dưới ô): `Tên này hiển thị làm tên hàng hóa/dịch vụ của dòng phí trên hóa đơn.`
- Lỗi khi để trống: `Vui lòng nhập tên dòng phí trên hóa đơn.`
- Lỗi khi vượt 255 ký tự: `Tên dòng phí tối đa 255 ký tự.`

**Mapping order → dòng phí VC (`separate_line`):** giống bảng Domain Model ở trên.

## Tuân thủ (nguyên văn cảnh báo, v0.6)

**Cảnh báo pháp lý (khi bật lấy phí VC):**
> ⚠️ Chỉ cài đặt hiển thị phí vận chuyển khi bạn **thực sự cung cấp dịch vụ vận chuyển**. Nếu phí do **bên thứ ba thu hộ**, khoản này không thuộc đối tượng phải xuất hóa đơn *(Nghị định 254/2026/NĐ-CP)*.

**Cảnh báo khi điều chỉnh hóa đơn (chế độ `separate_line`, câu chữ đổi nhẹ ở v0.6 — thêm "tích chọn"):**
> ⚠️ Nếu **tích chọn** và đã cài đặt **Tự động tạo và phát hành hóa đơn điều chỉnh**, hệ thống sẽ tự động điều chỉnh dòng phí vận chuyển cùng các dòng hàng hóa, dịch vụ khi điều chỉnh hóa đơn có phát sinh phí vận chuyển.

**Khác:** `store_id`/`tenant_id` luôn từ session, IDOR → 404 (BR04). Replace strategy khi sửa/phát hành: gửi lại **toàn bộ** `line_items[]` (gồm dòng phí VC) — bỏ sót = xóa dòng đó phía nhà cung cấp. Auto Invoice dựng dòng phí VC trong pipeline async, không giả định phát hành tức thì — cutoff 23:55 `Asia/Ho_Chi_Minh` giữ nguyên. Không đổi vòng đời `status` hóa đơn. Không thu thập PII mới.

---

## ⚠️ Sai lệch chưa giải quyết — SRS giả định `delivery_fee` là mảng, code thật là object đơn

**Khác với 2 mâu thuẫn đã resolve ở v0.6 (xem "Lịch sử phát hiện" bên dưới) — cái này MR 105 không đề cập, vẫn còn mở.**

SRS chốt: *"order có thể có MỘT HOẶC NHIỀU phí vận chuyển"* — `order.delivery_fee` là **mảng** `delivery_fee[]`, công thức `amount = Σ delivery_fee[].fee`.

**Code thật trong `sapo-einvoice-service` hiện tại lại là object đơn, không phải mảng:**

```java
// OrderResponse.java:57 và OrderDomain.java:58
private DeliveryFeeResponse deliveryFee;   // KHÔNG phải List<DeliveryFeeResponse>
private DeliveryFeeDomain deliveryFee;
```

`DeliveryFeeDomain`/`DeliveryFeeResponse` (`model/order/`) đúng 3 field như SRS mô tả (`shippingCostId`, `shippingCostName`, `fee`) — nhưng là **1 object**, không phải list. Thêm nữa: **`getDeliveryFee()` hiện KHÔNG được gọi ở bất kỳ đâu trong codebase** — field này được parse từ order API nhưng hoàn toàn chưa dùng tới trong flow tạo hóa đơn (xác nhận bằng `grep -rn "getDeliveryFee()" src/main/java` → rỗng).

**Cần làm rõ trước khi code (điều tra sau, theo quyết định của user):**
1. Omni/POS thực tế trả `delivery_fee` là mảng hay object đơn?
2. Nếu Omni trả mảng thật → `OrderResponse`/`OrderDomain` cần đổi field này thành `List<DeliveryFeeResponse>` (rủi ro thấp — grep hiện tại cho thấy field chưa dùng ở đâu khác).
3. Nếu Omni luôn chỉ trả 1 phí → SRS nên sửa lại đơn giản hơn (bỏ hẳn phần Σ/gộp nhiều phí).

→ **Nên hỏi lại BA (Nguyễn Thị Thu Dung) hoặc đối chiếu trực tiếp 1 order thật có `delivery_fee` trước khi bắt đầu code.**

## Repo đích — SỬA LẠI hiểu nhầm ban đầu

Epic gắn `module::invoice-core-v2` trong group `sapo-money/sapo-invoice`, dễ tưởng code nằm ở `sapo-invoice-admin-service`/`sapo-invoice-admin-frontend`. **Sai** — xác nhận qua epic phụ thuộc, toàn bộ task backend/frontend đều ghi rõ code đích là:

- Backend: **`sapo-einvoice-service`** — cụ thể `service/publisher/sapoinvoice/SapoInvoiceService.java`, `model/einvoice/EInvoiceLineItemRequest.java`, `domain/EInvoiceLineItem.java`
- Frontend: **`sapo-frontend-v3`** — cụ thể `src/page/EInvoice/edit/component/TableOrderLineItem/OrderLineItem/EinvoiceTableLineItems.tsx`

Đây là 2 repo Omni (group `sapo-core/sapo-microservices` + `sapo-presentation`), **không phải** `sapo-invoice-admin-service`/`admin-frontend`. Xem [[10_Projects/sapo-invoice/omni-einvoice-service-tong-quan]].

## Dependency: Epic "Tính chất hàng hóa dịch vụ" (&46) — nhãn "Done Code", verify lại trước khi tin

Epic phí vận chuyển này **dùng chung công thức tính tổng** (§9.2/§9.3 domain model ở trên) từ epic `item_type` (Epic &46, 3 issue con US-1 #49 / US-2 #50 / US-3 #51, tất cả nhãn `status::Done Code`). Kiểm tra code thật:

| Phần | Trạng thái thật |
|---|---|
| `EInvoiceLineItem.itemType` (domain), `EInvoiceLineItemDTO/Response.itemType` | ✅ Đã có, kiểu `Integer` — đúng SRS |
| `SapoInvoiceLineItem.itemType` (payload gửi SI) | Kiểu `String` |
| Map `Integer itemType` → `String` khi build payload gửi SI | ❌ **CHƯA** — `SapoInvoiceService.java:677` vẫn hardcode `sapoInvoiceLineItem.setItemType("products")` cho **mọi** dòng, không đọc từ `eInvoiceLineItem.getItemType()`. Đây chính là việc US-2 ticket #50 mô tả (task B5) nhưng có vẻ chưa merge dù nhãn ghi "Done Code". |
| FE: `item_type` trên `EinvoiceLineItem` (FE type) đang dùng cho `variant.product_type` (`FormEinvoice.tsx:921`) | ⚠️ **Xung đột đã biết** — chính epic &46 tự ghi nhận "F0 (chặn)" ở ticket US-1 (#49), có vẻ chưa xử lý |

→ **Đừng tin nhãn "Done Code" ở board là code đã chạy đúng trên nhánh sẽ merge tiếp.** Epic phí vận chuyển này thiết kế **né hẳn** xung đột `item_type` ở FE bằng cách dùng marker riêng `is_shipping_line` (không đụng `item_type`) — xem Cursor prompt.

## Cấu hình — 3 setting, đã có sẵn pattern EAV để cắm vào

`SapoInvoiceSetting` (`domain/sapoinvoice/SapoInvoiceSetting.java`) là bảng EAV: `tenantId + settingKey(enum) + settingValue(String)`. Enum hiện có: `auto_apply_tax_reduction_rate`, `auto_fill_invoice_series_by_location`, `auto_hidden_reduction_by_source`, `auto_fill_anonymous_customer`, `disable_adjustment_calculation_invoice`, `invoice_payment_methods`, `einvoice_explode_composite_lines`.

Thêm 3 giá trị mới: `shipping_fee_mode` (String, default `"none"`), `shipping_fee_item_name` (String, bắt buộc khi `separate_line`, ≤255 ký tự), `auto_adjust_shipping_fee` (Boolean, default `false`). **Không cần migration DB cho bảng settings** — API `POST/GET /invoice_providers/sapo_invoice/settings` (`SapoInvoiceController.java:271,297`) đã tổng quát qua `Map<String, Object>`.

**Riêng marker `is_shipping_line` (BR10) CẦN 1 migration nhỏ** — không phải cho settings, mà cho bảng `EInvoiceLineItems` (thêm cột `IsShippingLine BIT NULL`). Lý do: đã thử 2 phương án không cần migration (so `item_name`, tái dùng `itemCode`) và cả 2 đều không an toàn — xem chi tiết lý do trong Cursor prompt mục A6.

**Màn UI đã xác nhận tồn tại thật** (xem Figma trong "Lịch sử phát hiện") — "Quản lý kết nối Sapo Invoice" → "Cài đặt chung", không cần dựng màn mới.

---

## Xác nhận chéo — `invoice-app` KHÔNG phải repo đích (dù trông rất giống)

Đã khảo sát thêm `invoice-app` (repo thứ 3, group `bizweb-vnext-microservices/app`) để loại trừ khả năng nhầm. Kết quả củng cố kết luận ở trên, không lật ngược:

- **`sapo-invoice-admin-service` xác nhận KHÔNG chứa domain này** — grep toàn bộ không thấy `createDraft`/`publishing_provider`/Auto Invoice. Đây là service tuân thủ **TVAN** (ký số, truyền nhận CQT) — khác hẳn domain "dựng hóa đơn từ order".
- **`invoice-app` có field `shippingLines` (số nhiều, đúng chính tả "V3"), KHÔNG phải `delivery_fee`** — `OrderResponse.java:57` → `List<OrderShippingLine> shippingLines`. Khớp đúng với SRS: bản V3 native dùng `shipping_lines[]` — tức **`invoice-app` = hệ thống V3**, một hệ **khác**, không phải "invoice-core-v2".
- **`invoice-app` cũng có `item_type`/4 giá trị y hệt** và đã wire vào tính tổng — **không phải trùng lặp đáng ngờ**, 4 phân loại này là chuẩn dòng hàng hóa đơn VAT Việt Nam, nhiều hệ thống độc lập cùng implement là bình thường.
- `invoice-app` có doc SRS shipping-fee **riêng** — 3 mode (`none/separate_line/allocate`) + field tùy biến tên dòng phí. Đây là **spec của V3** (nguồn cảm hứng "đồng bộ UI" của MR 105, đúng như tiêu đề MR: "đồng bộ UI với V3 cho separate_line") — không phải bản cập nhật của SRS V2 đang xét.

→ Kết luận repo đích **giữ nguyên `sapo-einvoice-service` + `sapo-frontend-v3`** — không đổi sang `invoice-app`.

## Trạng thái triển khai

SRS đã từng breakdown thành 3 issue GitLab (project `invoice-docs`) US-1/US-2/US-3 — **cả 3 đã bị xóa** (2026-08-11, vướng lỗi gắn Epic qua MCP tool — xem [[project_gitlab-epic-child-issue-convention]] trong memory). User quyết định tự tạo lại issue thủ công trên GitLab. Nội dung story (theo v0.5, **cần viết lại theo v0.6** — thêm AC7/AC8/AC11) không còn giữ ở đây, tham khảo Cursor prompt để lấy nội dung task chi tiết nhất.

## Lịch sử phát hiện (đã resolve ở v0.6)

Quá trình dẫn tới SRS v0.6 — giữ lại để hiểu bối cảnh, không cần đọc lại khi code:

1. **2026-08-11:** Mở 2 link Figma đính trong comment epic (Lê Thị Xâm, 2026-08-06) — phát hiện 2 điểm SRS v0.5 (text) không khớp design: (a) tên dòng phí design cho sửa được, SRS nói cố định; (b) "tự động điều chỉnh" design là checkbox thật, SRS nói chỉ là cảnh báo tĩnh.
2. User xác nhận: *"đúng vậy, docs srs chưa update, đã thống nhất như figma thể hiện"* và *"đúng, là checkbox thật, là 1 tính năng trong task này"* — báo BA cập nhật SRS.
3. **2026-08-12:** BA tạo MR `invoice-docs!105` (v0.6) — độc lập đi đến đúng 2 kết luận trên, thêm chính xác `shipping_fee_item_name`, `auto_adjust_shipping_fee`, và tự đề xuất thêm marker `is_shipping_line` (BR10) — khớp với hướng "cần 1 field đánh dấu riêng, không dựa vào `item_name`" mà quá trình phân tích kỹ thuật (đọc code `edit()`, `buildAdjustmentLineItemsFromBaseline`, rủi ro tái dùng `itemCode`) đã đi tới độc lập.

## Liên kết

- MR SRS v0.6: `https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/merge_requests/105`
- [[epic-61-cursor-prompt-implement]] — prompt Cursor, đã cập nhật theo v0.6
- [[10_Projects/sapo-invoice/omni-einvoice-service-tong-quan]]
- [[10_Projects/sapo-invoice/omni-frontend-v3-einvoice-tong-quan]]
- Bản gốc SRS (lịch sử, không còn là nguồn chính): `invoice-docs/docs/invoice-core-v2/phi-van-chuyen-hoa-don/srs.md`
