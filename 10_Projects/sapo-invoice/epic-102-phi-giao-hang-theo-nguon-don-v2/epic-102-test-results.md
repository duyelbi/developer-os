---
created: 2026-10-02 08:30
status: Staging — cấu hình (C/F) + dựng dòng phí (D1, D3) pass; còn C8/C9/F7, E, R, Auto Invoice riêng chưa chạy
project: "[[10_Projects/sapo-invoice/README]]"
---

# Epic #102 — Kết quả test (unit + staging)

- Plan: [[epic-102-plan]] · Test case: [[epic-102-test-cases]] · Prompt: [[epic-102-cursor-prompt-implement]] · Fix review: [[epic-102-cursor-prompt-fix-review]]
- Epic [#102](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/102) · issue `sapo-invoice-admin-service#175`
- BE `sapo-einvoice-service`: commit `e9464ef9`, draft MR [!670](https://git.dktsoft.com:2008/sapo-core/sapo-microservices/sapo-einvoice-service/-/merge_requests/670) → master, MR [!671](https://git.dktsoft.com:2008/sapo-core/sapo-microservices/sapo-einvoice-service/-/merge_requests/671) → staging (merged 2026-10-01 15:32, pipeline #1128369 `16628b2628`)
- FE `sapo-frontend-v3`: commit `4acab4f43f`, draft MR [!12470](https://git.dktsoft.com:2008/sapo-presentation/sapo-frontend-v3/-/merge_requests/12470) → master; lên `staging` bằng merge local (merge commit `d3d3036ab7`, resolve `src/services/EinvoiceService/type.ts` — chỉ lệch vị trí field), pipeline #1128365
- Môi trường: staging, store `phuongtestmposlogin-sapostaging.mysapogo.com` (tenant `10014697`), tài khoản Ngô Văn Công, Chrome (Claude in Chrome). Test 2026-10-01 → 2026-10-02.
- Nguồn đơn trên store: 19 nguồn `active`/`default` (vd `146057` Pos, `198152` "them nguồn b2" — default), vài nguồn `deleted` (vd `195696`).

## Unit test (BE) — 51/51 pass (JDK 11)

| Class | Case |
| --- | :-: |
| `SapoInvoiceSettingUtilTest` (parse JSON cũ, normalize, validate rỗng/null/none) | 15 |
| `ShippingFeeSettingsTest` (`appliesToOrderSource`) | 2 |
| `SapoInvoiceServiceShippingFeeResetTest` (reset BR11 → `null`) | 3 |
| `ShippingFeeLineHelperTest`, `EInvoiceItemTypeTotalsTest` (hồi quy) | 31 |

> ⚠️ `mvn` mặc định trên máy là JDK 26 → Lombok không sinh getter, compile lỗi ở `EInvoice.java`. Chạy với `JAVA_HOME=/Library/Java/JavaVirtualMachines/openjdk-11.jdk/Contents/Home`.

FE: `eslint` 0 error (warning có sẵn + 1 `exhaustive-deps` cố ý ở effect lấy tên nguồn inactive); `tsc --skipLibCheck` không lỗi ở file thay đổi (repo có lỗi sẵn ở file khác).

## Staging — đã chạy

### Cấu hình (UI + API)

| Case | Kết quả | Ghi chú |
| --- | :-: | --- |
| C12 — store cũ `separate_line` chưa có `order_source_ids` | ✅ | Hiện `Đã chọn 19 giá trị` + 19 chip; nút Lưu disable (không dirty) |
| F4 — hàng "Chọn tất cả" trong dropdown | ✅ | Có sẵn, tích sẵn; bỏ tích → placeholder `Chọn giá trị`, chip mất |
| F5 / C4 (FE) — bỏ trống tên dòng phí + nguồn đơn → Lưu | ✅ | 2 lỗi cùng lúc: `Vui lòng nhập tên dòng phí trên hóa đơn.` + `Nguồn đơn không được để trống`, viền đỏ; **không** gửi request lưu. Toast chung có sẵn "Cập nhật cấu hình thất bại…" |
| C4 (BE) — POST API với `[]` và `[" ",""]` | ✅ | Cả 2 → 422 `{"setting":"Nguồn đơn không được để trống"}`; giá trị lưu không đổi |
| F8 — tìm "pos" | ✅ | Lọc ra đúng "Pos" |
| F2 / C5 — chọn riêng Pos → Lưu | ✅ | `Đã chọn 1 giá trị` + chip `Pos ✕`; "Cập nhật thành công"; DB `"order_source_ids":["146057"]`, `auto_adjust` giữ nguyên |

### Dựng dòng phí khi tạo HĐ từ đơn

Dữ liệu: mọi đơn có phí trên store đều thuộc nguồn `198152`; đơn finalized có phí đều đã có HĐ (tạo trước deploy). Dùng 2 đơn nháp `SON04069` (`464114`), `SON04067` (`464112`) — nguồn `198152`, 1 dòng SP thuế 10%, phí giao hàng `fee=1000` ("Giao hàng tiêu chuẩn"), tổng đơn 101.000. Đặt cấu hình **trước** khi duyệt đơn (store có Auto Invoice).

| Case | Cấu hình | Đơn | HĐ nháp | Kết quả |
| --- | --- | --- | --- | :-: |
| D3 — nguồn không khớp | `["146057"]` | `SON04069` | `EIN08987` (id 14421): chỉ dòng `sp 10% thue`; **không** có dòng phí; `total_amount = 100.000` | ✅ |
| D1 — nguồn khớp | `["198152","146057"]` | `SON04067` | `EIN08988` (id 14422): dòng 2 `Phí giao hàng` — `item_type=1`, `unit_name=""`, qty 1, giá 1.000, `KCT`, CK 0, `shipping_line=true`, cuối danh sách; `total_amount = 101.000` | ✅ |

- `SON04069`: sau ~45s Auto Invoice **không** tự tạo HĐ → tạo bằng `POST /admin/einvoices/create_draft.json?order_id=…`.
- `SON04067`: HĐ xuất hiện lúc 08:20:15 (giờ VN), ~23s sau khi duyệt, đúng lúc lệnh `create_draft` bị lỗi mạng ("Failed to fetch") → **không xác định được** HĐ do Auto Invoice hay `create_draft` tạo. Logic dòng phí vẫn được kiểm vì cả 2 đường cùng qua `setOrderData`.

### Thay đổi đã để lại trên staging

- Đơn `SON04069`, `SON04067`: `draft` → `finalized`.
- 2 HĐ **nháp** (chưa phát hành) `EIN08987`, `EIN08988`.
- Cấu hình phí giao hàng đã trả về: `{"mode":"separate_line","item_name":"Phí giao hàng","auto_adjust":true,"order_source_ids":null}` (gốc không có key `order_source_ids`; `null` tường minh = cùng nghĩa "chưa từng lưu").

## Chưa chạy

| Case | Lý do / cách chạy |
| --- | --- |
| C8 / C9 / F7 — chip nguồn ngừng áp dụng / đã xóa | Có thể lưu tạm qua API id nguồn đã xóa `195696` ("thêm nguồn bán hàng") → mở UI kiểm chip `thêm nguồn bán hàng (Ngừng áp dụng)` → lưu lại xem id còn giữ → trả cấu hình |
| D4 / D5 — đơn không có nguồn | Store không có đơn phí giao hàng mà `source_id = null` |
| D7 — nguồn tạo mới sau khi lưu "Tất cả" | Cần tạo nguồn bán hàng mới + đơn từ nguồn đó |
| D12 / D13 — mẫu 2, STP số lẻ | Chưa chạy riêng (store đang bật STP — D1 chạy với STP bật, tổng khớp) |
| D14 / D15 — Auto Invoice tách riêng | Cần store có cấu hình tự động chắc chắn áp cho nguồn của đơn |
| E1–E6 — thời điểm áp dụng, HĐĐC, đổi provider, gỡ kết nối | Chưa chạy |
| R1–R3 — regression | R1 gián tiếp pass (C12: store cũ hiển thị + lưu bình thường); R2/R3 chưa chạy |
