---
created: 2026-08-06 09:30
updated: 2026-08-06
status: Done — đã chạy, code đã review
project: "[[10_Projects/sapo-invoice/README]]"
---

# Prompt Cursor — implement issue #125 (cột CCCD file import hóa đơn)

- Plan đầy đủ: [[epic-62-them-cot-cccd-file-import-hoa-don]] · Test case: [[epic-62-test-cases-cccd]]
- Issue: [sapo-invoice-admin-service#125](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-service/-/work_items/125)

> ⚠️ **Prompt này đã chạy xong 06/08/2026.** Luật validate sau đó **đã đổi** so với bản Cursor sinh ra: `^\d{12}$` → **`^0\d{11}$`** (bắt buộc số `0` đầu), chỉ áp cho luồng import. Mục A5 và A8 dưới đây **đã được cập nhật theo luật mới** — nếu chạy lại prompt sẽ ra đúng bản hiện hành. Lý do đổi + hạn chế đã biết: xem mục *"Cập nhật sau khi implement"* trong plan.

Copy toàn bộ phần trong khung dưới đây và dán vào Cursor (mở workspace `/Users/sapo/invoice`).

---

````markdown
# Task: Thêm cột "Căn cước công dân" vào luồng import hóa đơn (BE + FE)

Workspace: `/Users/sapo/invoice` — làm việc trên 2 repo:
- `sapo-invoice-admin-service` (Java 17 / Spring Boot 3.3, Gradle)
- `sapo-invoice-admin-frontend` (React 18 + TS, Vite, pnpm)

Issue gốc: sapo-invoice-admin-service#125 · SRS: `invoice-docs/docs/invoice/them-cot-cccd-file-import-hoa-don/srs.md`

## Đọc trước khi code

1. `/Users/sapo/invoice/AGENTS.md` — routing repo
2. `/Users/sapo/developer-os/10_Projects/sapo-invoice/ai/rules-backend.md` — DDD, multi-tenancy
3. `/Users/sapo/developer-os/10_Projects/sapo-invoice/ai/rules-frontend.md` — RTK Query, useCustomForm
4. `sapo-invoice-admin-service/.claude/rules/sonarqube.md` — giới hạn complexity, logging, exception
5. `sapo-invoice-admin-frontend/.claude/commands/review-code.md` — convention FE (BẮT BUỘC trước khi sửa `.tsx`)

⚠️ `sapo-invoice-admin-service/.claude/CLAUDE.md` ghi "project chạy trên Windows, dùng PowerShell" — **sai với máy này**. Máy này là macOS, repo ở `/Users/sapo/invoice/sapo-invoice-admin-service`, build bằng `./gradlew`.

## Mục tiêu

Thêm 1 cột **"Căn cước công dân"** vào file mẫu import hóa đơn, đặt **giữa "Người mua hàng" và "Số điện thoại"**, ánh xạ → `invoice_buyers.id_number`. Validate: **tùy chọn** (trống → `null`, không lỗi); nếu có nhập → trim rồi phải khớp `^0\d{11}$` (12 chữ số, **bắt buộc bắt đầu bằng `0`**), sai → **lỗi dòng** với message nguyên văn `Căn cước công dân không đúng định dạng`.

## Phạm vi — CHỈ 3 template

| Mã | Case | Enum BE | Asset FE |
|---|---|---|---|
| `AD` | HĐ mới — **tích** "Tự động tính toán…" | `InvoiceHeaderAutomaticallyCalculateImport` | `mau_nhap_hoa_don_DEItyDnc.xlsx` |
| `AI` | HĐ mới — **không tích** | `InvoiceHeaderProactivelyCalculateImport` | `mau_nhap_hoa_don_DEItyDnb.xlsx` |
| `AL` | HĐ thay thế | `InvoiceHeaderReplacementImport` | `mau_nhap_hoa_don_DEItyFna.xlsx` |

## ⛔ TUYỆT ĐỐI KHÔNG ĐỤNG — hóa đơn điều chỉnh (`AR`)

Đang có branch `feature/import-invoice-total` chưa merge sẽ sửa nặng phần này. Sửa vào đây là chắc chắn conflict.

**Không được chạm** các file/hàm sau, kể cả 1 dòng:
- `InvoiceHeaderAdjustmentImport.java`
- `InvoiceImportExcelAdjustmentModel.java`
- `InvoiceImportService.readInvoiceAdjustmentExcelData` (~dòng 3086)
- `InvoiceImportService.validateInvoiceAdjustmentExcelData` (~dòng 2503)
- `InvoiceImportService.generateRequestInvoiceAdjustmentFromExcelData` (~dòng 1190)
- `src/assets/files/mau_nhap_hoa_don_DEItyFnb.xlsx` (FE)

## Nền tảng đã có sẵn — KHÔNG làm lại

- `invoice_buyers.id_number` `varchar(50)` đã tồn tại → **KHÔNG viết migration, KHÔNG chạy ALTER TABLE**
- `InvoiceBuyerRequest.idNumber` đã có sẵn `@Pattern(regexp = "^$|^[0-9]{12}$", message = "Căn cước công dân không đúng định dạng")`
- `Invoice.java` đã truyền `idNumber` qua `create`/`update` → chỉ cần set vào request là dữ liệu tự chảy xuống DB

---

# PHẦN A — Backend (`sapo-invoice-admin-service`)

Branch: `feat/import-invoice-buyer-id-number` (tách từ `master`)

Đường dẫn dưới đây tính từ `src/main/java/vn/sapo/invoice/admin/invoice/`.

## A1. `InvoiceHeaderAutomaticallyCalculateImport.java` (AD) — thay TOÀN BỘ danh sách enum

Đây là bảng đã đối chiếu với file `.xlsx` thật, dùng nguyên văn:

```java
invoice_series("Ký hiệu*", "A1:A3"),
partner_ref_code("Mã chứng từ gốc", "B1:B3"),
// buyer info
buyer_info("Thông tin người mua", "C1:J1"),
buyer_code("Mã khách", "C2:C3"),
buyer_tax_code("Mã số thuế người mua", "D2:D3"),
buyer_legal_name("Tên đơn vị", "E2:E3"),
buyer_address("Địa chỉ", "F2:F3"),
buyer_full_name("Người mua hàng", "G2:G3"),
buyer_id_number("Căn cước công dân", "H2:H3"),
buyer_phone_number("Số điện thoại", "I2:I3"),
buyer_email("Email", "J2:J3"),
// receiver info
receiver_info("Thông tin người nhận", "K1:L1"),
receiver_name("Tên người nhận hóa đơn", "K2:K3"),
receive_email("Email nhận hóa đơn", "L2:L3"),
// transaction info
transaction_info("Thông tin giao dịch", "M1:Q1"),
payment_method_name("Hình thức thanh toán*", "M2:M3"),
buyer_bank_name("Tên ngân hàng", "N2:N3"),
buyer_bank_account("Số tài khoản ngân hàng", "O2:O3"),
currency_code("Loại tiền", "P2:P3"),
exchange_rate("Tỷ giá", "Q2:Q3"),
// discount invoice
discount_invoice("Chiết khấu cả hóa đơn", "R1:S2"),
discount_type_value("Giá trị", "R3"),
discount_type_percent("%", "S3"),

vat_name("Thuế GTGT cả hóa đơn (%)", "T1:T3"),

// item info
item_info("Thông tin hàng hóa, dịch vụ", "U1:AE1"),
item_type("Tính chất", "U2:U3"),
item_code("Mã hàng", "V2:V3"),
item_name("Tên hàng hóa/dịch vụ", "W2:W3"),
item_unit_name("ĐVT", "X2:X3"),
item_quantity("Số lượng", "Y2:Y3"),
item_unit_price("Đơn giá", "Z2:Z3"),
item_discount_item("Chiết khấu/SP", "AA2:AB2"),
item_discount_item_type_value("Giá trị", "AA3"),
item_discount_item_type_percent("%", "AB3"),
item_original_discount_amount("Tiền chiết khấu", "AC2:AC3"),
item_vat_rate_business_group("%Tính thuế", "AD2:AD3"),
item_vat_name("Thuế GTGT (%)", "AE2:AE3");
```

## A2. `InvoiceHeaderProactivelyCalculateImport.java` (AI) và `InvoiceHeaderReplacementImport.java` (AL)

Áp **cùng một quy tắc**, KHÔNG chép bảng của AD sang:

1. Thêm entry `buyer_id_number("Căn cước công dân", "<ô>")` ngay sau `buyer_full_name`
2. Mở rộng merge `buyer_info` thêm 1 cột
3. **Dịch phải +1 mọi cellRange từ `buyer_phone_number` trở đi** (cả ô đơn `Q3` lẫn range `Z2:AA2`)

Neo đã verify:

| Enum | `buyer_info` | `buyer_id_number` | `buyer_phone_number` | `buyer_email` |
|---|---|---|---|---|
| `...ProactivelyCalculateImport` (AI) | `C1:I1` → **`C1:J1`** | **`H2:H3`** | `H2:H3` → `I2:I3` | `I2:I3` → `J2:J3` |
| `...ReplacementImport` (AL) | `F1:L1` → **`F1:M1`** | **`K2:K3`** | `K2:K3` → `L2:L3` | `L2:L3` → `M2:M3` |

**Bắt buộc verify sau khi sửa** — chạy script này và đối chiếu từng entry enum với output:

```bash
cd /Users/sapo/invoice/invoice-docs/docs/invoice/them-cot-cccd-file-import-hoa-don && python3 - <<'PY'
import zipfile
from xml.etree import ElementTree as ET
N='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
for f in ["AD_Hoa_don_HD_moi_Tich_tu_dong_mau_nhap_hoa_don.xlsx",
          "AI_Hoa_don_HD_moi_Khong_Tich_tu_dong_mau_nhap_hoa_don.xlsx",
          "AL_Hoa_don_HD_thay_the_mau_nhap_hoa_don.xlsx"]:
    z=zipfile.ZipFile(f)
    ss=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')):
            ss.append(''.join(t.text or '' for t in si.iter(N+'t')))
    sh=ET.fromstring(z.read(sorted(n for n in z.namelist() if n.startswith('xl/worksheets/sheet'))[0]))
    def val(c):
        if c.get('t')=='inlineStr': return ''.join(x.text or '' for x in c.iter(N+'t'))
        v=c.find(N+'v')
        return '' if v is None else (ss[int(v.text)] if c.get('t')=='s' else v.text or '')
    merges={}
    mc=sh.find(N+'mergeCells')
    if mc is not None:
        for m in mc:
            ref=m.get('ref'); merges[ref.split(':')[0]]=ref
    print("=== ",f)
    for r in sh.find(N+'sheetData'):
        if int(r.get('r'))>3: break
        for c in r:
            t=val(c).strip()
            if t: print(f"   {merges.get(c.get('r'), c.get('r')):<10} {t}")
PY
```

Mọi `cellRange` trong 3 enum phải khớp **chính xác** cột bên trái của output tương ứng.

## A3. Model — 3 file trong `application/model/invoice/invoiceimport/`

`InvoiceImportExcelAutomaticallyCalculateModel`, `InvoiceImportExcelProactiveCalculateModel`, `InvoiceImportExcelReplacementModel`:

1. Thêm `private String buyerIdNumber;` **ngay sau** `buyerFullName`
2. Cập nhật comment chỉ số ở các field phía sau (`// 7`, `// 8`… dịch +1)
3. **Thêm `StringUtils.isNotBlank(buyerIdNumber) ||` vào `hasData()`** — bỏ sót thì dòng chỉ có CCCD bị coi là hết dữ liệu và vòng đọc `break` sớm

## A4. Hàm đọc trong `application/service/invoice/InvoiceImportService.java`

| Hàm | ~Dòng | Chèn | Dịch |
|---|---|---|---|
| `readAutomaticallyCalculateExcelData` | 3205 | `case 7 -> rowModel.setBuyerIdNumber(ExcelUtils.getCellStringValue(cell));` | mọi `case` ≥ 7 cũ → +1 |
| `readProactivelyCalculateExcelData` | 3147 | `case 7 -> ...` | mọi `case` ≥ 7 cũ → +1 |
| `readInvoiceReplacementExcelData` | 3025 | `case 10 -> ...` | mọi `case` ≥ 10 cũ → +1 |

**Sửa từ index LỚN xuống NHỎ** để không đè nhầm. Sau khi sửa, đối chiếu lại từng `case` với thứ tự khai báo trong enum tương ứng — số `case` phải bằng đúng vị trí (0-based) của field trong enum, tính cả các entry header nhóm bị bỏ qua.

## A5. `application/service/invoice/ImportInvoiceValidator.java`

Thêm helper cạnh `validatePhoneNumber` (~dòng 768), cùng style trả `String` lỗi hoặc `null`:

```java
// CCCD: 12 chữ số, bắt buộc bắt đầu bằng số 0. Chỉ áp dụng cho luồng import hóa đơn —
// form tạo hóa đơn vẫn giữ luật cũ ở InvoiceBuyerRequest.idNumber (ngoài phạm vi task này).
private static final Pattern ID_NUMBER_PATTERN = Pattern.compile("^0\\d{11}$");

protected static String validateIdNumber(String idNumber) {
    if (StringUtils.isBlank(idNumber)) {
        return null; // CCCD tùy chọn — để trống không lỗi
    }
    if (!ID_NUMBER_PATTERN.matcher(idNumber.trim()).matches()) {
        return "Căn cước công dân không đúng định dạng";
    }
    return null;
}
```

> Vì sao phải validate tường minh: `InvoiceWriteService` KHÔNG gắn `@Validated`, nên `@Pattern` trên `InvoiceBuyerRequest.idNumber` **không tự chạy** trong luồng import.

## A6. Gọi validate — 3 hàm trong `InvoiceImportService.java`

`validateProactivelyCalculateExcelData` (~1434) · `validateAutomaticallyCalculateExcelData` (~1741) · `validateInvoiceReplacementExcelData` (~2044)

Chèn **ngay sau** block `validatePhoneNumber`, trong vùng `// region validate buyer`:

```java
var idNumberError = validateIdNumber(data.getBuyerIdNumber());
if (idNumberError != null) {
    listFailedInvoices.add(MessageFormat.format(errorKey, data.getRowNumber(), idNumberError));
}
```

Đặt đúng chỗ này để dòng lỗi được gom vào `listFailedInvoices` **trước** đoạn `if (errorSizeBefore < listFailedInvoices.size()) data.setHasError(true);` ở cuối vòng lặp.

## A7. Map vào `InvoiceBuyerRequest` — 3 chỗ trong `InvoiceImportService.java`

| ~Dòng | Hàm bao ngoài | Template |
|---|---|---|
| 582 | `generateRequestProactiveCalculateFromExcelData` | AI |
| 768 | `generateRequestAutomaticallyCalculateFromExcelData` | AD |
| 1091 | `generateRequestInvoiceReplacementFromExcelData` | AL |

Thêm ngay cạnh `setPhoneNumber` / `setEmail`, cùng style guard:

```java
if (StringUtils.isNotBlank(data.getBuyerIdNumber())) {
    buyerRequest.setIdNumber(data.getBuyerIdNumber().trim());
}
```

**Dọn kèm:** ở khoảng dòng 596-601 có block lặp y hệt 2 lần:
```java
if (AnyFieldValidator.isValid(buyerRequest)) {
    invoiceRequest.setBuyer(buyerRequest);
}
```
Xóa 1 bản.

## A8. Unit test `validateIdNumber`

Đặt trong `src/test/java/`, JUnit Jupiter. Các case:

| Input | Kỳ vọng |
|---|---|
| `null`, `""`, `"   "` | `null` (hợp lệ — CCCD tùy chọn) |
| `"001099001234"`, `"012345678901"`, `"096099001234"`, `"099099001234"`, `"000000000000"` | `null` — 12 số, bắt đầu bằng `0` |
| `" 001099001234 "` | `null` (trim) |
| `"101099001234"`, `"112345678901"`, `"704099001234"`, `"840123456789"`, `"999999999999"` | `"Căn cước công dân không đúng định dạng"` — không bắt đầu bằng `0` |
| `"00109900123"` (11 số) | lỗi |
| `"0010990012345"` (13 số) | lỗi |
| `"00109900123a"` | lỗi |
| `"001 099 001234"` (dấu cách ở giữa) | lỗi |
| `"００１０９９００１２３４"` (full-width) | lỗi |
| `"0010-9900-1234"` | lỗi |

Tên method test dùng **camelCase**, không dùng `_` (Sonar S100).

---

# PHẦN B — Frontend (`sapo-invoice-admin-frontend`)

Branch: `feature/import-invoice-cccd-template` (tách từ `master`)

## B1. Thay 3 file mẫu — GIỮ NGUYÊN TÊN FILE

```bash
SRC=/Users/sapo/invoice/invoice-docs/docs/invoice/them-cot-cccd-file-import-hoa-don
DST=/Users/sapo/invoice/sapo-invoice-admin-frontend/src/assets/files

cp "$SRC/AD_Hoa_don_HD_moi_Tich_tu_dong_mau_nhap_hoa_don.xlsx"        "$DST/mau_nhap_hoa_don_DEItyDnc.xlsx"
cp "$SRC/AI_Hoa_don_HD_moi_Khong_Tich_tu_dong_mau_nhap_hoa_don.xlsx"  "$DST/mau_nhap_hoa_don_DEItyDnb.xlsx"
cp "$SRC/AL_Hoa_don_HD_thay_the_mau_nhap_hoa_don.xlsx"                "$DST/mau_nhap_hoa_don_DEItyFna.xlsx"
# KHÔNG copy file AR_... — mẫu hóa đơn điều chỉnh giữ nguyên
```

⚠️ AD/AI rất dễ đảo: `AD` = **tích** tự động = `DEItyDnc`; `AI` = **không tích** = `DEItyDnb`. Copy xong chạy lại script verify ở mục A2 trên chính 3 file trong `src/assets/files/` để chắc chắn không đảo.

Không đổi tên file → không phải sửa các dòng `import ... from "app/assets/files/....xlsx?url"` ở `InvoiceImportModal.tsx:18-21`. Vite tự sinh hash mới.

## B2. Text ngày cập nhật — `src/pages/invoice/components/modal/InvoiceImportModal.tsx`

Trong `StyledLinkDownloadFile` (~dòng 253-264), thêm text **cùng dòng, ngay sau** `<Link>`:

```tsx
{fieldValues.invoiceImportType !== Status.MODIFY ? (
  <StyledUpdatedAt>
    {/* TODO: cập nhật đúng ngày merge master trước khi uplive */}
    <Text as="span" color="subdued">(cập nhật ngày: 06/08/2026)</Text>
  </StyledUpdatedAt>
) : null}
```

- Nguyên văn theo Figma: `(cập nhật ngày: dd/MM/yyyy)` — chữ thường, có dấu `:`, trong ngoặc đơn, màu xám (subdued), **cùng baseline với link**, KHÔNG phải dòng riêng bên dưới.
- `StyledLinkDownloadFile` vốn đã `display: inline-flex` → chỉ cần chèn node + styled wrapper canh baseline khớp `StyledLink` (đang có `padding-top: spacing(2) + 1`).
- Ẩn khi `Status.MODIFY` vì đợt này chưa đổi mẫu hóa đơn điều chỉnh.
- Dùng token màu/size của `@sapo/ui-components`, **không hardcode màu hoặc px**.

## B3. Không đổi gì khác

Giữ nguyên `getDownloadSampleLink` (~dòng 108-127), payload `createJobImportFileInvoice`, toàn bộ bố cục còn lại của popup.

---

# Verify

**Backend**
```bash
cd /Users/sapo/invoice/sapo-invoice-admin-service
./gradlew compileJava
./gradlew test
```

**Frontend**
```bash
cd /Users/sapo/invoice/sapo-invoice-admin-frontend
pnpm lint:fix && pnpm format
pnpm lint      # phải exit 0
pnpm build     # đã bao gồm tsc
```

**Tự rà lại trước khi báo xong**
- [ ] `git diff` ở BE **không** chứa `Adjustment` ở bất kỳ tên file/hàm nào
- [ ] `git status` ở FE cho thấy đúng 3 file `.xlsx` bị đổi, **không có** `DEItyFnb`
- [ ] Mọi `cellRange` trong 3 enum khớp output script verify
- [ ] Số `case` trong 3 hàm `read*ExcelData` khớp thứ tự field trong enum tương ứng
- [ ] `hasData()` của cả 3 model đã có `buyerIdNumber`

# Ràng buộc

- **KHÔNG chạy `git add` / `git commit`** — để nguyên unstaged, tôi tự review rồi tự stage.
- **KHÔNG viết migration**, không chạy SQL.
- Comment code: tiếng Việt cho logic nghiệp vụ, technical term giữ tiếng Anh.
- Không thêm file test nào ngoài unit test `validateIdNumber` ở mục A8.
- Nếu phát hiện chỗ nào lệch so với mô tả trên (số dòng đã trôi, cellRange không khớp file thật) → **dừng lại báo tôi**, không tự suy diễn sửa bừa.
````

---

## Ghi chú khi dùng

- Prompt cố tình **không** yêu cầu Cursor tự tra file `.xlsx` để suy ra cellRange — bảng AD đã verify sẵn, AI/AL cho quy tắc + neo, và bắt chạy script đối chiếu. Đây là chỗ dễ sai nhất của task nên không để agent tự do.
- Nếu Cursor làm hỏng phần dịch cột: cách nhanh nhất để phát hiện là chạy script verify ở mục A2 rồi so từng dòng với enum, không phải đọc diff.
- Ngày `06/08/2026` trong B2 là giá trị tạm — sửa thành ngày merge master thật trước khi lên production.
