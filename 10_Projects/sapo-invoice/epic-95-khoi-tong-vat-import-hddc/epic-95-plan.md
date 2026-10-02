---
created: 2026-09-29 09:00
status: Đã implement + lên dev, E2E dev đạt phần chính — xem [[epic-95-test-results]]
project: "[[10_Projects/sapo-invoice/README]]"
---

# Epic #95 — Nhập khối tổng tiền theo từng thuế suất (`AT–AW`) khi import HĐ điều chỉnh bỏ tick

- GitLab epic: [#95](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/95) · BA chốt: [note_784732](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/95#note_784732) · Dev bổ sung: [note_785766](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/95#note_785766)
- Child issue: BE [sapo-invoice-admin-service#191](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-service/-/work_items/191) · FE [sapo-invoice-admin-frontend#61](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-frontend/-/work_items/61) — assignee `duynd7`, iteration #35
- SRS: `invoice-docs/docs/invoice/nhap-tong-tien-hoa-don-theo-file/srs.md` **v0.20** (đã đồng bộ chữ cái cột + chuẩn hóa `3.6%`; đặc tả `AT–AW` còn `TODO` → dùng epic + note BA)
- File mẫu chuẩn: `invoice-docs/docs/invoice/nhap-tong-tien-hoa-don-theo-file/mau_nhap_hoa_don_khoi-tong-vat.xlsx` (đã merge master, MR invoice-docs!162)
- Prompt Cursor: [[epic-95-cursor-prompt-implement]]

> **Thứ tự ưu tiên nguồn khi mâu thuẫn:** note BA 784732 > plan này > mô tả epic > SRS. Mô tả epic **chưa cập nhật** theo chốt (vẫn ghi `KHAC:3.6%`, "không đổi code phát hành", ER-08 thông báo cũ, IDOR 404…).

## Tóm tắt

Import HĐ điều chỉnh, **bỏ tick** "Tự động tính toán giá trị tổng tiền": thêm 4 cột `AT–AW` (Thuế suất / Tổng tiền chưa thuế / Tổng tiền thuế / Tổng tiền thanh toán), **mỗi dòng = 1 nhóm thuế suất**. HĐ có khai → bảng tổng hợp thuế suất lưu **đúng theo file** (chỉ làm tròn HALF_UP theo `DecimalConfiguration`) **và XML `THTTLTSuat` lấy theo bảng này** — cho cả mẫu nhiều thuế suất lẫn mẫu 1 thuế suất. HĐ không khai → như hiện hành.

## Chốt nghiệp vụ (note BA 784732 + note dev 785766)

| # | Chốt |
| :-: | --- |
| A1 | Có khai `AT–AW` → lưu bảng tổng hợp theo file **và** XML `THTTLTSuat` lấy theo bảng này, **kể cả mẫu 1 thuế suất**. Không đối chiếu với `AN–AS`. Không khai → như hiện hành. §4.2-2 giữ nguyên (mẫu 1 thuế suất: đúng 1 nhóm, `AT` = `W`). |
| A2 | ~~Mở nháp → sửa → Lưu: như hiện hành (tính lại từ dòng hàng).~~ **Đổi 2026-09-29 (dev chốt, hướng b):** review phát hiện màn chi tiết HĐĐC nháp chỉ có "Lưu" / "Lưu & Phát hành", **cả hai đều PUT update trước** (`AdjustedInvoiceDetailPage.tsx` `onSubmit` → `updateInvoice`) → giữ A2 cũ thì phát hành từ màn chi tiết luôn mất giá trị theo file. Chốt mới: HĐ `modify`, bỏ tick (`is_auto_calculate = false`), `is_vats_from_file = true`, request **không** gửi vats → `update` **giữ nguyên bảng đã lưu + giữ cờ**. Người dùng bật lại tự tính, hoặc client gửi vats → như cũ (cờ tắt). Xem "Cập nhật sau review" cuối file. |
| A3 | `AT = 3.6` → lưu `vat_name = "3.6%"`; XML `TSuat = KHAC:3.6%` (tiền tố do publish tự thêm). Cột `W` nhập `3.6` nếu XML sai → sửa luôn trong task. |
| B1/B2 | Sai template / sửa tiêu đề cột → dùng nguyên thông báo hiện có: *"File nhập không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán và thực hiện tải lại file mẫu."* |
| B3 | HĐ gốc khác store → lỗi dòng HĐ gốc không tồn tại như hiện hành (không phải 404). |
| B4 | Có 1 dòng lỗi → không tạo HĐ đó; HĐ khác vẫn tạo (như hiện hành). |
| B5 | Nhóm `0%/KCT/KKKNT` khai `AV ≠ 0` → **không báo lỗi**, lưu theo file; XML ghi `TThue = 0` (code hiện có đã làm). |
| B8 | Chỉ đổi ngày nhãn cho file mẫu **HĐ điều chỉnh bỏ tick**; file mẫu khác giữ ngày cũ. |
| PDF | PDF **mẫu 1 thuế suất giữ như hiện hành** (`W` + `AP/AQ`), chấp nhận có thể khác XML. Mẫu nhiều thuế suất: PDF/chi tiết đọc bảng đã lưu → tự đúng. |
| CQT | QA gửi thử ca lệch khối VAT vs `AN–AS` trên môi trường test CQT; CQT từ chối → báo BA xem lại A1 trước uplive. |

## Hiện trạng code (đã đọc `origin/master` 3d6e0beda, 2026-09-28)

### Import (`InvoiceImportService.java`)

| Chỗ | Dòng | Ghi chú |
| --- | --- | --- |
| `importFileInvoiceAdjustment` | ~421 | entry job; đọc `automaticallyCalculate` từ history |
| `generateRequestInvoiceAdjustmentFromExcelData` | ~1234 | **4 điểm chốt HĐ copy-paste** (~1252, ~1283, ~1316, ~1494): `applyFormOfDiscount` + `isTaxReduction` + `put` map |
| khối `!automaticallyCalculate` đọc `AN–AS` | ~1406 | chỉ lấy dòng đầu có dữ liệu (`adjustmentAmountFilledFromData`) |
| `validateInvoiceAdjustmentExcelData` | ~2590 | validate **từng dòng**; `listFailedInvoices.add("Hàng {row}: ...")` + `data.setHasError(true)` |
| chuẩn hóa cột `W` nhánh bỏ tick | ~2919–2945 | ⚠️ ~2937 `data.setVatName("KHAC:" + formattedVat)` → sai (A3) |
| `readInvoiceAdjustmentExcelData` | ~3263 | map theo index `case 0..44`; dừng ở dòng rỗng đầu tiên (`AnyFieldValidator.isValid`) |
| `validateImportFile` | ~3445 | so khớp **tuyệt đối** header theo `cellRange` + **số lượng** → thêm enum là file cũ tự bị chặn |
| `isItemEmpty(InvoiceImportExcelAdjustmentModel)` | ~3643 | chỉ xét cột hàng hóa → dòng chỉ có `AT–AW` không sinh dòng hàng |

Model/enum: `application/model/invoice/invoiceimport/InvoiceHeaderAdjustmentProactivelyCalculateImport.java` (tới `total_amount` `AS2:AS3`), `InvoiceImportExcelAdjustmentModel.java` (index 0–38 + 6 field tổng 39–44).

### Domain / đọc / phát hành

| Chỗ | File | Hành vi |
| --- | --- | --- |
| Override bảng thuế suất | `InvoiceUpdateRequest.adjustmentVats` (`List<InvoiceVatRequest>`) → `Invoice` ctor ~355 / `update` ~422 → `setCustomVats` (~380) | có sẵn; domain **không** làm tròn |
| Dẫn xuất từ dòng hàng | `Invoice.internalSeVats` (~921) | chạy khi không có custom vats (create & update) |
| Luồng tạo HĐĐC từ import | `ImportRowProcessor.processAdjustment` → `InvoiceProcessingService.createInvoiceAdjustment` (~90) → `InvoiceCommonService` → `Invoice.create(... source=import_file ..., adjustmentVats, ...)` | `source` = `import_file` do import set |
| Đọc cho màn chi tiết / PDF | `InvoiceReadService.getById` → DTO path ~226–234 | **dùng bảng đã lưu** (fallback tính lại nếu rỗng) |
| **Đọc cho XML** | `InvoicePublishService.generateXmlTemplate` (~1094) → `InvoiceReadService.getInvoiceResponses(tenantId, List<Invoice>, …)` → `enrichInvoiceResponse` (~382–387) | ⚠️ **luôn** `setVats(enrichVatInfo(...))` = tính lại từ dòng hàng, **bỏ qua bảng đã lưu**. Chỉ `generateXmlTemplate` gọi hàm này (tất cả luồng phát hành, kể cả MTT, đi qua đây) |
| Dựng `THTTLTSuat` | `InvoicePublishService.createInvoiceVats` (~1496) | series `1*`: `isMoreVatRate` → loop `vats`; mẫu 1 thuế suất → 1 nhóm từ `invoice.vatName` + `originalTotalAmountWithoutVat/VatAmount` cấp HĐ. `createVatMap` ép `TThue=0` cho `0%/KCT/KKKNT` (B5 ✅) |
| Chuẩn hóa `TSuat` | `MoneyInfo.VatRate.getVatRateNameByName` | không thuộc `0%/5%/8%/10%/KCT/KKKNT` → thêm `KHAC:` |

⇒ Không sửa đường đọc XML thì **mục tiêu epic không đạt** kể cả mẫu nhiều thuế suất (XML vẫn 21.601; HP-12 → `THTTLTSuat` rỗng).

> ⚠️ **Không sửa chung** đường đọc XML (luôn dùng bảng đã lưu): V2 (`sapo-einvoice-service`) và V3 (`invoice-app`) đang gửi `adjustment_vats` sang SI → XML của họ sẽ đổi ngay khi deploy. Chỉ rẽ nhánh bằng cờ riêng của import. Hiện tượng "màn chi tiết/PDF theo bảng đã lưu nhưng XML tính lại" của V2/V3 là **lỗi tiềm ẩn ngoài phạm vi** → issue riêng.

### FE (`sapo-invoice-admin-frontend`)

- `src/pages/invoice/components/modal/InvoiceImportModal.tsx`: `getDownloadSampleLink` (~131) → `importInvoiceAdjustmentTotalsSampleURL` = `app/assets/files/mau_nhap_hoa_don_DEItyFnc.xlsx?url` (file thật: **`src/assets/files/mau_nhap_hoa_don_DEItyFnc.xlsx`**); nhãn `(cập nhật ngày: {SAMPLE_FILE_UPDATED_AT})` (~313).
- `src/pages/invoice/constants.ts:112` `SAMPLE_FILE_UPDATED_AT = "19/08/2026"` — dùng chung mọi template.
- Đã diff: file mẫu mới **giống hệt** `DEItyFnc.xlsx` cột `A–AS` (header + merge), chỉ thêm `AT1:AW1` "Tổng tiền theo từng thuế suất" + `AT2:AT3` "Thuế suất" (có comment giống `AK2`) · `AU2:AU3` "Tổng tiền chưa thuế" · `AV2:AV3` "Tổng tiền thuế" · `AW2:AW3` "Tổng tiền thanh toán".

## Thiết kế

### 1. Cờ nguồn bảng thuế suất — `invoices.is_vats_from_file`

- Cột mới `is_vats_from_file TINYINT(1) NOT NULL DEFAULT 0`. Không dùng `invoices.metadata` (JSON public, client ghi đè được qua API).
- `Invoice`: field `isVatsFromFile` (`@Column(name = "is_vats_from_file")`).
  - **Create:** `true` khi `CollectionUtils.isNotEmpty(vats) && source == InvoiceSource.import_file`; ngược lại `false`.
  - **Update:** luôn `false` (A2 — sửa & lưu thì quay về như hiện hành, kể cả khi update có gửi custom vats từ API).
- Migration `src/main/resources/db/migration/V28__add_is_vats_from_file_to_invoices.sql` (số lớn nhất hiện tại là `V27`):
  ```sql
  -- Epic #95: đánh dấu bảng tổng hợp thuế suất lấy theo file import (khối AT–AW),
  -- để XML THTTLTSuat dùng bảng đã lưu thay vì tính lại từ dòng hàng.
  ALTER TABLE invoices
      ADD COLUMN IF NOT EXISTS is_vats_from_file TINYINT(1) NOT NULL DEFAULT 0
      COMMENT 'Bảng tổng hợp thuế suất lấy theo file import (epic #95)';
  ```
  Không dùng `AFTER` (để MariaDB `ADD COLUMN` INSTANT trên bảng lớn). **Chạy migration trước khi deploy BE** (entity map cột → thiếu cột là lỗi SELECT).

### 2. Import

**2a. Enum header** — thêm cuối `InvoiceHeaderAdjustmentProactivelyCalculateImport`:

```java
// total vat info (khối tổng tiền theo từng thuế suất — epic #95)
total_vat_info("Tổng tiền theo từng thuế suất", "AT1:AW1"),
vat_group_vat_name("Thuế suất", "AT2:AT3"),
vat_group_amount_without_vat("Tổng tiền chưa thuế", "AU2:AU3"),
vat_group_vat_amount("Tổng tiền thuế", "AV2:AV3"),
vat_group_total_amount("Tổng tiền thanh toán", "AW2:AW3");
```

**2b. Model + reader** — `InvoiceImportExcelAdjustmentModel` thêm `vatGroupVatName` (45), `vatGroupAmountWithoutVat` (46), `vatGroupVatAmount` (47), `vatGroupTotalAmount` (48); reader thêm `case 45..48`. Thêm helper `hasVatGroupData()` = một trong 4 ô có giá trị.

**2c. Hàm chuẩn hóa thuế suất dùng chung** (private static trong service hoặc `ImportInvoiceValidator`):

```
normalizeImportVatRate(raw) -> Optional<String>
  trim; chứa "%" -> invalid
  "KCT"/"KKKNT" -> giữ nguyên
  BigDecimal(raw) < 0 -> invalid; lỗi parse -> invalid
  s = bd.stripTrailingZeros().toPlainString()
  s ∈ {0,5,8,10} -> s + "%"  ; khác -> s + "%"   // "3.6" -> "3.6%" (KHÔNG thêm "KHAC:")
```

Dùng cho `AT` **và** thay nhánh `W` bỏ tick ở ~2926–2941 (A3): `W = 3.6` → `3.6%`. Giữ nguyên message lỗi hiện có của `W`.

**2d. Validate theo dòng** (trong `validateInvoiceAdjustmentExcelData`, chỉ khi `!automaticallyCalculate`, format `"Hàng {row}: {msg}"` + `setHasError(true)`):

| Điều kiện | Message |
| --- | --- |
| `hasVatGroupData()` mà `AT` trống | `Thuế suất không được để trống` |
| `AT` có giá trị, `normalizeImportVatRate` invalid | `Thuế suất không hợp lệ` |
| `AU/AV/AW` không phải số / quá 20 chữ số | tái dùng wrapper `protected static` có sẵn trong `ImportInvoiceValidator`: `validateAdjustmentOriginalTotalAmountWithoutVat` (AU), `validateAdjustmentOriginalTotalVatAmount` (AV), `validateAdjustmentOriginalTotalAmount` (AW) — tên trường trùng tiêu đề cột nên message giống hệt `AP/AQ/AS` (chấp nhận, theo B1 "dùng lại thông báo hiện có"; số dòng vẫn phân biệt được) |

Hợp lệ → `data.setVatGroupVatName(normalized)`. Không validate `AV ≠ 0` cho `0%/KCT/KKKNT` (B5). Chấp nhận số âm.

**2e. Validate theo HĐ** — lượt riêng **sau** vòng validate dòng, gom dòng theo cách generate đang gom (dòng có đủ `rootSerial + rootNo + invoiceSeries` mở HĐ mới; dòng sau không có 3 trường → thuộc HĐ trước). Chỉ xét dòng có `vatGroupVatName`. Lỗi → thêm message vào dòng **đầu** của HĐ và `setHasError(true)` cho **mọi dòng** của HĐ đó:

| # | Điều kiện | Message |
| :-: | --- | --- |
| 1 | 2 dòng cùng `vatGroupVatName` | `Thuế suất {x} bị nhập trùng trong khối Tổng tiền theo từng thuế suất` (`{x}` = dạng chuẩn, vd `8%`) |
| 2a | Mẫu 1 thuế suất (`series.startsWith("1") && !isMoreVatRate`) có > 1 nhóm | `Mẫu hóa đơn {Ký hiệu} chỉ hỗ trợ nhập một thuế suất trong khối Tổng tiền theo từng thuế suất` |
| 2b | Mẫu 1 thuế suất, 1 nhóm, `vatGroupVatName ≠` `vatName` (cột `W` đã chuẩn hóa) | `Mẫu hóa đơn {Ký hiệu} có Thuế suất trong khối Tổng tiền theo từng thuế suất không khớp với Thuế GTGT cả hóa đơn` (nếu `W` trống thì guard hiện có "cần có Thuế GTGT trên cả hóa đơn" đã báo — không báo 2b trùng) |
| 3 | Mẫu không phải GTGT (`!series.startsWith("1")`) có khai | `Mẫu hóa đơn {Ký hiệu} không hỗ trợ nhập thuế GTGT` |

> Lượt gom HĐ nên tách hàm riêng (`validateAdjustmentVatGroups`) — `validateInvoiceAdjustmentExcelData` đã rất dài (Sonar complexity, `.claude/rules/sonarqube.md`).

**2f. Generate** (`generateRequestInvoiceAdjustmentFromExcelData`):
- Gộp 4 điểm chốt HĐ thành 1 helper `finalizeAdjustmentRequest(invoiceRequest, templates, automaticallyCalculate, vatGroups)` → giữ nguyên logic `applyFormOfDiscount` + `isTaxReduction`; thêm set `adjustmentVats`.
- Với `!automaticallyCalculate`: mỗi dòng **không lỗi** có `vatGroupVatName` → `InvoiceVatRequest` (đọc **từng dòng**, không áp "dòng đầu"):
  - `vatName` = `vatGroupVatName`
  - `originalTotalAmountWithoutVat` = `roundHalfUp(AU, decimal_digit_amount_without_vat)`, trống → `0`
  - `originalTotalVatAmount` = `roundHalfUp(AV, decimal_digit_vat_amount)`, trống → `0`
  - `originalTotalAmount` = `roundHalfUp(AW, decimal_digit_amount_after_tax)`, trống → `0`
  - Giữ thứ tự dòng trên file.
- HĐ không có nhóm → **không** set `adjustmentVats` (null) → domain tự dẫn xuất như cũ.
- Không đụng nhánh `automaticallyCalculate = true`.

### 3. Đọc cho XML — `InvoiceReadService.enrichInvoiceResponse` (~382)

```java
// Epic #95: HĐ import có khai khối AT–AW → XML dùng bảng đã lưu; còn lại giữ tính lại từ dòng hàng như cũ
if (invoice.isVatsFromFile() && CollectionUtils.isNotEmpty(invoice.getVats())) {
    invoiceResponse.setVats(invoice.getVats().stream().map(invoiceMapper::fromInvoiceVatToResponse).toList());
    invoiceResponse.setVatsFromFile(true);
} else {
    invoiceResponse.setVats(enrichVatInfo(invoiceResponse, decimalConfigurations));
}
```

- `InvoiceMapper`: thêm `InvoiceVatResponse fromInvoiceVatToResponse(InvoiceVat vat)` (4 field cùng tên).
- `InvoiceResponse`: thêm `@JsonIgnore private boolean vatsFromFile;` (chỉ dùng nội bộ publish, không lộ API). Không cần set ở DTO path.

### 4. XML — `InvoicePublishService.createInvoiceVats` (~1496)

```java
if (invoiceSerial.startsWith("1")) {
    if (Boolean.TRUE.equals(invoiceResponse.getIsMoreVatRate()) || invoiceResponse.isVatsFromFile()) {
        for (var vat : invoiceResponse.getVats()) { ... createVatMap(vat...) }   // như nhánh nhiều thuế suất
    } else { ... giữ nguyên nhánh mẫu 1 thuế suất ... }
}
```

`createVatMap` giữ nguyên (B5). PDF mẫu 1 thuế suất **không sửa**.

### 5. FE (#61)

- Thay `src/assets/files/mau_nhap_hoa_don_DEItyFnc.xlsx` bằng `invoice-docs/docs/invoice/nhap-tong-tien-hoa-don-theo-file/mau_nhap_hoa_don_khoi-tong-vat.xlsx` (giữ tên file để không đổi import).
- `constants.ts`: giữ `SAMPLE_FILE_UPDATED_AT = "19/08/2026"`; thêm `ADJUSTMENT_TOTALS_SAMPLE_FILE_UPDATED_AT = "<dd/MM/yyyy ngày uplive>"`. `InvoiceImportModal`: `invoiceImportType === MODIFY && !automaticallyCalculate` → hiển thị hằng mới; còn lại hằng cũ.
- ⚠️ Ngày uplive chưa biết → để placeholder `TODO(uplive)` và **chốt trước khi merge**.

## Ngoài phạm vi

- Nhánh tick; import HĐ gốc / thay thế; PDF mẫu 1 thuế suất; màn sửa HĐ điều chỉnh (A2 = như hiện hành).
- Sửa chung đường đọc XML cho V2/V3 `adjustment_vats` → issue riêng.
- Update SRS UC-03/UC-04 (BA làm).

## Rủi ro

| # | Rủi ro | Mức | Giảm thiểu |
| :-: | --- | :-: | --- |
| 1 | Sửa `enrichInvoiceResponse` / `createInvoiceVats` — luồng XML của **mọi** HĐ | Cao | Chỉ rẽ nhánh khi `is_vats_from_file = true` (mọi HĐ cũ = 0). Unit test cả nhánh cũ. QA hồi quy phát hành: HĐ gốc 1/nhiều thuế suất, thay thế, điều chỉnh tick, MTT, V2/V3 |
| 2 | Migration trên bảng `invoices` lớn | Thấp | Add column default, không `AFTER`, không backfill; chạy trước deploy BE |
| 3 | CQT từ chối khi tổng nhóm ≠ tổng thuế HĐ (A1 không đối chiếu) | TB | QA test môi trường CQT (ED-02) trước uplive; từ chối → báo BA |
| 4 | Mẫu 1 thuế suất: PDF ≠ XML | Thấp–TB | Đã báo BA (note 785766) |
| 5 | Lệch deploy FE/BE → người dùng bị "File nhập không đúng mẫu" | TB | Deploy #191 + #61 cùng đợt |
| 6 | Sửa chuẩn hóa cột `W` (A3) đổi `vat_name` lưu cho HĐ mẫu 1 thuế suất nhập số khác | Thấp | Chỉ nhánh bỏ tick, chỉ giá trị ngoài `0/5/8/10/KCT/KKKNT`; QA verify XML `TSuat` |

## Test

### Unit (BE)

- Reader: đọc đúng `case 45–48`; dòng chỉ có `AT–AW` vẫn được đọc (không bị coi là dòng rỗng).
- `normalizeImportVatRate`: `8`, `8.0`, `08`→`8%`; `3.6`→`3.6%`; `KCT`; `8%`/`abc`/`-1` → invalid.
- Validate: 6 quy tắc §4.2 + trống-tiền-có-thuế-suất = 0; lỗi HĐ đánh dấu mọi dòng; HĐ khác không bị ảnh hưởng.
- Generate: HP-01 (2 nhóm theo file), HP-06 (trống = 0), HP-07 (làm tròn), HP-12 (không dòng hàng), ED-01 (dòng chỉ VAT không sinh dòng hàng), HĐ không khai → `adjustmentVats == null`.
- Domain `Invoice`: create + custom vats + `import_file` → flag `true`; source khác → `false`; `update(...)` → `false`.
- `InvoiceReadService`/`InvoicePublishService` (mở rộng `InvoicePublishServiceTest` nếu tiện): flag `true` → `THTTLTSuat` = bảng lưu (cả mẫu 1 thuế suất); flag `false` → giống hệt code cũ; `KCT` có `AV≠0` → `TThue=0`; `3.6%` → `KHAC:3.6%`.

### QA (ngoài bảng §6 epic)

- **XML sau phát hành** (quan trọng nhất): mẫu nhiều thuế suất ca 21.600/21.601 (ED-03), HP-12 không dòng hàng, mẫu 1 thuế suất HP-02.
- CQT test env: ca lệch ED-02 có được cấp mã không.
- Nháp import (bỏ tick, có `AT–AW`) → mở chi tiết → **"Lưu & Phát hành" không sửa gì** → XML vẫn theo file (A2 mới).
- Như trên nhưng sửa tên người mua / sửa dòng hàng → XML **vẫn** theo file (A2 mới).
- Như trên nhưng bật lại "tự động tính toán" trên form → Lưu → XML tính lại từ dòng hàng như cũ.
- Phát hành từ màn danh sách (không qua PUT) → XML theo file.
- `W = 3.6` bỏ tick → `TSuat = KHAC:3.6%` (A3).
- Ô `AT` dạng số / text / `8.0` / `8%` (lỗi).
- Hồi quy: nhánh tick; import HĐ gốc/thay thế; nhãn ngày các file mẫu khác vẫn `19/08/2026`; template bỏ-tick cũ bị chặn.
- Sửa kỳ vọng epic: ER-08/ED-06 dùng thông báo sai mẫu hiện có; ED-08 → lỗi dòng HĐ gốc không tồn tại; HP-11 `vat_name = 3.6%`.

## Việc sau khi plan chạy

- [ ] Cập nhật mô tả #191 (bỏ D1 "giữ bảng khi sửa nháp", bỏ validate B5, thêm mục 1/3/4 của plan này) và #61 (đường dẫn `src/assets/files`, B8 hằng riêng).
- [ ] Tạo issue riêng: V2/V3 gửi `adjustment_vats` nhưng XML tính lại từ dòng hàng.
- [ ] Chốt ngày uplive cho nhãn FE.
- [ ] Báo BA đổi chốt A2 (hướng b) để cập nhật epic.

## Cập nhật sau review (2026-09-29)

- Cursor đã implement BE theo plan; review code: đúng plan, không thấy lỗi logic trong các file đã đọc (chưa xem được `git diff` đầy đủ / chạy test do Bash lỗi phiên review).
- **Lỗ hổng plan:** A2 cũ + "Lưu & Phát hành" luôn PUT → mất giá trị theo file. Chốt **hướng (b)**: `Invoice.update` giữ bảng đã lưu + cờ khi HĐ `modify`, bỏ tick, `is_vats_from_file = true`, request không gửi vats. Prompt: [[epic-95-cursor-prompt-implement]] § "Phiên 1b".
- Lưu ý QA: "Xem trước" trên form sửa đi `InvoicePreviewService` dựng từ request (không có `adjustment_vats`) → bảng thuế suất trên bản xem trước **tính lại từ dòng hàng**, có thể khác XML. Kiểm tra và báo nếu cần xử lý tiếp.
