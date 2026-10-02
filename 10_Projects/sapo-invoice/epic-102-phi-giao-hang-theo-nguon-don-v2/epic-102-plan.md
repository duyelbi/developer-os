---
created: 2026-09-30 10:00
status: Sẵn sàng implement — Figma đã có (còn 3 trạng thái chưa vẽ, xem mục UI)
project: "[[10_Projects/sapo-invoice/README]]"
---

# Epic #102 — [V2] Phí giao hàng theo nguồn đơn (chỉ dựng dòng phí cho nguồn đơn được chọn)

- GitLab epic: [#102](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/102) (author `dungntt6`, assignee `phuongnt20` · `duynd7`, labels `T::Newfeature` · `tier::2` · `workflow::ready`)
- Child issue: `sapo-money/sapo-invoice/sapo-invoice-admin-service#175` (label `System::V2`, assignee `duynd7`)
- Epic gốc: [[epic-61-phi-van-chuyen-hoa-don-v2]] (&61) · Bản V3: &101 (đã lên staging `invoice-app`, commit `e90cc984`)
- SRS: `invoice-docs` `docs/invoice-core-v2/phi-van-chuyen-hoa-don/srs.md` **v0.9** (mục đánh dấu 🆕, BR12)
- Repo: **`sapo-einvoice-service`** (BE) + **`sapo-frontend-v3`** (FE màn Cài đặt hóa đơn điện tử)
- Prompt Cursor: [[epic-102-cursor-prompt-implement]] · Test case: [[epic-102-test-cases]]

## Tóm tắt

Hiện `shipping_fee_mode = separate_line` bật/tắt dòng "Phí giao hàng" **chung toàn store**. Đơn sàn mang phí "kỹ thuật" 0đ vẫn sinh dòng phí 0đ vô nghĩa, và phí sàn thu hộ không thuộc đối tượng phải xuất HĐ (NĐ 254/2026). Epic thêm trường **Nguồn đơn** (multi-select) vào cấu hình phí: chỉ order có `order.source_id` thuộc danh sách đã chọn mới được dựng dòng phí; không khớp thì kết quả như `none`.

## Quyết định đã chốt (user, 2026-09-30) — ⚠️ lệch SRS v0.9

| # | Quyết định | SRS nói | Lý do |
|---|---|---|---|
| D1 | **Giống V3:** chọn "Tất cả" thì lưu **danh sách đầy đủ** id nguồn đang áp dụng. `null`/thiếu field chỉ có nghĩa **store cũ chưa từng lưu** nguồn đơn → áp mọi nguồn (kể cả order không có nguồn) | BR3: "Tất cả" gồm cả nguồn **thêm mới sau này**; BR4: order không nguồn vẫn dựng khi "Tất cả" | User thấy "null = tất cả" không hợp lý; đồng nhất hành vi V2/V3 |
| D2 | Lưu **id** nguồn (`String`), so với `order.source_id` | BR1 V2: lưu `id` | Khớp quy ước V2 (`auto_hidden_reduction_by_source`, dropdown `sapo-frontend-v3` đều dùng id). V3 lưu alias, V2 **không** theo điểm này |

**Hệ quả D1 (cần PO/BA sửa SRS BR3/BR4 để QA không lệch expected):**
- Store đã lưu "Tất cả" rồi tạo nguồn bán hàng mới → đơn từ nguồn mới **không** có dòng phí cho tới khi merchant tích thêm.
- Sau lần lưu đầu, order **không có nguồn** (`source_id = null`) → **không** dựng dòng phí.

## Hiện trạng code (đã đọc, không đoán)

| Chỗ | File | Hành vi hiện tại |
|---|---|---|
| Model cấu hình | `domain/sapoinvoice/SapoInvoiceSetting.java:88` `ShippingFeeSetting` | JSON 1 row key `shipping_fee_setting`: `{mode, item_name, auto_adjust}` |
| Validate/normalize | `service/publisher/sapoinvoice/SapoInvoiceSettingUtil.java` | `normalizeShippingFeeSettings` (trim `item_name`), `validateShippingFeeSettings` (~93, validate trên **setting hợp nhất**), `normalizeParsed` (~214), `defaultShippingFeeSetting` (~152) |
| Lưu setting | `SapoInvoiceService.java` ~2225–2254 | normalize → validate hợp nhất → marshal lại |
| Đọc cấu hình khi dựng | `SapoInvoiceService.java:2288` `getShippingFeeSettings` → DTO `ShippingFeeSettings` (~2305) | Lỗi đọc → fallback `none` |
| **Gate dựng dòng phí** | `service/impl/EInvoiceServiceImpl.java` ~2650–2667 trong `setOrderData` (khai báo ~2438) | provider = SI **và** `isSeparateLine()` → `buildShippingFeeLineItem` (null nếu không có `delivery_fee` / fee âm) |
| Luồng đi qua gate | `createDraftInvoice` (~1436, gọi `setOrderData` ~1503) ← `createDraft` (controller `create_draft` **và** Kafka `OrderConsumer:77` Auto Invoice); `createDraftPreview` (~1971/1994) | Một chỗ sửa → phủ cả thủ công + Auto Invoice + preview |
| HĐ điều chỉnh | `EInvoiceServiceImpl.java` ~1689 | Dựa marker `shipping_line` của HĐ gốc — **không sửa** (HĐ gốc không có dòng phí → HĐĐC tự không có) |
| Tiền lệ lọc theo nguồn | `EInvoiceServiceImpl.java:1390` `isAutoHiddenReductionRate(long sourceId, …)` | `source.contains(String.valueOf(sourceId))`. ⚠️ Tham số `long` → caller unbox `orderResponse.getSourceId()` (Long) **ngoài try** → NPE nếu null. **Không copy mẫu này** |
| Source của order | `model/order/OrderResponse.java:46` `Long sourceId` | có thể null |
| FE màn cấu hình | `sapo-frontend-v3/src/page/Settings/Einvoices/Einvoice.tsx` | `parseShippingFeeSetting`/`stringifyShippingFeeSetting` (~87–112), validate FE (~461–473), `activeOrderSources` (~120, lọc `status === "active" \|\| "default"` ~227), dropdown nguồn mẫu cho "ẩn CK theo nguồn" (`DropdownSearch multiple`, ~1405–1440) |

## V3 đã làm thế nào (tham chiếu — `invoice-app` commit `e90cc984`)

- JSON `shipping_fee_setting` thêm `order_source_names: string[] | null` (alias). `null` = chưa từng lưu → áp mọi nguồn.
- BE `StoreSettingService`: trim, bỏ rỗng, distinct; `separate_line` + list rỗng → 422 field `shipping_fee_setting.order_source_names`, message **"Nguồn đơn không được để trống"**.
- `ShippingFeeLineAppender`: check nguồn **sau** check mode, **trước** check shipping lines; không khớp → `log.debug(... reason=source_not_matched)`. `matchesOrderSource`: list null → true; source blank → false; else equalsIgnoreCase.
- FE: `OrderConditionMultiSelect` (label "Nguồn đơn", placeholder "Chọn nguồn đơn", `requiredIndicator`, `selectAll`) đặt **cạnh** "Tên dòng phí" (`InlineGrid columns={2}`). `null` → hiển thị tích hết; **khi submit đổi `null` → danh sách toàn bộ nguồn** (`resolveOrderSourceNamesForSubmit`).
- ⚠️ Gap V3: selected chỉ lấy option còn trong list → nguồn ngừng áp dụng bị rơi khỏi cấu hình khi lưu lại (BR5). **V2 phải xử lý** (xem FE-4).

## UI theo Figma (đã đối chiếu 2026-09-30)

- Figma: [SAPO-INVOICE-V2 — section "Thiết lập hiển thị phí giao hàng"](https://www.figma.com/design/eB5jx4MxReLJuyrlptKhs2/SAPO-INVOICE-V2?node-id=979-50171) (`979:50171`)

| Frame (node) | Trạng thái | Nội dung |
|---|---|---|
| `979:50173`, `979:50924` | Mode **Không hiển thị phí giao hàng** | Chỉ có 2 radio + mô tả; **không** có Tên dòng phí / Nguồn đơn / checkbox / Lưu ý |
| `979:51676` | `separate_line`, đã điền | Tên dòng phí = "Phí giao hàng"; Nguồn đơn: ô hiển thị **"Đã chọn 1 giá trị"**, bên dưới là **chip** `Shoppee ✕`; checkbox Tự động điều chỉnh bỏ tích |
| `979:52519` | `separate_line`, tên trống | Placeholder "Nhập tên dòng phí trên hóa đơn"; Nguồn đơn "Đã chọn 1 giá trị" + chip; checkbox **đã tích** |
| `979:53321` | `separate_line`, **lỗi validate** | Tên dòng phí viền đỏ + `Vui lòng nhập tên dòng phí trên hóa đơn.`; Nguồn đơn viền đỏ, placeholder **"Chọn giá trị"**, lỗi `Nguồn đơn không được để trống` |
| `979:53317` | Tooltip icon ⓘ | `Tên này hiển thị làm tên hàng hóa/dịch vụ của dòng phí trên hóa đơn.` |

**Bố cục (khác V3):** trong khối lùi lề của radio "Hiển thị 1 dòng phí giao hàng", các trường **xếp dọc, full width**: Tên dòng phí → **Nguồn đơn** (mới) → chip đã chọn → checkbox "Tự động điều chỉnh phí giao hàng" → khối "Lưu ý:" (2 bullet). V3 đặt Nguồn đơn **cạnh** Tên dòng phí (2 cột) — V2 **không** làm vậy.

**Chuỗi UI trường Nguồn đơn (nguyên văn Figma):**
- Nhãn: `Nguồn đơn` + dấu `*` đỏ
- Placeholder khi trống: `Chọn giá trị` ⚠️ (khác trường Nguồn đơn của "ẩn chiết khấu"/"người mua không lấy HĐ" đang dùng `Chọn nguồn đơn`, và khác V3) — **làm theo Figma**
- Khi có chọn: ô hiển thị `Đã chọn {n} giá trị`; các nguồn đã chọn hiện thành chip có nút ✕ ngay dưới ô
- Lỗi: `Nguồn đơn không được để trống` (trùng message BE)

**Component:** dùng lại `DropdownSearch` `multiple` của `@sapo-presentation/sapo-ui-components` như trường "Không hiện chiết khấu trên hóa đơn theo nguồn đơn" (`Einvoice.tsx` ~1405). Popup của component đã có sẵn hàng checkbox **chọn tất cả** (value `"all"`, có trạng thái indeterminate) → dùng làm "Tất cả nguồn đơn", không cần tự thêm option. Cần kiểm tra khi code: chế độ hiển thị "Đã chọn N giá trị" + chip dưới ô là hành vi mặc định của component hay phải tự render chip (Figma không có frame mở dropdown).

**Các phần khác trong Figma đã khớp code hiện tại** (không cần sửa): tiêu đề "Thiết lập hiển thị phí giao hàng", 2 radio + mô tả, tooltip, placeholder tên dòng phí, checkbox + mô tả, khối Lưu ý 2 bullet (`Einvoice.tsx` ~1500–1575).

**Figma chưa có (cần designer/PO bổ sung — không chặn code, làm tạm theo đề xuất):**
1. Trạng thái **mở dropdown** (danh sách nguồn + hàng chọn tất cả).
2. Hiển thị **nguồn đã chọn nhưng ngừng áp dụng / bị xóa** (BR5) — đề xuất tạm: chip vẫn hiện, kèm hậu tố ` (Ngừng áp dụng)` màu xám.
3. Khi chọn nhiều nguồn: chip có xuống dòng không / có giới hạn hiển thị (+N) không — tạm: wrap nhiều dòng, không giới hạn.

## Thiết kế V2

```json
{ "mode": "separate_line", "item_name": "Phí giao hàng", "auto_adjust": false,
  "order_source_ids": ["12", "34", "56"] }
```

| Giá trị `order_source_ids` | Ý nghĩa | Order có `source_id` | Order `source_id = null` |
|---|---|---|---|
| `null` / thiếu field | Store chưa từng lưu (legacy, sau deploy) | dựng | dựng |
| `["12","34"]` | Đã chọn (kể cả khi user chọn "Tất cả" → FE gửi đủ id) | dựng nếu thuộc list | **không** dựng |
| `[]` | Không hợp lệ khi `separate_line` → chặn lưu | — | — |

- Không migration DB (thêm field vào JSON có sẵn). Không backfill (BR6).
- Không lọc theo `status` khi so khớp → nguồn ngừng áp dụng/bị xóa vẫn khớp đơn cũ (BR5).
- Reset khi gỡ kết nối SI (BR11) → default mới có `order_source_ids = null`.

## Việc cần làm

### BE — `sapo-einvoice-service`
- **BE-1** `ShippingFeeSetting`: thêm `@JsonProperty("order_source_ids") private List<String> orderSourceIds;` — mặc định `null`; `normalizeParsed` **không** gán list rỗng.
- **BE-2** `normalizeShippingFeeSettings`: nếu `orderSourceIds != null` → trim, bỏ blank, distinct (giữ thứ tự).
- **BE-3** `validateShippingFeeSettings`: `separate_line` + `orderSourceIds != null && isEmpty()` → `SapoInvoiceExeption("setting", "Nguồn đơn không được để trống")`.
- **BE-4** `ShippingFeeSettings` (DTO trong `SapoInvoiceService`): thêm field `List<String> orderSourceIds` + method `appliesToOrderSource(Long sourceId)`; map từ `fee.getOrderSourceIds()` ở `getShippingFeeSettings` (cả 2 nhánh fallback → `null`).
- **BE-5** Gate trong `setOrderData`: `if (shippingFeeSettings.isSeparateLine() && shippingFeeSettings.appliesToOrderSource(orderResponse.getSourceId()))`; không khớp → `log.debug("Skip shipping fee line tenantId={} orderId={} sourceId={} reason=source_not_matched", …)`.
- **BE-6** Unit test (xem [[epic-102-test-cases]] nhóm U).

### FE — `sapo-frontend-v3` (Figma đã có — xem mục "UI theo Figma")
- **FE-1** `parseShippingFeeSetting` / `stringifyShippingFeeSetting`: thêm `order_source_ids: string[] | null` (parse: không phải array → `null`; lọc phần tử string). Dirty-check so được `null` vs list.
- **FE-2** Trường "Nguồn đơn" (bắt buộc `*`, placeholder **"Chọn giá trị"**) **dưới** "Tên dòng phí", full width, trên checkbox "Tự động điều chỉnh"; **chỉ hiện khi `separate_line`**. `DropdownSearch multiple` trên `activeOrderSources` (dùng hàng "chọn tất cả" có sẵn của component); ô hiển thị "Đã chọn N giá trị" + chip ✕ dưới ô.
- **FE-3** `null` → hiển thị tích hết; khi lưu ở `separate_line` đổi `null` → id toàn bộ `activeOrderSources`. Lưu ở `none` → giữ nguyên giá trị (không ép).
- **FE-4** (BR5, V3 thiếu, Figma chưa vẽ) Giữ id đã lưu nhưng không còn trong `activeOrderSources`: chip vẫn hiện, hậu tố tạm " (Ngừng áp dụng)" màu xám; bỏ chọn tay (✕) mới xóa.
- **FE-5** Validate FE: `separate_line` + list rỗng → viền đỏ + lỗi "Nguồn đơn không được để trống" dưới trường (Figma `979:53321`), hiện **cùng lúc** với lỗi tên dòng phí nếu cả hai trống; map lỗi BE cùng message.

### Docs
- Nhắc PO/BA (`dungntt6`) sửa SRS BR3/BR4 theo D1; trả lời `[TODO: Dev BE]` (tên key JSON = `order_source_ids`, IDOR scope theo session).
- Báo đội V3 (`trongns`) gap BR5 ở FE V3.

## Rủi ro

- **NPE `sourceId` null** nếu copy mẫu `isAutoHiddenReductionRate` → dùng `Long`, check null tường minh.
- **FE rơi nguồn inactive** khi lưu lại → FE-4.
- **Partial update**: API settings cho phép gửi từng phần; nếu FE gửi `shipping_fee_setting` thiếu `order_source_ids` → ghi đè thành `null` (= áp mọi nguồn). FE hiện luôn gửi cả object — giữ nguyên thói quen này.
- **Deploy**: không có DB change → deploy BE trước FE hay đồng thời đều an toàn (BE đọc JSON cũ = `null` = hành vi cũ).

## Cần xác nhận

1. Designer/PO bổ sung Figma: trạng thái mở dropdown, chip nguồn ngừng áp dụng (BR5), nhiều chip (xem mục "Figma chưa có").
2. PO/BA cập nhật SRS BR3/BR4 theo quyết định D1.
3. Xác nhận placeholder `Chọn giá trị` (Figma) là chủ ý, dù các trường Nguồn đơn khác trên cùng màn dùng `Chọn nguồn đơn`.
