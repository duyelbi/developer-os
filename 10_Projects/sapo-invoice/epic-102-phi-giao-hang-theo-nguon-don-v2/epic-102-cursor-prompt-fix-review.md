---
created: 2026-10-01 15:30
status: Chưa chạy — fix sau review lần 1
project: "[[10_Projects/sapo-invoice/README]]"
---

# Prompt Cursor — fix review Epic #102 (lần 1)

Plan: [[epic-102-plan]] · Prompt implement: [[epic-102-cursor-prompt-implement]] · Test case: [[epic-102-test-cases]]

Kết quả review 2026-10-01: BE 51 unit test pass (JDK 11), FE eslint 0 error, tsc không lỗi ở file thay đổi. Còn 3 việc cần sửa.

````markdown
# Task: Epic #102 — sửa theo review (3 mục)

Workspace `/Users/sapo/invoice`. Code đang ở nhánh `dev-money/feature/shipping-fee-by-source-SM-0` của 2 repo (chưa commit):
- `sapo-frontend-v3` — file `src/page/Settings/Einvoices/Einvoice.tsx`
- `sapo-einvoice-service` — 2 file test

Chỉ sửa đúng 3 mục dưới, không refactor thêm, không đổi hành vi khác.

## Mục 1 (bắt buộc) — FE: chip nguồn ngừng áp dụng hiển thị id thay vì tên

**Vấn đề:** `allOrderSources` (set ở ~270) lấy từ `fetchAllOrderSource` trong `src/store/TenantContext/tenantContextSlice.ts`, hàm này gọi `OrderSourceService.filter({ statuses: "active,default" })` → **không có nguồn inactive**. Vì vậy ở chỗ render chip (~1681, `const name = source?.name || id;`) nguồn ngừng áp dụng luôn rơi về id → hiện `34 (Ngừng áp dụng)`.

**Sửa:**
- Bỏ state `allOrderSources` hiện tại (không dùng được cho mục đích này). Thay bằng state `inactiveOrderSourceNames: Record<string, string>` (id → name).
- Thêm `useEffect` phụ thuộc `[shippingFeeSetting.order_source_ids, activeOrderSources]`:
  - `missing` = các id trong `order_source_ids` (khác null) **không** có trong `activeOrderSources` và **chưa** có trong `inactiveOrderSourceNames`.
  - `missing` rỗng → return.
  - Gọi `OrderSourceService.filter({ ids: missing.join(","), page: 1, limit: 250 })` — **không truyền `statuses`** (`OrderSourceFilter` đã có field `ids`, xem `src/services/OrderSourceService/types.ts`). Merge `id → name` vào state.
  - Lỗi API → bỏ qua (try/catch, không snackbar); chip vẫn fallback id.
  - Tránh gọi lặp: chỉ fetch id chưa có trong map; id không trả về từ API (đã bị xóa) thì ghi vào map với giá trị `""` để không fetch lại.
- Render chip: tên = `activeOrderSources` (nếu active) → `inactiveOrderSourceNames[id]` (nếu có, khác rỗng) → fallback `id`. Giữ nguyên hậu tố ` (Ngừng áp dụng)` và class `inactiveSourceChip`.
- **Không** sửa `fetchAllOrderSource` (dùng chung toàn app). Chỉ ghi chú: trang ≥ 2 của hàm này không truyền `statuses` → lỗi có sẵn, ngoài phạm vi.

## Mục 2 — FE: không đổi `null` thành `[]` khi danh sách nguồn chưa tải được

**Vấn đề:** `resolveShippingFeeForSubmit` (~133): store cũ `separate_line` + `order_source_ids = null` mà `activeOrderSources` rỗng (API lỗi) → payload thành `[]` → validate (~675) chặn lưu **mọi** cài đặt với lỗi "Nguồn đơn không được để trống".

**Sửa:** trong `resolveShippingFeeForSubmit`, nếu `activeSources.length === 0` → trả về `value` nguyên vẹn (giữ `null`). Cập nhật JSDoc của hàm cho khớp.

## Mục 3 — BE test: bỏ tên class đầy đủ inline (vi phạm CLAUDE.md)

- `src/test/java/vn/sapo/services/service/publisher/sapoinvoice/SapoInvoiceSettingUtilTest.java:163` — `java.util.List<String>` → `List<String>`, thêm `import java.util.List;` đúng thứ tự cụm import `java.util.*` hiện có.
- `src/test/java/vn/sapo/services/service/publisher/sapoinvoice/ShippingFeeSettingsTest.java:30` — tương tự.

## Kiểm tra trước khi báo xong
- BE (bắt buộc **JDK 11** — `mvn` mặc định trên máy là JDK 26, Lombok sẽ lỗi compile):
  ```bash
  cd /Users/sapo/invoice/sapo-einvoice-service
  JAVA_HOME=/Library/Java/JavaVirtualMachines/openjdk-11.jdk/Contents/Home mvn -q test -Dtest='SapoInvoiceSettingUtilTest,ShippingFeeSettingsTest,SapoInvoiceServiceShippingFeeResetTest,ShippingFeeLineHelperTest,EInvoiceItemTypeTotalsTest'
  ```
  Đọc kết quả trong `target/surefire-reports/*.txt` — phải 0 failure / 0 error.
- FE:
  ```bash
  cd /Users/sapo/invoice/sapo-frontend-v3
  npx eslint src/page/Settings/Einvoices/Einvoice.tsx
  npx tsc --skipLibCheck --noEmit 2>&1 | grep "Einvoices/Einvoice"
  ```
  eslint 0 error; lệnh tsc không in dòng nào (repo có lỗi tsc sẵn ở file khác — bỏ qua).
- Test tay (nếu chạy được local): store đã lưu nguồn WEB, chuyển WEB sang ngừng áp dụng → mở màn cấu hình → chip hiện `Website (Ngừng áp dụng)` (case C8/F7 trong test-cases).
- Không commit. Commit message (khi user commit) không có dòng `Co-Authored-By`.
- Báo lại: diff tóm tắt từng mục + output các lệnh kiểm tra.
````
