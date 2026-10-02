---
created: 2026-08-26 08:40
status: Fixed — working tree `sapo-invoice-admin-frontend` (chưa merge); đã vá follow-up review Correctness 1–6 + cleanup
priority: Medium
project: "[[10_Projects/sapo-invoice/README]]"
repo: sapo-invoice-admin-frontend
---

# Template editor — lệch layout khi chọn thư viện + Hủy viền không revert preview

Màn: **Thêm mới / Sửa mẫu hóa đơn** (`/admin/templates/create`, `/admin/templates/:id`) → tab **Cấu hình chung** → accordion **Logo, hình nền, viền hóa đơn**.

## Mô tả

### Bug A — Lệch layout khi chọn hình nền / viền từ thư viện

1. Vào tab **Cấu hình chung**, mở accordion Logo/hình nền/viền.
2. **Hình nền** → Chọn từ thư viện (hoặc **Viền hóa đơn** → Chọn từ thư viện).
3. Quan sát cột phải: **mất Tabs** (Thông tin / Cấu hình chung / Tùy chỉnh), form “Tên mẫu”… bị kéo xuống dưới card “Danh sách …”.

Kỳ vọng: Tabs vẫn hiện; UI chọn thư viện nằm **inline** trong accordion.

### Bug B — Hủy viền chỉ reset select, không revert editor

1. Chưa có viền → mở thư viện viền → chọn V00x (preview iframe hiện viền).
2. Bấm **Hủy**, hoặc **đóng accordion** / sang Font·QR.
3. Select về “Chưa chọn viền”, nhưng **preview iframe vẫn giữ viền**.

Hình nền (watermark) Hủy thì revert cả select lẫn preview — viền không đồng bộ.

## Nguyên nhân

### Bug A

Điều kiện render cột phải dạng:

```tsx
!isOpenBorder && !isOpenLogo && !mdDown ? <Tabs /> : <MobileFallback />;
```

Khi mở thư viện trên **desktop**, điều kiện `false` → rơi vào nhánh **mobile fallback** (xếp dọc, không Tabs).

- Ternary lỗi đưa vào qua MR [!188](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-frontend/-/merge_requests/188) (`feature/hide-navigation`, commit `feat: 6870` — responsive).
- **Không** phải do MR Tabs “Cấu hình chung” [!338](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-frontend/-/merge_requests/338) (`feature/template-font-mau-qr`). !338 chỉ đổi nội dung tab 1 → accordion; giữ nguyên ternary → lỗi lộ rõ hơn khi test chọn thư viện.

Pattern đúng lúc mới có Tabs + thư viện (Jun 2025): ẩn Tabs khi mở select, **không** có `else` mobile gộp chung.

### Bug B

Hai lớp:

1. **Debounce race** — `useBorderRenderer` debounce 100ms; Hủy có thể bị update cũ ghi đè / không flush kịp (watermark dùng `immediate=true`).
2. **Early-return trên màn create** — effect viền:

   ```ts
   if (!isStateRestored && !borderImage && !borderImageDataUrl) return;
   ```

   Create flow thường `isStateRestored === false`. Sau Hủy về “chưa chọn”, effect **return sớm** → không clear DOM iframe. Select đã reset, editor không.

## Cách khắc phục

### Layout (Bug A)

- Giữ `<Tabs>` theo `mdDown`; **không** ẩn Tabs khi mở thư viện.
- Chọn thư viện **inline** trong accordion (`LogoWatermarkSelector` / `BorderImageSelector` — không bọc Card thay cả cột).
- Giữ Logo + slider khi đang chọn hình nền.
- UX chọn thư viện:
  | Thao tác | Select UI | Preview |
  |---|---|---|
  | **Hủy** | Đóng | Revert |
  | **Đóng accordion** / sang Font·QR | = Hủy | Revert |
  | **Áp dụng** | Đóng | Giữ lựa chọn |
- Mở thư viện hình nền khi đang chọn viền (và ngược lại) → Hủy cái đang mở.

File chính: `TemplateManagerPage.tsx`, `LogoWatermarkSelector.tsx`, `BorderImageSelector.tsx`.

### Viền ↔ editor (Bug B)

- `useBorderImage.cancelSelection`: clear / restore `borderImageDataUrl` ngay (cache nếu có viền trước).
- `useBorderRenderer.renderBorder(..., immediate)`: hủy debounce + update DOM ngay.
- Effect viền: track `hadBorder` (ref); chỉ skip clear lúc mount trước restore — **không** chặn Hủy sau khi user đã chọn.

File: `hooks/useBorderImage.ts`, `hooks/useBorderRenderer.ts`, effect trong `TemplateManagerPage.tsx`.

## Follow-up review (2026-08-26) — đã vá

Correctness từ code review sau diff đầu:

| #         | Vấn đề                                                         | Fix                                                                                                      |
| --------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 1         | Bỏ gate `isBorderReady` → e-document nháy mất viền lúc restore | Khôi phục gate `(isBorderReady \|\| borderImage)` cho debounce; `immediate` dùng `allowClearBeforeReady` |
| 2         | Hủy khi rời chưa gắn Tabs / jump validate Lưu                  | `handleTabSelect`, `jumpToConfigSection` trong `useDocumentLibrarySelection`                             |
| 3–4       | Cache evict / fetch stale ghi đè sau Hủy                       | Pin `prevBorderImageDataUrl` lúc mở picker; `requestId` bỏ stale fetch; evict không xóa key đang pin     |
| 5         | `reset()` không đóng picker / không clear prev                 | `reset()` đóng modal + clear prev + invalidate request                                                   |
| 6         | Logo/watermark chưa vá như border                              | Cùng pattern pin dataUrl + stale guard + reset đóng picker trong `useLogoWatermark`                      |
| 8–9,13–14 | Cleanup                                                        | Bỏ DOM cleanup trùng; `LibrarySelectShared`; extract `useDocumentLibrarySelection`                       |

Chưa làm: #10 reuse `Modal2/Footer` (footer modal có outline semantics khác accordion); #12 thay `hadBorder` bằng `isBorderRestoring` toàn cục (giữ hadBorder + comment — đủ đúng, tránh scope lớn).

### Follow-up 2 (2026-08-26) — race pin/requestId + sample change

| #                                     | Vấn đề                                                                                | Fix                                                                                       |
| ------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Race Hủy nuốt fetch restore           | Mở picker rồi Hủy khi fetch tô màu SVG chưa xong → bump requestId → mất màu vĩnh viễn | `sameSelection` → không bump; đổi lựa chọn mới invalidate + pin hoặc `updateDataUrl` lại  |
| `isRevertingToSavedSample` kẹt picker | `setTabSelected(0)` bỏ qua cancel; không reset picker                                 | `cancelLibrarySelectIfNeeded()` trước khi đổi sample / restore                            |
| Lag kéo màu                           | Effect luôn `immediate`                                                               | `flushBorderRender` khi clear/đổi identity; `scheduleBorderRender` (debounce) khi kéo màu |
| DRY pin/cache                         | Lặp 2 hook                                                                            | Extract `useTintedSvgDataUrl`                                                             |

## Lesson Learned

1. Ternary gộp nhiều điều kiện (`!A && !B && !mobile ? X : Y`) dễ khiến `Y` chạy cho case không thuộc mobile — tách: “đang select?” rồi mới “desktop Tabs vs mobile stack”.
2. Preview DOM + state form phải cùng semantics khi Hủy (watermark đã `immediate`; border quên → lệch UX).
3. Guard “tránh nháy trước restore” (`!isStateRestored && empty`) trên create có thể **chặn clear sau tương tác user** — cần phân biệt “chưa từng chọn” vs “đã chọn rồi Hủy”.
4. Smoke test bắt buộc sau đổi tab/accordion: **Chọn từ thư viện → Áp dụng / Hủy / đóng accordion** trên desktop, kiểm tra cả select và iframe.

## Related Notes

- [[10_Projects/sapo-invoice/ai/rules-frontend]]
- MR gốc ternary: [!188](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-frontend/-/merge_requests/188)
- MR Tabs Cấu hình chung (không gây ternary): [!338](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-frontend/-/merge_requests/338)
