---
created: 2026-09-08 08:35
status: Draft — dựng trước khi code chạy, chưa verify trên môi trường thật
project: "[[10_Projects/sapo-invoice/README]]"
---

# Test case Epic #87 — Popup xác nhận trách nhiệm HĐ điều chỉnh MTT

- Epic: [#87](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/87) · Plan: [[epic-87-plan]]
- Repo: `sapo-invoice-admin-frontend` · màn `/admin/adjusted-invoices`
- Dựng **trước khi code chạy**, theo BR1–BR6 + DoD epic. Số dòng là tham chiếu code hiện tại.

Precondition chung trừ khi ghi khác: user đủ quyền `CREATE_INVOICES` + `ADJUSTMENT_INVOICES`; có ít nhất 1 HĐ MTT và 1 HĐ không MTT đủ điều kiện điều chỉnh (status INITIALIZED/MODIFIED, đã cấp mã/chấp nhận).

Nhận diện MTT: `invoice_series.charAt(4) === "M"` — ví dụ MTT `1C26MLO` / `1C26MAA`; không MTT `1C26TAL` / `2C26TQL`.

---

## Nhóm 1 — Gate trên popup Chọn hóa đơn điều chỉnh (BR1, BR3, BR4)

| # | Precondition | Bước | Kỳ vọng | Ref |
|---|---|---|---|---|
| G1 | Chọn HĐ MTT (ký hiệu `…M…` ở `charAt(4)`) | Bấm **Lập hóa đơn** | Hiện popup tiêu đề **Lưu ý khi điều chỉnh hóa đơn từ máy tính tiền**; popup chọn HĐ **không** đóng | BR1, DoD |
| G2 | Chọn HĐ không MTT (`1C26TAL`, `2C26TQL`, …) | Bấm **Lập hóa đơn** | **Không** hiện popup mới; vào màn lập HĐ điều chỉnh như cũ | BR1, DoD |
| G3 | G1 đang mở, checkbox **chưa** tick | Quan sát nút **Tiếp tục lập hóa đơn** | DISABLED | BR3 |
| G4 | G1, tick **Tôi xác nhận và chịu hoàn toàn trách nhiệm về quyết định này.** | Quan sát nút Tiếp tục | ENABLED | BR3 |
| G5 | G4 | Bấm **Tiếp tục lập hóa đơn** | Vào `/admin/adjusted-invoices/create/:id` của HĐ vừa chọn; popup confirm đóng | DoD |
| G6 | G1 | Bấm **Hủy bỏ** (hoặc đóng popup confirm) | Không tạo HĐ; quay lại popup chọn HĐ; HĐ MTT **vẫn được chọn** | BR4 |
| G7 | Chưa chọn HĐ nào | Nút **Lập hóa đơn** trên popup chọn | Vẫn DISABLED như hiện tại — không lọt confirm | Regression |
| G8 | Đổi chọn từ MTT → không MTT rồi bấm Lập hóa đơn | — | Không hiện confirm (theo HĐ **đang** chọn, không nhớ lần chọn trước) | BR1 |
| G9 | Đổi chọn từ không MTT → MTT rồi bấm Lập hóa đơn | — | Hiện confirm | BR1 |
| G10 | Mobile (`mdDown`, `AdjustInvoiceList`) | Lặp G1–G6 | Cùng hành vi — chung `primaryAction` | Modal |

---

## Nhóm 2 — Copy, textlink, checkbox (BR2)

| # | Bước | Kỳ vọng | Ref |
|---|---|---|---|
| C1 | Mở popup confirm | Tiêu đề đúng: `Lưu ý khi điều chỉnh hóa đơn từ máy tính tiền` (có cảnh báo ⚠️ nếu design dùng) | BR2 |
| C2 | Đọc đoạn nội dung | Có **cả hai** nhánh Điều 10: lập sai MTT → **hóa đơn thay thế**; trả hàng (kể cả đổi hàng đổi giá trị) → **hóa đơn điều chỉnh** (trừ thỏa thuận người mua lập HĐ) | BR2, điểm c + c.1 |
| C3 | Đọc dòng Lưu ý | Có dòng: trường hợp khác tham khảo Điều 10 TT 91/2026 hoặc liên hệ CQT | BR2 |
| C4 | Click cụm **Điều 10 Thông tư 91/2026/TT-BTC** | Mở **tab mới**, URL `https://vanban.chinhphu.vn/?pageid=27160&docid=219006&classid=1&orggroupid=4` | BR2 |
| C5 | Checkbox | Label đúng nguyên văn: `Tôi xác nhận và chịu hoàn toàn trách nhiệm về quyết định này.` Bắt buộc tick mới tiếp tục | BR2, BR3 |
| C6 | Tick rồi Hủy bỏ → mở lại confirm (chọn MTT, Lập hóa đơn lại) | Checkbox **reset** về chưa tick; Tiếp tục lại DISABLED | UX suy ra từ BR3 — verify với implement |

---

## Nhóm 3 — Không hồi quy / out of scope (BR6)

| # | Precondition | Bước | Kỳ vọng | Ref |
|---|---|---|---|---|
| O1 | HĐ không MTT | Đi hết luồng chọn → lập → lưu nháp | Không popup mới; form lập không đổi | DoD |
| O2 | HĐ MTT, đã confirm | Màn lập `AdjustedInvoiceCreatePage` | Banner **Lưu ý** cũ **vẫn** hiện bullet MTT (điểm c khoản 1 — lập thay thế). Không thay bằng popup | BR6 |
| O3 | Nhập khẩu file, chọn loại hóa đơn điều chỉnh | Mở `InvoiceImportModal` | Banner Lưu ý cũ vẫn hiện; **không** có popup xác nhận trách nhiệm mới | BR6, DoD |
| O4 | List HĐĐC → **Lập biên bản điện tử** (`isStatement`) | Chọn HĐ MTT → **Tạo biên bản** | **Không** hiện popup MTT; vào luồng biên bản như cũ | Phạm vi |
| O5 | **Điều chỉnh HĐ trên hệ thống khác** (`/other/create`) | Mở form | Không popup MTT | Phạm vi |
| O6 | Bảng list HĐĐC, dòng draft (chưa có số HĐ) bấm **Lập hóa đơn** | — | Không hiện popup #87 (đây không phải popup chọn HĐ gốc) | Phạm vi |
| O7 | Có mã / Không mã trên popup chọn | Chọn HĐ MTT ở cả 2 tab | Confirm vẫn hiện đúng (ký hiệu `M`, không phụ thuộc tab) | BR1 |

---

## Nhóm 4 — Biên nhận diện series

| # | `invoice_series` | Kỳ vọng khi bấm Lập hóa đơn | Ref |
|---|---|---|---|
| S1 | `1C26MLO`, `1C26MAA`, `1C26MDM` | Hiện confirm | Epic §4 |
| S2 | `1C26TAL`, `2C26TQL` | Không hiện | Epic §4 |
| S3 | Series ngắn hơn 5 ký tự / rỗng | Không hiện confirm (không crash) | Fail-open, không block nhầm |
| S4 | `charAt(3) === "M"` nhưng `charAt(4) !== "M"` (nếu có data lệch) | **Không** hiện — rule là `charAt(4)` như code SI, không đếm "ký tự thứ 4" 1-based | [[epic-87-plan]] |

---

## Không test (ngoài epic)

- BE từ chối tạo HĐ điều chỉnh MTT khi chưa confirm (không có API)
- Sửa copy banner Lưu ý cũ cho khớp đoạn dài của popup mới
- Invoice-app (merchant embed) — epic này là SI admin
