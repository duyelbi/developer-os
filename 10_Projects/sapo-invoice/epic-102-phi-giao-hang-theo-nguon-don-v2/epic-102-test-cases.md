---
created: 2026-09-30 10:00
status: Draft — dựng trước khi Cursor implement, chưa chạy trên code thật
project: "[[10_Projects/sapo-invoice/README]]"
---

# Test case Epic #102 — Phí giao hàng theo nguồn đơn (V2)

- Plan: [[epic-102-plan]] · Prompt Cursor: [[epic-102-cursor-prompt-implement]] · Epic gốc: [[epic-61-test-cases]]
- Expected theo **quyết định D1/D2** trong plan (giống V3: "Tất cả" = danh sách đầy đủ; lưu id) — **lệch SRS v0.9 BR3/BR4**, các case bị ảnh hưởng đánh dấu ⚠️D1.
- Precondition chung trừ khi ghi khác: provider = Sapo Invoice, order có `delivery_fee` (fee ≥ 0).
- Ký hiệu nguồn: `POS=12`, `WEB=34`, `SHOPEE=56` (id minh họa — lấy id thật từ `GET /order_sources.json` của store test).

---

## Nhóm C — Cấu hình (UC-01b)

| # | Precondition | Bước | Kỳ vọng | Ref |
|---|---|---|---|---|
| C1 | Store chưa từng cấu hình phí VC | Mở Cài đặt tự động SI | `none`; trường Nguồn đơn **ẩn** | BR1 |
| C2 | — | Chọn `separate_line` | Trường "Nguồn đơn" (bắt buộc `*`) hiện **dưới** "Tên dòng phí", trên checkbox "Tự động điều chỉnh"; **tích sẵn toàn bộ** nguồn đang áp dụng → ô hiển thị `Đã chọn {n} giá trị` + chip từng nguồn | BR1, BR3, Figma `979:51676` |
| C3 | C2 | Lưu → GET settings | `order_source_ids` = id **toàn bộ** nguồn `status active/default` (không phải `null`) | D1 |
| C4 | `separate_line` | Bỏ chọn hết → Lưu | Chặn lưu; ô viền đỏ, placeholder `Chọn giá trị`, lỗi **`Nguồn đơn không được để trống`** (FE); gọi thẳng API với `[]` hoặc `[" ",""]` → BE cũng chặn cùng message | BR1, Figma `979:53321` |
| C5 | `separate_line` | Chọn POS, WEB → Lưu → reload | Hiện đúng POS, WEB; JSON `["12","34"]` | BR1, D2 |
| C6 | — | Gọi API với `[" 12 ","34","","12"]` | Lưu thành `["12","34"]` (trim, bỏ rỗng, bỏ trùng) | BE-2 |
| C7 | Đang `separate_line` + POS | Đổi sang `none` → Lưu | Trường ẩn; lưu OK dù không validate nguồn | BR1 |
| C8 | C5 đã lưu; chuyển nguồn WEB sang **ngừng áp dụng** trong Sapo | Mở lại màn cấu hình | WEB vẫn hiển thị (kèm chú thích ngừng áp dụng); không bị tự gỡ | BR5 |
| C9 | C8 | Sửa tên dòng phí → Lưu → GET | `order_source_ids` **vẫn chứa** `"34"` | BR5 (gap V3) |
| C10 | Store dùng provider khác SI | Mở cài đặt | Không có cấu hình phí VC / nguồn đơn | BR09 SRS |
| C11 | Store A | Gọi API settings với tenant/store của B | 404, không đọc/ghi được B | BR7 |
| C12 | Store có setting cũ `{"mode":"separate_line","item_name":"Phí giao hàng","auto_adjust":false}` (chưa có field) | Mở màn cấu hình | Hiển thị tích hết nguồn; chưa lưu thì DB vẫn không có field | D1 legacy |

## Nhóm F — UI đối chiếu Figma (`979:50171`)

| # | Bước | Kỳ vọng | Frame |
|---|---|---|---|
| F1 | Mode `none` | Chỉ 2 radio + mô tả; không có Tên dòng phí, Nguồn đơn, checkbox, khối Lưu ý | `979:50924` |
| F2 | Chọn 1 nguồn (Shopee) | Ô: `Đã chọn 1 giá trị`; dưới ô chip `Shopee ✕` | `979:51676` |
| F3 | Bấm ✕ trên chip | Nguồn bị bỏ khỏi danh sách, số đếm giảm; bỏ chip cuối → ô về placeholder `Chọn giá trị` | `979:53321` |
| F4 | Mở dropdown → tích hàng "chọn tất cả" | Tích hết nguồn đang áp dụng; bỏ tích → rỗng | (Figma chưa vẽ) |
| F5 | Xóa trắng tên dòng phí **và** bỏ hết nguồn → Lưu | Hiện **cùng lúc** 2 lỗi: `Vui lòng nhập tên dòng phí trên hóa đơn.` và `Nguồn đơn không được để trống` | `979:53321` |
| F6 | Hover icon ⓘ cạnh "Tên dòng phí trên hóa đơn" | Tooltip `Tên này hiển thị làm tên hàng hóa/dịch vụ của dòng phí trên hóa đơn.` | `979:53317` |
| F7 | Nguồn đã chọn chuyển ngừng áp dụng (C8) | Chip vẫn hiện, hậu tố ` (Ngừng áp dụng)` màu xám; số đếm tính cả nguồn này | (Figma chưa vẽ — tạm) |
| F8 | Tìm kiếm trong dropdown gõ không dấu ("shop") | Lọc ra Shopee | — |

## Nhóm D — Dựng dòng phí khi tạo HĐ từ order (UC-02b)

| # | Cấu hình `order_source_ids` | Order | Kỳ vọng | Ref |
|---|---|---|---|---|
| D1 | `["12","34"]` | POS, fee 30.000 | Có 1 dòng phí `shipping_line=true`, `amount=30000`, KCT, CK 0; tổng HĐ khớp chi tiết | BR2, BR8 |
| D2 | `["12","34"]` | SHOPEE, fee 0 | **Không** có dòng phí; line items + tổng giống `none` | BR2 (mục tiêu epic) |
| D3 | `["12","34"]` | SHOPEE, fee 25.000 | Không có dòng phí | BR2 |
| D4 | `["12"]` | `source_id = null`, fee 30.000 | Không có dòng phí | ⚠️D1 / BR4 |
| D5 | `null` (legacy) | `source_id = null`, fee 30.000 | **Có** dòng phí (giữ hành vi cũ) | D1 legacy |
| D6 | `null` (legacy) | SHOPEE, fee 0 | **Có** dòng phí 0đ (giữ hành vi cũ BR07 SRS) | D1 legacy |
| D7 | Lưu "Tất cả" (= đủ id lúc lưu), **sau đó** tạo nguồn mới `TIKTOK=78` | Order TIKTOK fee 20.000 | **Không** có dòng phí cho tới khi tích thêm TIKTOK | ⚠️D1 / BR3 |
| D8 | `["34"]`, WEB đã ngừng áp dụng | Order WEB (cũ) fee 15.000 | Có dòng phí | BR5 |
| D9 | `["12"]`, mode `none` | POS fee 30.000 | Không có dòng phí | BR2 |
| D10 | `["12"]`, provider ≠ SI trên HĐ | POS fee 30.000 | Không có dòng phí | BR09 SRS |
| D11 | `["12"]` | POS **không có** `delivery_fee` | Không có dòng phí | BR01 SRS |
| D12 | `["12"]` | POS fee 30.000, **mẫu 2** (HĐ bán hàng) | Có dòng phí, tổng đúng | Phạm vi B |
| D13 | `["12"]`, **bật cấu hình STP** (số thập phân) | POS fee 30.000,5 | Dòng phí vào tổng RAW; 6 ô tổng = round(Σ RAW) | Regression SM-76 |
| D14 | `["12"]` | Order SHOPEE qua **Auto Invoice** (Kafka) | Không có dòng phí | Phạm vi B |
| D15 | `["12"]` | Order POS qua **Auto Invoice** | Có dòng phí, HĐ phát hành thành công | Phạm vi B |
| D16 | `["12"]` | `create_draft` thủ công từ order SHOPEE + preview | Preview và draft đều không có dòng phí | Phạm vi B |

## Nhóm E — Thời điểm áp dụng & hóa đơn liên quan

| # | Precondition | Bước | Kỳ vọng | Ref |
|---|---|---|---|---|
| E1 | `null`, đã tạo nháp X từ order SHOPEE (có dòng phí 0đ) | Đổi cấu hình `["12"]` → mở nháp X sửa/lưu | Nháp X **giữ** dòng phí cũ | BR6 |
| E2 | `["12"]` | Tạo HĐ từ SHOPEE (không dòng phí) → phát hành → trả hàng → HĐ điều chỉnh (auto_adjust = true) | HĐĐC **không** phát sinh dòng phí âm | BR8 |
| E3 | `["12"]` | HĐ từ POS có dòng phí → điều chỉnh, auto_adjust = true | Dòng phí ghi âm như epic 61 | BR8 (không hồi quy) |
| E4 | `["12"]`, HĐ POS có dòng phí | Đổi provider trên form sang MeInvoice | Dòng phí bị loại, tổng tính lại | BR10 |
| E5 | E4 | Đổi ngược provider về SI | **Không** dựng lại dòng phí | BR10 |
| E6 | Store `["12"]` | Gỡ hẳn kết nối SI → kết nối lại | Cấu hình phí về default (`none`, `order_source_ids = null`) | BR11 SRS |

## Nhóm U — Unit test BE (Cursor viết)

| # | Class test | Case |
|---|---|---|
| U1 | `SapoInvoiceSettingUtilTest` | Parse JSON cũ không có `order_source_ids` → `getOrderSourceIds() == null` |
| U2 | `SapoInvoiceSettingUtilTest` | `normalizeShippingFeeSettings` trim/bỏ rỗng/distinct: `[" 12 ","34","","12"]` → `["12","34"]` |
| U3 | `SapoInvoiceSettingUtilTest` | `separate_line` + `[]` → throw "Nguồn đơn không được để trống" |
| U4 | `SapoInvoiceSettingUtilTest` | `separate_line` + `null` → không throw (legacy) |
| U5 | `SapoInvoiceSettingUtilTest` | `none` + `[]` → không throw |
| U6 | test mới `ShippingFeeSettingsTest` (hoặc trong test có sẵn) | `appliesToOrderSource`: list null + sourceId null → true; list null + 56 → true; `["12"]` + 12 → true; `["12"]` + 56 → false; `["12"]` + null → false |
| U7 | `SapoInvoiceSettingUtilTest` | `defaultShippingFeeSetting().getOrderSourceIds() == null` |
| U8 | `SapoInvoiceServiceShippingFeeResetTest` | Reset (BR11) → JSON default không có list rỗng |

## Nhóm R — Regression

| # | Kịch bản | Kỳ vọng |
|---|---|---|
| R1 | Store prod có `separate_line` từ epic 61, chưa đụng cấu hình sau deploy | Mọi đơn (mọi nguồn, kể cả không nguồn) vẫn có dòng phí như trước |
| R2 | Các cài đặt tự động khác (ẩn CK theo nguồn, KH vãng lai theo nguồn, STP) lưu cùng lúc | Không mất/không đổi giá trị |
| R3 | Provider MeInvoice/SInvoice/VnInvoice | Không đổi hành vi |
