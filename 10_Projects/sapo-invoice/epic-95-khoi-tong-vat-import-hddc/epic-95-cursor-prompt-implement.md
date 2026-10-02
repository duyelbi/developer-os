---
created: 2026-09-29 09:30
status: Chưa chạy
project: "[[10_Projects/sapo-invoice/README]]"
---

# Prompt Cursor — implement epic #95 (khối `AT–AW` import HĐ điều chỉnh bỏ tick)

- Plan đầy đủ (nguồn chính, đọc trước): [[epic-95-plan]]
- Issue: BE [sapo-invoice-admin-service#191](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-service/-/work_items/191) · FE [sapo-invoice-admin-frontend#61](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-frontend/-/work_items/61)

Chạy **2 phiên riêng**: phiên BE trước (nhiều việc, có migration), phiên FE sau. Copy khung tương ứng dán vào Cursor (mở workspace `/Users/sapo/invoice`).

---

## Phiên 1 — BE

````markdown
# Task: Epic #95 — Import HĐ điều chỉnh bỏ tick: nhập khối "Tổng tiền theo từng thuế suất" (AT–AW) theo file (BE)

Workspace: `/Users/sapo/invoice/sapo-invoice-admin-service` (Java 17 / Spring Boot 3.3, Gradle `./gradlew`, macOS — bỏ qua dòng "Windows/PowerShell" trong `.claude/CLAUDE.md`).
Tạo branch từ `master` mới nhất: `feature/95-import-adjustment-vat-groups`.

## Đọc trước khi code (bắt buộc)

1. `/Users/sapo/developer-os/10_Projects/sapo-invoice/epic-95-khoi-tong-vat-import-hddc/epic-95-plan.md` — **plan chi tiết, làm đúng theo đây**; mâu thuẫn với mô tả epic thì theo plan.
2. `/Users/sapo/developer-os/10_Projects/sapo-invoice/ai/rules-backend.md` — DDD, multi-tenancy.
3. `.claude/rules/sonarqube.md`, `.claude/rules/ddd.md`, `.claude/rules/jpa.md` trong repo.
4. File mẫu chuẩn: `/Users/sapo/invoice/invoice-docs/docs/invoice/nhap-tong-tien-hoa-don-theo-file/mau_nhap_hoa_don_khoi-tong-vat.xlsx` (`git -C /Users/sapo/invoice/invoice-docs pull` trước).

Comment tiếng Việt cho logic nghiệp vụ, ngắn, theo style file đang sửa. Không refactor ngoài phạm vi.

## Việc cần làm (theo thứ tự)

### 1. Migration + cờ domain
- `src/main/resources/db/migration/V28__add_is_vats_from_file_to_invoices.sql` — nội dung đúng như plan mục Thiết kế §1 (không `AFTER`).
- `domain/invoice/model/Invoice.java`: field `isVatsFromFile` map `is_vats_from_file`.
  - Constructor tạo mới (chỗ gọi `setCustomVats` ~355): `isVatsFromFile = CollectionUtils.isNotEmpty(vats) && source == InvoiceSource.import_file`.
  - `update(...)` (~390): luôn `isVatsFromFile = false`.

### 2. Import — `application/service/invoice/InvoiceImportService.java` + model/enum
- Enum `InvoiceHeaderAdjustmentProactivelyCalculateImport`: thêm 5 hằng `AT1:AW1`, `AT2:AT3`, `AU2:AU3`, `AV2:AV3`, `AW2:AW3` (text đúng plan §2a).
- `InvoiceImportExcelAdjustmentModel`: 4 field index 45–48 + `hasVatGroupData()`; `readInvoiceAdjustmentExcelData` thêm `case 45..48`.
- Hàm chuẩn hóa thuế suất dùng chung (plan §2c) → áp cho `AT` **và** thay nhánh cột `W` bỏ tick đang `setVatName("KHAC:" + formattedVat)` (~2937) thành `formattedVat + "%"`. Giữ nguyên message lỗi `W`.
- Validate theo dòng (plan §2d) — chỉ khi `!automaticallyCalculate`; tiền dùng wrapper có sẵn `validateAdjustmentOriginalTotalAmountWithoutVat/VatAmount/Amount` của `ImportInvoiceValidator`. **Không** validate `AV ≠ 0` cho `0%/KCT/KKKNT`.
- Validate theo HĐ (plan §2e) — hàm riêng `validateAdjustmentVatGroups(...)` gọi sau vòng validate dòng; message nguyên văn theo bảng plan; đánh dấu `hasError` mọi dòng của HĐ lỗi.
- Generate (plan §2f): gộp 4 điểm chốt HĐ (~1252, ~1283, ~1316, ~1494) thành 1 helper; build `List<InvoiceVatRequest>` từ **từng dòng** có `vatGroupVatName`, làm tròn HALF_UP theo `DecimalConfigUtils.roundHalfUp` với key `decimal_digit_amount_without_vat` / `decimal_digit_vat_amount` / `decimal_digit_amount_after_tax`, trống = `0`; set `invoiceRequest.setAdjustmentVats(...)` chỉ khi có nhóm. Không đụng nhánh `automaticallyCalculate = true`.

### 3. Đọc cho XML — `InvoiceReadService.enrichInvoiceResponse` (~382)
- Rẽ nhánh theo plan §3; thêm `InvoiceMapper.fromInvoiceVatToResponse(InvoiceVat)`; `InvoiceResponse` thêm `@JsonIgnore boolean vatsFromFile`.
- **Không** đổi DTO path (`getById`, ~226–234) và không đổi hành vi khi flag = false.

### 4. XML — `InvoicePublishService.createInvoiceVats` (~1496)
- Điều kiện loop `vats`: `isMoreVatRate || invoiceResponse.isVatsFromFile()` (plan §4). `createVatMap` giữ nguyên.

### 5. Test (JUnit 5 + Mockito, theo style `ImportRowProcessorTest`, `InvoicePublishServiceTest`)
Làm đủ danh sách "Unit (BE)" trong plan mục Test. Bắt buộc có test chứng minh **flag = false → XML giống hệt trước**.

## ⛔ Không làm
- Không sửa nhánh tick, import HĐ gốc / thay thế, PDF/preview (`InvoicePreviewService`), DTO path của `InvoiceReadService`, màn sửa HĐ.
- Không dùng `invoices.metadata` làm cờ.
- Không "sửa chung" để XML luôn dùng bảng đã lưu (ảnh hưởng V2/V3 gửi `adjustment_vats`).
- Không commit/push khi chưa được yêu cầu; commit message **không** thêm `Co-Authored-By` hay trailer AI.

## Tự kiểm tra trước khi báo xong
- `./gradlew compileJava compileTestJava`, rồi `./gradlew test --tests '<Class>'` cho các test mới + `InvoicePublishServiceTest` + `ImportRowProcessorTest` — dán output.
- Liệt kê file đã sửa + tóm tắt từng file; ghi rõ chỗ nào lệch plan và vì sao.
````

---

## Phiên 1b — BE: giữ bảng thuế suất theo file khi "Lưu" / "Lưu & Phát hành" (chốt A2 hướng b, 2026-09-29)

Chạy **sau Phiên 1**, trên cùng branch `feature/95-import-adjustment-vat-groups`.

````markdown
# Task: Epic #95 (bổ sung) — Invoice.update giữ bảng tổng hợp thuế suất lấy theo file

Workspace: `/Users/sapo/invoice/sapo-invoice-admin-service` (branch `feature/95-import-adjustment-vat-groups`, đã có code Phiên 1: cột `is_vats_from_file`, field `Invoice.isVatsFromFile`, nhánh XML theo cờ). macOS, `./gradlew`.

## Bối cảnh (vì sao cần sửa)
Màn chi tiết HĐ điều chỉnh nháp trên admin FE chỉ có "Lưu" và "Lưu & Phát hành"; **cả hai đều PUT update trước** rồi mới phát hành (`sapo-invoice-admin-frontend/src/pages/adjusted-invoices/AdjustedInvoiceDetailPage.tsx`, `onSubmit` → `updateInvoice`). FE **không gửi** `adjustment_vats`. Hiện `Invoice.update(...)` luôn `internalSeVats()` + `isVatsFromFile = false` → HĐ import có khai khối AT–AW, bấm "Lưu & Phát hành" (kể cả không sửa gì) là mất bảng theo file, XML tính lại từ dòng hàng. Chốt mới: giữ bảng.

Plan: `/Users/sapo/developer-os/10_Projects/sapo-invoice/epic-95-khoi-tong-vat-import-hddc/epic-95-plan.md` (bảng chốt A2 + mục "Cập nhật sau review").

## Việc cần làm

### 1. `domain/invoice/model/Invoice.java` — method `update(...)`
Thay khối hiện tại:

```java
if (CollectionUtils.isNotEmpty(vats)) {
    this.setCustomVats(vats);
} else {
    this.internalSeVats();
}
this.isVatsFromFile = false;
```

bằng logic sau (tách private method cho gọn, vd `applyVatsOnUpdate(vats, adjustmentAmount)`):

| Điều kiện | Hành vi |
| --- | --- |
| `this.isVatsFromFile` **và** `Status.modify.equals(this.status)` **và** `adjustmentAmount != null && !adjustmentAmount.isAutoCalculate()` **và** `CollectionUtils.isEmpty(vats)` | **Không đụng** `this.vats`, **giữ** `isVatsFromFile = true` |
| `CollectionUtils.isNotEmpty(vats)` (client gửi custom vats) | `setCustomVats(vats)`, `isVatsFromFile = false` (như Phiên 1) |
| Còn lại (gồm bật lại tự động tính toán) | `internalSeVats()`, `isVatsFromFile = false` (như Phiên 1) |

- Comment tiếng Việt ngắn nêu **why**: "Lưu & Phát hành" luôn PUT trước, FE không gửi vats → phải giữ bảng lấy theo file (epic #95, chốt A2-b).
- Null-safe với `adjustmentAmount` (hiện code `modify` gọi thẳng `adjustmentAmount.isAutoCalculate()` — không đổi hành vi đoạn đó, chỉ điều kiện mới phải null-safe).
- Không đổi signature `update(...)`, không đổi `InvoiceCommonService`, không đổi FE.

### 2. Test — `src/test/java/vn/sapo/invoice/admin/invoice/domain/invoice/model/InvoiceVatsFromFileTest.java` (mới)
Dựng `Invoice` qua `Invoice.create(...)` với `status = modify`, `source = import_file`, `adjustmentAmount.isAutoCalculate = false`, custom vats 1 nhóm `8%` (vd chưa thuế 270000, thuế 21600, thanh toán 291600) + 1 dòng hàng 8% sao cho tính lại sẽ ra số khác (vd thuế 21601). Các case:
1. create → `isVatsFromFile() == true`, `getVats()` đúng giá trị file.
2. `update(...)` với `vats = null`, `isAutoCalculate = false` → vats **giữ nguyên** giá trị file, cờ vẫn `true`.
3. Như (2) nhưng HĐ **không có dòng hàng** → vats vẫn giữ (không bị rỗng).
4. `update(...)` với `isAutoCalculate = true` → vats tính lại từ dòng hàng, cờ `false`.
5. `update(...)` với `vats` khác rỗng → dùng vats request, cờ `false`.
6. HĐ tạo với `source = admin` + custom vats → cờ `false`; `update(...)` `vats = null` bỏ tick → tính lại như cũ (không giữ).

Nếu dựng `Invoice` quá nặng (nhiều tham số), viết helper builder trong chính file test; không sửa code production để phục vụ test.

## ⛔ Không làm
- Không sửa FE, `InvoicePreviewService`, `InvoiceReadService`, `InvoicePublishService`, import service.
- Không đổi hành vi HĐ không phải `modify`, HĐ không có cờ, HĐ tick tự tính.
- Không commit/push khi chưa được yêu cầu; commit message không thêm `Co-Authored-By` / trailer AI.

## Tự kiểm tra
- `./gradlew compileJava compileTestJava`, rồi `./gradlew test --tests 'vn.sapo.invoice.admin.invoice.domain.invoice.model.InvoiceVatsFromFileTest'` + các test đã thêm ở Phiên 1 + `InvoicePublishServiceTest` — dán output.
- Dán diff của `Invoice.java`.
````

---

## Phiên 2 — FE

````markdown
# Task: Epic #95 — File mẫu nhập HĐ điều chỉnh (bỏ tick) thêm khối AT–AW + ngày nhãn riêng (FE)

Workspace: `/Users/sapo/invoice/sapo-invoice-admin-frontend` (React 18 + TS, Vite, pnpm).
Branch từ `master` mới nhất: `feature/95-adjustment-totals-sample-vat-groups`.

Đọc trước: `.claude/commands/review-code.md` (bắt buộc trước khi sửa `.tsx`), `/Users/sapo/developer-os/10_Projects/sapo-invoice/ai/rules-frontend.md`, plan `/Users/sapo/developer-os/10_Projects/sapo-invoice/epic-95-khoi-tong-vat-import-hddc/epic-95-plan.md` mục Thiết kế §5.

## Việc cần làm
1. Copy `/Users/sapo/invoice/invoice-docs/docs/invoice/nhap-tong-tien-hoa-don-theo-file/mau_nhap_hoa_don_khoi-tong-vat.xlsx` đè lên `src/assets/files/mau_nhap_hoa_don_DEItyFnc.xlsx` (giữ tên file, không đổi import).
2. `src/pages/invoice/constants.ts`: giữ `SAMPLE_FILE_UPDATED_AT = "19/08/2026"`; thêm `ADJUSTMENT_TOTALS_SAMPLE_FILE_UPDATED_AT` = ngày uplive (chưa biết → để `"TODO(uplive)"` kèm comment, KHÔNG tự bịa ngày).
3. `src/pages/invoice/components/modal/InvoiceImportModal.tsx` (~313): loại file = HĐ điều chỉnh (`Status.MODIFY`) **và** bỏ tick → hiển thị hằng mới; mọi trường hợp khác giữ hằng cũ.

## ⛔ Không làm
Không đụng các file mẫu khác, logic checkbox, banner cảnh báo, API. Không commit/push khi chưa được yêu cầu; không thêm `Co-Authored-By`.

## Tự kiểm tra
- `pnpm lint` + `pnpm typecheck` + `pnpm format:check` — dán output.
- Mô tả cách verify tay: bỏ tick HĐ điều chỉnh → tải file có `AT–AW` + ngày mới; tick / HĐ mới / HĐ thay thế → ngày `19/08/2026`.
````
