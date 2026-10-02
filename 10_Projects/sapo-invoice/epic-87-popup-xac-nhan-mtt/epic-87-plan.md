---
created: 2026-09-08 08:35
status: Sẵn sàng implement — 1 child issue FE
project: "[[10_Projects/sapo-invoice/README]]"
---

# Epic #87 — Popup xác nhận trách nhiệm khi lập HĐ điều chỉnh cho HĐ MTT

- GitLab epic: [#87](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/87) (group `sapo-money/sapo-invoice`, author `dungntt6`, labels `T::Newfeature` · `module::hoa-don-dau-ra` · `workflow::ready` · `tier::3` · `HTF::Uplive`)
- Repo: **`sapo-invoice-admin-frontend`** (SI admin). Không đụng `invoice-app`, admin-service, V2/V3 Omni.
- Test case: [[epic-87-test-cases]]

## Tóm tắt

SI đã có banner **Lưu ý** (chỉ thông báo, không chặn) khi lập HĐ điều chỉnh cho hóa đơn máy tính tiền (MTT). Epic thêm **1 popup xác nhận trách nhiệm** (checkbox bắt buộc) ngay lúc bấm **Lập hóa đơn** trên popup **Chọn hóa đơn điều chỉnh**, nếu HĐ gốc là MTT. Không cấm cứng điều chỉnh MTT — case trả hàng vẫn hợp lệ theo điểm c.1 khoản 5 Điều 10 TT 91/2026.

## Hiện trạng code (đã đọc, không đoán)

| Chỗ | File | Hành vi hiện tại |
| --- | --- | --- |
| Popup chọn HĐ | `src/pages/adjusted-invoices/component/AdjustInvoiceModal/AdjustInvoiceModal.tsx` | Primary **"Lập hóa đơn"** dùng `url` → navigate thẳng `/admin/adjusted-invoices/create/:id`. **Không có confirm.** |
| Mở popup | `AdjustedInvoiceListPage.tsx` (~363, 397) | Nút "Lập hóa đơn điều chỉnh" → `setOpenAdjustModal(true)` |
| Banner Lưu ý trên màn lập | `AdjustedInvoiceCreatePage.tsx` (~1371–1398) | Hiện **thêm** 1 bullet MTT khi `invoice_series.charAt(4) === "M"` — **giữ nguyên** (BR6) |
| Banner Lưu ý nhập file | `src/pages/invoice/components/modal/InvoiceImportModal.tsx` (~162–183) | Hiện khi `invoiceImportType === MODIFY` — **không thêm popup** (out of scope) |
| Nhận diện MTT | Nhiều chỗ SI | `invoice_series.charAt(4) === "M"` (ví dụ `1C26MLO`). Field `is_calculating_machine` có trên type nhưng **không dùng** cho epic này |

Luồng statement ("Tạo biên bản") dùng cùng modal với `isStatement=true` — **không** áp popup mới.

## Nhận diện MTT

Epic viết "ký tự thứ 4" + `substring(invoice_series, 4, 1)`. Ví dụ epic (`1C26MLO` vs `1C26TAL`) và **toàn bộ code SI hiện tại** dùng `charAt(4)` = ký tự thứ 5 theo đếm 1-based = `M`.

**Chốt implement:** `invoice_series.charAt(4) === "M"`, lấy `invoice_series` từ object HĐ trong response list API (đã lưu trên SI — BR5). Không tin field client tự gửi, không đọc `is_calculating_machine`.

Helper nhỏ (đặt cạnh feature, không refactor toàn repo):

```ts
export function isMttInvoiceSeries(series?: string): boolean {
  return series?.charAt(4) === "M";
}
```

## Phạm vi sửa

**In-scope**

1. Intercept nút **Lập hóa đơn** trên `AdjustInvoiceModal` (khi `!isStatement`).
2. Nếu HĐ đang chọn là MTT → mở popup xác nhận; chưa tick thì primary disabled.
3. Tick + **Tiếp tục lập hóa đơn** → đi `/admin/adjusted-invoices/create/:id` như cũ.
4. **Hủy bỏ** → đóng popup xác nhận, **giữ** popup chọn HĐ + selection, không navigate.

**Out-of-scope (epic chốt)**

- Luồng **Nhập khẩu file** (`InvoiceImportModal`)
- Banner Lưu ý cũ trên create / import — không sửa copy, không thay bằng popup
- Công thức đảo dấu / mapping HĐ điều chỉnh
- Cấm cứng điều chỉnh MTT
- BE mới / API mới / lưu "đã xác nhận" xuống DB
- `AdjustedInvoiceOtherCreatePage` (điều chỉnh HĐ hệ thống khác)
- Nút **Lập hóa đơn** trên bảng danh sách HĐĐC draft (`AdjustedInvoiceTable` ~142) — đó là tiếp tục draft đã chọn HĐ gốc rồi

## File đụng

| File | Việc |
| --- | --- |
| `src/pages/adjusted-invoices/utils.ts` (mới, hoặc `constants.ts` nếu muốn gộp) | `isMttInvoiceSeries` |
| `src/pages/adjusted-invoices/component/AdjustInvoiceModal/AdjustInvoiceModal.tsx` | Đổi `primaryAction.url` → `onAction`; tìm HĐ theo `selectedResources[0]`; mở confirm nếu MTT |
| `src/pages/adjusted-invoices/component/AdjustInvoiceModal/MttAdjustConfirmModal.tsx` (mới) | Popup copy epic: tiêu đề, đoạn Điều 10 + Lưu ý, checkbox, textlink tab mới, nút Hủy bỏ / Tiếp tục |

Tái sử dụng `ConfirmModal` (`src/components/ConfirmModal.tsx`) + `useToggle`. Không cần RTK Query / form mới.

Copy + URL Thông tư: lấy nguyên từ mô tả epic #87 (không tự diễn giải). Textlink neo vào cụm "Điều 10 Thông tư 91/2026/TT-BTC" → `https://vanban.chinhphu.vn/?pageid=27160&docid=219006&classid=1&orggroupid=4`.

## Luồng sau khi sửa

```
Popup "Chọn hóa đơn điều chỉnh"
  → chọn 1 HĐ
  → bấm "Lập hóa đơn"
      → không MTT: navigate create như cũ
      → MTT: popup "Lưu ý khi điều chỉnh hóa đơn từ máy tính tiền"
          → chưa tick: "Tiếp tục lập hóa đơn" DISABLED
          → tick + Tiếp tục: navigate create
          → Hủy bỏ: đóng confirm, vẫn ở popup chọn HĐ
```

Điểm kỹ thuật: `primaryAction` hiện là `url` (browser navigate, không chặn được). Đổi sang `onAction` + `navigate(...)`.

## Hướng đã chọn (không hỏi lại trừ khi bạn muốn đổi)

| # | Chủ đề | Hướng |
| --- | --- | --- |
| Q1 | Vào thẳng URL `/admin/adjusted-invoices/create/:id` | **Không** hiện popup mới. DoD epic chỉ gate tại popup chọn HĐ. Màn create vẫn có banner Lưu ý. |
| Q2 | BE hard-gate | **Không** làm. Epic không cấm cứng; không có field "đã xác nhận" để BE check. |
| Q3 | Dùng `is_calculating_machine` | **Không.** Chỉ `invoice_series.charAt(4)`. |
| Q4 | Split BE/FE issue | **1 issue FE** trên project `sapo-invoice-admin-frontend`. |

## Child issue

1. [#54](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-frontend/-/work_items/54) `[SI][FE] Popup xác nhận trách nhiệm khi lập HĐ điều chỉnh cho HĐ MTT` — assignee `duynd7`, labels giống epic (`T::Newfeature`, `module::hoa-don-dau-ra`, `workflow::ready`, `status::To do`, `HTF::Uplive`, `tier::3`)
