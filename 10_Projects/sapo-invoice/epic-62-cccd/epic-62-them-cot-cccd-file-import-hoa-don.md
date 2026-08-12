---
created: 2026-08-05 17:00
updated: 2026-08-06
status: Implemented — chờ QA
project: "[[10_Projects/sapo-invoice/README]]"
---

# WI #62 — Thêm cột CCCD vào file dữ liệu mẫu import hóa đơn đầu ra

- Work item: [invoice-docs#62](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/work_items/62) (type `ISSUE`, label `module::hoa-don-dau-ra`, assignee hiện tại: duynd7 + quynhctd2)
- SRS: `invoice-docs/docs/invoice/them-cot-cccd-file-import-hoa-don/srs.md` (v0.1, 2026-07-21, BA Mary) + 4 file `.xlsx` đính kèm
- Figma: https://www.figma.com/design/7t7C9XzNP3nBJpBismG9zS/SAPO-E-INVOICE?node-id=34591-255426
- Repo tác động: `sapo-invoice-admin-service` (parser/validate) + `sapo-invoice-admin-frontend` (file mẫu + UI)
- Child issue tạo ở project `sapo-invoice-admin-service` (convention chung).
- Tài liệu liên quan: [[epic-62-cursor-prompt-implement]] (prompt đã dùng để code) · [[epic-62-test-cases-cccd]] (ma trận test cho QA)

## Yêu cầu tóm tắt

Thêm 1 cột **"Căn cước công dân"** vào file mẫu import hóa đơn, đặt **giữa "Người mua hàng" và "Số điện thoại"**, map → `invoice_buyers.id_number`. Validate: **tùy chọn**, nếu nhập phải khớp **`^0\d{11}$`** (12 chữ số, **bắt buộc bắt đầu bằng `0`** — siết so với SRS, xem [[#Cập nhật sau khi implement (06/08/2026)]]), sai → lỗi dòng *"Căn cước công dân không đúng định dạng"*. Áp cho cả 2 phân hệ **Hóa đơn** và **HĐ từ máy tính tiền**. Thêm text **"Cập nhật ngày dd/MM/yyyy"** cạnh nút tải file mẫu (yêu cầu bổ sung nằm ở mô tả work item + Figma, **không có trong SRS**).

## ✅ Quyết định phạm vi (2026-08-05)

**Hóa đơn điều chỉnh (`AR`) tạm PENDING — chờ `feature/import-invoice-total` xong mới làm.**

| Đợt | Template | Trạng thái |
|---|---|---|
| **Đợt 1 — làm ngay** | `AD` (HĐ mới, tích) · `AI` (HĐ mới, không tích) · `AL` (HĐ thay thế) | Sẵn sàng code, file mẫu BA đã giao đủ và đã verify khớp |
| **Đợt 2 — sau** | `AR` (HĐ điều chỉnh) — cả 2 biến thể tích / bỏ tích | Chờ `feature/import-invoice-total` merge + BA giao thêm file mẫu "AR-tích + CCCD" |

Cách tách này chạy được vì `validateImportFile` so header **theo từng template độc lập** — 3 template mới có cột CCCD, `AR` giữ nguyên bản cũ, hai bên không ảnh hưởng nhau. Đợt 1 **không đụng** `InvoiceHeaderAdjustmentImport`, `readInvoiceAdjustmentExcelData` (dòng 3086), `validateInvoiceAdjustmentExcelData` (dòng 2503), `generateRequestInvoiceAdjustmentFromExcelData` (dòng 1190) → khi merge `feature/import-invoice-total` sẽ **không có conflict** ở nhánh điều chỉnh.

⚠️ Hệ quả cần lưu ý ở FE: text "Cập nhật ngày dd/MM/yyyy" là **text dùng chung** cho cả 3 lựa chọn Loại file nhập, trong khi đợt 1 chỉ đổi mẫu HĐ mới + thay thế. Chọn 1 trong 2: (a) chấp nhận hiển thị chung, (b) chỉ hiện text khi Loại file nhập ≠ "Hóa đơn điều chỉnh". Cần hỏi BA — xem Q4.

---

## Trạng thái code hiện tại (đã verify, KHÔNG phải giả định)

### Nền tảng đã sẵn — phần dễ hơn SRS mô tả

| Điểm | Trạng thái |
|---|---|
| `invoice_buyers.id_number` | Đã tồn tại. `InvoiceBuyer.java:51` có field `idNumber`; `Invoice.java:865,867` đã truyền qua `create`/`update`. **Không cần migration.** |
| `InvoiceBuyerRequest.idNumber` | **Đã có sẵn**, kèm đúng regex và đúng message SRS yêu cầu:<br>`@Pattern(regexp = "^$\|^[0-9]{12}$", message = "Căn cước công dân không đúng định dạng")` |
| Đồng bộ ngược danh mục KH | `InvoiceImportService` **không hề gọi customer service** (grep `customer` → 0 hit) — buyer dựng thuần từ file. UC-01 AC7 đã đúng sẵn, không cần code. |
| Popup import dùng chung 2 phân hệ | `InvoiceListPage.tsx:59` phân biệt MTT bằng `pathname.includes("invoice-calculating-machines")`, cùng render `InvoiceImportModal`. **1 chỗ sửa FE là đủ cho cả 2 module.** |
| CCCD lên CQT | `InvoicePublishService.java:1322,1325` đã map `buyer.getIdNumber()` → `CMND` / `CCCDan` trong thông điệp. CCCD nhập qua file **sẽ tự động lên XML khi phát hành**. |
| Case dùng thật | `InvoiceCommonService.java:661` — HĐ **bán hàng dự trữ quốc gia** (mẫu 4) bắt buộc `taxCode` hoặc `idNumber`. Hiện import không truyền được `idNumber` → mẫu 4 + người mua không MST **đang không import được**. Tính năng này gỡ bỏ nút thắt đó. |

### Nơi file mẫu thực sự nằm — **frontend, không phải backend**

4 file static asset trong `sapo-invoice-admin-frontend/src/assets/files/`, import trực tiếp bằng `?url` tại `pages/invoice/components/modal/InvoiceImportModal.tsx:18-21`:

| Mã SRS | Case | File FE | Enum BE |
|---|---|---|---|
| **AD** | HĐ mới — **tích** tự động | `mau_nhap_hoa_don_DEItyDnc.xlsx` | `InvoiceHeaderAutomaticallyCalculateImport` |
| **AI** | HĐ mới — **không tích** | `mau_nhap_hoa_don_DEItyDnb.xlsx` | `InvoiceHeaderProactivelyCalculateImport` |
| **AL** | HĐ thay thế | `mau_nhap_hoa_don_DEItyFna.xlsx` | `InvoiceHeaderReplacementImport` |
| **AR** | HĐ điều chỉnh | `mau_nhap_hoa_don_DEItyFnb.xlsx` | `InvoiceHeaderAdjustmentImport` |

> **Đính chính SRS:** SRS ghi *"tên file tải về `..._mau_nhap_hoa_don_<mã>.xlsx`, `<mã>` do hệ thống tự sinh mỗi lần tải"*. Thực tế `<mã>` là **content hash của Vite lúc build** (vd `-CbZhv3sZ`), cố định theo bản build, **không đổi theo lượt tải**. Không có logic sinh mã nào cả.

### Luồng parse + validate ở BE (`InvoiceImportService.java`, 3464 dòng)

```
POST /api/invoices/import → RabbitMQ (ImportFileInvoiceConsumer) → InvoiceImportService
  1. validateImportFile()            (dòng 3259) — so header thực tế vs enum theo cellRange → "File nhập không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán và thực hiện tải lại file mẫu."
  2. readXxxExcelData()              (dòng 3025 / 3086 / 3147 / 3205) — switch theo CHỈ SỐ CỘT
  3. validateXxxExcelData()          (dòng 1434 / 1741 / 2044 / 2503) — validate từng dòng, gom vào listFailedInvoices
  4. generateRequest... → dựng InvoiceBuyerRequest (dòng ~582 / 768 / 1091 / 1335)
  5. invoiceWriteService.create(...) → HĐ nháp (status=initialized, publishStatus=draft)
  6. Email báo cáo: "Hàng {n}: {lý do}"
```

**Hai điểm kỹ thuật quyết định cách implement:**

1. **`@Pattern` trên `InvoiceBuyerRequest.idNumber` KHÔNG tự chạy trong luồng import.** `InvoiceWriteService` không gắn `@Validated`, `invoiceWriteService.create(...)` là gọi service thường → bean validation không kích hoạt. Phải validate **tường minh** trong `validateXxxExcelData`, đúng pattern email/phone đang dùng (`validatePhoneNumber` tại `ImportInvoiceValidator.java:768`).

2. **`ExcelUtils.getCellStringValue` (dòng 46-68) làm mất số 0 đầu với ô kiểu NUMERIC:**
   ```java
   BigDecimal bd = BigDecimal.valueOf(cell.getNumericCellValue()).setScale(6, HALF_UP);
   return bd.stripTrailingZeros().toPlainString();
   ```
   → xem Q2.

---

## 🚩 Xung đột với `feature/import-invoice-total` — lý do hoãn `AR`

Đây là phát hiện dẫn tới quyết định tách đợt ở trên. **File mẫu AR do BA giao KHÔNG khớp với code master.**

Đã dump XML của cả 2 file để đối chiếu:

| File | Khối "Tổng tiền hóa đơn" | Kết luận |
|---|---|---|
| `nhap-tong-tien-hoa-don-theo-file/mau_nhap_hoa_don.xlsx` | merge `AM1:AR1` | Template của feature import tổng tiền, **chưa có CCCD** |
| `them-cot-cccd.../AR_...xlsx` (BA giao cho task này) | merge **`AN1:AS1`** | = template trên **+ CCCD tại K** (dịch phải +1) |
| Enum `InvoiceHeaderAdjustmentImport` trên **master** | **không có khối tổng** | Master không biết cột AM–AR |

Branch `origin/feature/import-invoice-total` (chưa merge) thêm enum thứ **5** — `InvoiceHeaderAdjustmentProactivelyCalculateImport` (khối tổng `AM1:AR1`) — và đổi `validateImportFile` chọn template HĐ điều chỉnh theo checkbox:

```java
if (request.isAutomaticallyCalculate()) → InvoiceHeaderAdjustmentImport                  // tích: template thường
else                                    → InvoiceHeaderAdjustmentProactivelyCalculateImport // bỏ tích: có khối tổng
```
Branch đó cũng siết header check thành `actualHeaders.size() != expectedHeaders.size()` → **thừa cột cũng chặn**.

**Ba hệ quả:**

1. Nếu làm CCCD cho `AR` trên master trước khi import-tổng-tiền merge → dùng file `AR_...xlsx` của BA sẽ **luôn báo "File nhập không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán và thực hiện tải lại file mẫu."**.
2. Sau khi import-tổng-tiền lên, hệ thống có **5 template**, không phải 4: AD, AI, AL, **AR-tích** (không khối tổng), **AR-bỏ-tích** (có khối tổng).
3. **BA mới giao 4 file — thiếu template "AR-tích tự động + CCCD".** Phải yêu cầu bổ sung ở đợt 2, nếu không nhánh tích tự động của HĐ điều chỉnh sẽ không import được sau khi đổi.

→ **Đã xử lý bằng cách hoãn `AR` sang đợt 2** (xem mục Quyết định phạm vi). Đợt 1 chỉ đụng AD/AI/AL nên không vướng gì.

---

## Câu hỏi cần chốt trước khi code

### Q1 — Thứ tự release với feature import tổng tiền ✅ ĐÃ CHỐT (2026-08-05)
**Hoãn `AR`, chờ `feature/import-invoice-total` xong mới làm.** Đợt 1 chỉ làm AD/AI/AL.

Còn lại cho **đợt 2** (chưa cần trả lời bây giờ): yêu cầu BA bổ sung **file mẫu thứ 5** (AR — tích tự động tính tổng tiền, có cột CCCD tại K, **không** có khối `AM–AR`) + cập nhật §6.2 SRS từ 4 → 5 file. **Không tự chế file Excel thay BA** — sai 1 ô merge là hỏng cả luồng import.

### Q2 — "Giữ số 0 đầu" nghĩa là gì ✅ ĐÃ CHỐT (2026-08-05)

**Bối cảnh:** CCCD VN luôn bắt đầu bằng `0` — 3 số đầu là mã tỉnh, chạy `001`–`096` (vd `001099001234` = Hà Nội). Yêu cầu "giữ số 0 đầu" **không nói về validate**, mà nói về việc **Excel phá dữ liệu trước khi file tới server**:

| Định dạng ô | User gõ `001099001234` | File `.xlsx` thực sự chứa |
|---|---|---|
| **Text (`@`)** | giữ nguyên chuỗi | `"001099001234"` ✅ |
| **General / Number** | Excel hiểu là **số** | `1099001234` — 2 số 0 bị vứt **ngay lúc gõ** ❌ |

Khác với form web (browser giữ nguyên chuỗi user gõ, server validate sau), ở đây **Excel chính là "browser"** và đã chuẩn hoá dữ liệu trước khi ghi file. Server chỉ nhận file đã ghi → không còn bản gốc để đọc. Đọc kiểu chuỗi hay kiểu số cũng như nhau.

**Đính chính (so với bản plan đầu):** AC4 **không** bất khả thi hoàn toàn. Tách 2 nửa:
1. *"đọc ra chuỗi, không dùng scientific notation"* → **code hiện tại đã đạt** (`ExcelUtils.getCellStringValue` dùng `toPlainString()`). Không cần sửa gì.
2. *"khôi phục số 0 đã bị Excel cắt"* → không làm được.

**Phía template BA đã xử lý đúng** (đã dump XML kiểm): cột CCCD `H` (AD/AI) và `K` (AL/AR) đều có `numFmt = @ (Text)` trên vùng dữ liệu, ô mẫu dòng 4 = `001099001234` lưu dạng `inlineStr`. → Luồng bình thường (tải mẫu về, gõ vào) **không mất số 0**. SRS không cần sửa.

**Chốt:** khi user tự phá định dạng (paste đè / xoá format / tự dựng lại file) làm ô thành kiểu số → **báo lỗi** *"Căn cước công dân không đúng định dạng"*, **KHÔNG tự pad `0`**.
> Lý do quyết định (mạnh hơn lý do "bịa dữ liệu"): nếu pad `0` cho đủ 12 thì **mọi** số ≤ 12 chữ số đều thành hợp lệ — gõ thiếu 1 số (`00109900123` → `109900123` → pad → `000109900123`) cũng qua. Tức quy tắc "đúng 12 chữ số" **mất tác dụng hoàn toàn** với ô kiểu số, mà CCCD sai đi thẳng lên thông điệp CQT (`InvoicePublishService:1325`).

### Q3 — Phạm vi validate & giá trị lấy vào hóa đơn ✅ ĐÃ CHỐT (2026-08-05)

**Validate mọi dòng có giá trị CCCD (nhất quán với email/SĐT hiện tại); giá trị ghi vào hóa đơn lấy ở dòng đầu tiên của hóa đơn đó.**

Vì sao không "lấy tất cả CCCD": CCCD là trường **cấp hóa đơn** — 1 hóa đơn có đúng 1 người mua (1 bản ghi `invoice_buyers`) → màn chi tiết hóa đơn chỉ có **1 ô "Căn cước công dân"**. Hóa đơn 3 dòng hàng chiếm 3 dòng Excel, nhưng mọi cột cấp-hóa-đơn (Mã khách, MST, Tên đơn vị, Địa chỉ, Người mua hàng, SĐT, Email, CCCD) chỉ được đọc ở **dòng mở đầu hóa đơn** — code nhận biết bằng cột "Ký hiệu*" có giá trị (dòng 533). Không cần code thêm gì, hành vi này có sẵn.

⚠️ Hệ quả cần biết — xem mục "Rủi ro" và "Issue 6".

### Q7 — Cột "Số hộ chiếu" ✅ ĐÃ CHỐT (2026-08-05)
**Không thêm ở đợt này.** Phạm vi task chỉ có CCCD. `passport_id` để lại cho yêu cầu khác.

### Q4 — Text "cập nhật ngày" ✅ Chốt **cách làm** ngày 05/08/2026 · ⏳ **con số ngày CHƯA chốt**

> Nhãn "(2026-08-05)" ở các câu hỏi là **ngày ra quyết định**, không phải giá trị được chốt. Riêng Q4 nội dung chính lại là một ngày tháng nên ghi tách ra cho rõ: *nguyên tắc* đã chốt, *ngày hiển thị* thì chưa — xem mục "Ngày uplive lấy từ đâu" bên dưới.

Yêu cầu này **chỉ có ở mô tả work item + Figma, không có trong SRS** (SRS §6.1 ghi "không thay đổi bố cục popup").

**Đã đọc node Figma** [34591-255426](https://www.figma.com/design/7t7C9XzNP3nBJpBismG9zS/SAPO-E-INVOICE?node-id=34591-255426) — spec chính xác:

```
Tải dữ liệu mẫu:
⤓ Tải file dữ liệu mẫu (cập nhật ngày: dd/MM/yyyy)
   └─ link xanh ────────┘ └─ text xám, CÙNG DÒNG ─┘
```

- Nguyên văn: **`(cập nhật ngày: dd/MM/yyyy)`** — chữ thường, có dấu hai chấm, bọc trong ngoặc đơn.
- Vị trí: **cùng dòng, ngay sau link** "Tải file dữ liệu mẫu" — **không** phải dòng riêng bên dưới.
- Style: chữ xám (subdued), cỡ nhỏ hơn link, cùng baseline.
- Phần còn lại của popup **giữ nguyên 100%** so với bản đang chạy.

**Chốt:**
- Ngày = **ngày uplive chức năng** (production), hardcode trong FE.
- **Ẩn text khi chọn "Hóa đơn điều chỉnh"** — đợt 1 chưa đổi mẫu `AR`. Sang đợt 2 (làm xong HĐ điều chỉnh) thì **mở lại**.
- Không thêm banner cảnh báo nào khác ngoài text này.

#### Ngày uplive lấy từ đâu — 4 phương án đã cân nhắc

Ràng buộc: **ngày uplive = ngày đẩy code lên `master`**, chưa biết lúc dev code. CI của FE **chỉ build trên `master`/`dev`** (`.gitlab-ci.yml:84-86`) → merge master = build = uplive, không có bước deploy riêng.

| # | Phương án | Kết luận |
|---|---|---|
| **A** | **Hằng số trong code + bước bắt buộc trước khi merge** | ✅ **Đề xuất** |
| B | Inject ngày build qua Vite `define` | ❌ Loại |
| C | Lưu DB / Spring Cloud Config, BE trả qua API | ❌ Loại |
| D | Nhúng ngày vào tên file asset | ⚠️ Có tiền lệ nhưng không giải được bài toán |

**A — Fix cứng ngày tạm + comment TODO tại chỗ ✅ ĐÃ CHỐT (05/08/2026)**

Không dựng hằng số riêng, không thêm file. Ghi thẳng ngày vào JSX kèm `// TODO`:

```tsx
{/* TODO: cập nhật đúng ngày merge master trước khi uplive */}
<Text as="span" color="subdued">(cập nhật ngày: 06/08/2026)</Text>
```

- Sửa 1 dòng rồi merge master là ra đúng bản — **không cần deploy thêm lần nào**, vì CI build ngay khi merge.
- Giá trị tạm nên đặt = **ngày uplive dự kiến**, không phải ngày bừa → nếu lỡ quên thì cùng lắm lệch vài ngày, không hiển thị dữ liệu vô nghĩa.
- `// TODO` không vướng lint: repo đã có sẵn nhiều chỗ dùng (`src/types/tenant.ts:69`, `src/components/SettingColumn/SettingColumn.tsx:79`…).

> ⚠️ **Đánh đổi đã biết và chấp nhận:** ngày fix cứng trông hợp lệ nên **nếu quên sửa thì không có gì trông hỏng** — QA thấy một ngày bình thường và cho pass. Bù lại bằng 2 lớp rẻ tiền: (1) mục "Trước khi merge master" trong checklist cuối tài liệu này, (2) test case #13 yêu cầu đối chiếu ngày hiển thị với ngày merge thật. Mức thiệt hại nếu lọt: thấp — sai vài ngày, không ảnh hưởng nghiệp vụ import.

**B — Vite `define` ngày build: LOẠI**
Khả thi kỹ thuật (`vite.config.ts` đã dùng `defineConfig(({ mode }) => ...)`, thêm `define` là xong) và ngày build ≈ ngày merge vì CI chỉ chạy trên master. Nhưng **mọi lần build master sau đó** (fix bug màn khác, hotfix) đều đẩy ngày lên trong khi file mẫu không đổi → **text nói dối**. Ngữ nghĩa đúng là "ngày **file mẫu** đổi", không phải "ngày **app** build".

**C — Lưu DB/config + API: LOẠI**
Lợi ích duy nhất là "đổi ngày không cần deploy FE", nhưng file mẫu là **static asset trong bundle FE** → đổi mẫu bắt buộc deploy FE, nên lợi ích đó vô dụng. Đổi lại: tách nguồn sự thật làm 2 chỗ (file ở FE, ngày ở DB) → có thể lệch; thêm endpoint + bảng/config + cache cho 1 dòng text là không tương xứng.

**D — Ngày trong tên file asset: có tiền lệ nhưng không gỡ được nút thắt**
`invoice-app` đang làm vậy: `sapo_mau_nhap_san_pham_tren_hoa_don_30122025.xlsx` / `_31122025.xlsx` / `_17032025.xlsx`. Ưu: ngày dính chặt vào file, không thể lệch, giữ được lịch sử các bản mẫu. Nhược: **vẫn phải chốt ngày lúc đặt tên file** — đúng bài toán cũ — cộng thêm sửa 4 dòng import và đổi tên file user tải về (SRS đang mô tả dạng `..._mau_nhap_hoa_don_<mã>.xlsx`).

#### ⭐ Hướng gỡ tận gốc — nên hỏi BA trước khi chọn A

Text này tồn tại để user biết *"mẫu đã đổi rồi, tải lại đi"*. Nếu đúng mục đích đó thì dùng **ngày phát hành mẫu do BA chốt** (ngày BA giao file / duyệt SRS) là đủ, và **biết ngay từ bây giờ** — hết phải chờ lịch release, hết rủi ro quên. Chênh vài ngày so với ngày uplive không thay đổi gì việc user hiểu "bản này mới hơn cái tôi đang cầm".

→ **Hỏi BA:** ngày hiển thị bắt buộc phải là ngày uplive production, hay ngày phát hành mẫu là được? Nếu ngày phát hành mẫu OK → điền luôn, bỏ được cả phương án A. Nếu bắt buộc uplive → dùng A.

### Q5 — CCCD import xong sẽ lên thông điệp CQT — có nằm trong test scope không?
SRS §1 ghi *"chỉ theo lên thông điệp CQT sau khi ký & gửi (ngoài phạm vi bản này)"*, nhưng thực tế **không cần code gì thêm, nó tự lên** qua `InvoicePublishService:1322-1325`. Đề nghị BA/QA bổ sung ít nhất **1 test case E2E**: import CCCD → phát hành → kiểm `CCCDan` trong XML gửi CQT. Đây là dữ liệu pháp lý, không nên bỏ trắng.

### Q6 — Chỉ chấp nhận đúng 12 chữ số: có khách nào còn dùng CMND 9 số?
Code publish map cả nhãn `CMND` lẫn `CCCDan` từ cùng field. Regex `^[0-9]{12}$` trên `InvoiceBuyerRequest` nghĩa là **form tạo HĐ hiện tại cũng đã chặn 9 số** → import giữ nguyên là nhất quán. Xác nhận với BA rằng đây là chủ ý (không hỗ trợ CMND cũ), để QA không raise bug.

> ⚠️ **Đã thay đổi 06/08/2026:** import siết thêm thành `^0\d{11}$`, form **giữ nguyên** `^[0-9]{12}$` → hai đường nhập **không còn nhất quán**. Đây là lệch có chủ đích, xem mục cập nhật cuối tài liệu.

### Q8 — Có thêm test chống lệch cột không?
Rủi ro lớn nhất của task này là **lệch chỉ số cột** giữa file Excel (do BA làm) và enum/switch (do dev làm) — sai 1 index là toàn bộ dữ liệu lệch trường mà **không** báo lỗi (header vẫn khớp). Đề xuất copy 5 file mẫu vào `src/test/resources/` và viết unit test đọc file thật, assert từng header khớp `cellRange` của enum. Xem Issue 3.

---

## Đề xuất chia issue

### Đợt 1 — HĐ mới + HĐ thay thế (làm ngay)

**Gộp BE + FE + test vào 1 issue duy nhất** (quyết định 05/08/2026) — vì hai bên bắt buộc lên cùng lúc, tách ra dễ bị đóng lệch nhau.

| # | Tiêu đề | Project tạo issue | Ước lượng |
|---|---|---|---|
| **1** | [`[SI] Import hóa đơn: thêm cột Căn cước công dân (HĐ mới, HĐ thay thế)` — **#125**](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-service/-/work_items/125) | `sapo-invoice-admin-service` | ~1.5–2 ngày (BE + FE) |

> ✅ **Đã tạo 06/08/2026** — issue [#125](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-service/-/work_items/125), label `module::hoa-don-dau-ra`, assign `duynd7` + `quynhctd2`, đã link `relates_to` về [invoice-docs#62](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/work_items/62).

Nội dung issue = mục "Issue 1" (backend, B1–B6) + "Issue 2" (frontend) + "Issue 3" (test chống lệch cột, gấp thành 1 mục nhỏ "khuyến nghị, làm nếu kịp") của tài liệu này.

- Label: `module::hoa-don-dau-ra` · Link về [invoice-docs#62](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/work_items/62)
- 2 nhánh, 2 MR: BE `feat/import-invoice-buyer-id-number` · FE `feature/import-invoice-cccd-template`
- **Ràng buộc release ghi thẳng trong issue:** file mẫu mới mà parser cũ → chặn hết; parser mới mà file mẫu cũ → cũng chặn hết → BE và FE merge master cùng lúc.

### Đợt 2 — HĐ điều chỉnh (PENDING, chờ `feature/import-invoice-total`)

| # | Tiêu đề | Repo | Ước lượng | Phụ thuộc |
|---|---|---|---|---|
| **4** | *(BA)* Giao file mẫu "AR-tích tự động + CCCD" + cập nhật SRS §6.2 từ 4 → 5 file | invoice-docs | — | sau import-tổng-tiền |
| **5** | [SI][BE+FE] Thêm cột CCCD cho 2 template HĐ điều chỉnh | cả 2 repo | ~0.5–1 ngày | #4, #1 |

Đợt 2 làm lại đúng các bước B1–B6 của Issue 1 nhưng cho `InvoiceHeaderAdjustmentImport` + `InvoiceHeaderAdjustmentProactivelyCalculateImport`, cộng thêm asset FE thứ 5 và nhánh mới trong `getDownloadSampleLink`.

---

## Issue 1 — [BE] Parse + validate + map cột CCCD (AD / AI / AL)

Tất cả đường dẫn dưới đây tính từ `src/main/java/vn/sapo/invoice/admin/invoice/`.
**Không đụng bất kỳ file/hàm nào của nhánh HĐ điều chỉnh** — để đợt 2 và để tránh conflict với `feature/import-invoice-total`.

### B1. Header enum — thêm cột + dịch cellRange (`application/model/invoice/invoiceimport/`)

Với mỗi enum: thêm `buyer_id_number("Căn cước công dân", "<ô>")` ngay sau `buyer_full_name`, mở rộng merge `buyer_info` thêm 1 cột, **dịch phải +1 mọi cellRange từ `buyer_phone_number` trở đi**.

| Enum | `buyer_info` | CCCD | Cột cuối sau dịch | Đợt |
|---|---|---|---|---|
| `InvoiceHeaderAutomaticallyCalculateImport` (AD) | `C1:I1` → **`C1:J1`** | `H2:H3` | `AD2:AD3` → `AE2:AE3` | **1** |
| `InvoiceHeaderProactivelyCalculateImport` (AI) | `C1:I1` → **`C1:J1`** | `H2:H3` | … → `AJ` | **1** |
| `InvoiceHeaderReplacementImport` (AL) | `F1:L1` → **`F1:M1`** | `K2:K3` | `AL2:AL3` → `AM2:AM3` | **1** |
| ~~`InvoiceHeaderAdjustmentImport` (AR-tích)~~ | `F1:L1` → `F1:M1` | `K2:K3` | — | 2 |
| ~~`InvoiceHeaderAdjustmentProactivelyCalculateImport` (AR-bỏ tích)~~ | `F1:L1` → `F1:M1` | `K2:K3` | khối tổng `AM1:AR1` → `AN1:AS1` | 2 |

Đã **verify khớp với file BA giao** (dump XML): AD/AI có `C1` + `H2`="Căn cước công dân" + `J2`="Email"; AL có `F1` + `K2` + `M2`="Email". ✅

### B2. Model — thêm field (`application/model/invoice/invoiceimport/InvoiceImportExcel*Model.java`)

3 model của đợt 1: `InvoiceImportExcelAutomaticallyCalculateModel`, `InvoiceImportExcelProactiveCalculateModel`, `InvoiceImportExcelReplacementModel`.
Mỗi model: thêm `private String buyerIdNumber;` ngay sau `buyerFullName`, cập nhật comment chỉ số, **và thêm vào `hasData()`** (bỏ sót → dòng chỉ có CCCD bị coi là hết dữ liệu và `break` vòng đọc).
*(`InvoiceImportExcelAdjustmentModel` để đợt 2.)*

### B3. Hàm đọc — chèn case + dịch index (**chỗ dễ sai nhất**)

| Hàm | Dòng | Chèn `case` | Dịch +1 | Đợt |
|---|---|---|---|---|
| `readInvoiceReplacementExcelData` | 3025 | `case 10 -> setBuyerIdNumber(...)` | mọi case ≥ 10 cũ | **1** |
| `readProactivelyCalculateExcelData` | 3147 | `case 7` | mọi case ≥ 7 cũ | **1** |
| `readAutomaticallyCalculateExcelData` | 3205 | `case 7` | mọi case ≥ 7 cũ | **1** |
| ~~`readInvoiceAdjustmentExcelData`~~ | 3086 | `case 10` | mọi case ≥ 10 cũ | 2 |

Làm **từ index lớn xuống nhỏ** để không đè nhầm. Sau khi sửa, đối chiếu lại từng case với thứ tự enum tương ứng.

### B4. Validator (`application/service/invoice/ImportInvoiceValidator.java`)

Thêm helper cạnh `validatePhoneNumber` (dòng 768), cùng style trả `String` lỗi hoặc `null`:

```java
// CCCD: 12 chữ số, bắt buộc bắt đầu bằng số 0. Chỉ áp dụng cho luồng import hóa đơn —
// form tạo hóa đơn vẫn giữ luật cũ ở InvoiceBuyerRequest.idNumber (ngoài phạm vi task này).
private static final Pattern ID_NUMBER_PATTERN = Pattern.compile("^0\\d{11}$");

protected static String validateIdNumber(String idNumber) {
    if (StringUtils.isBlank(idNumber)) {
        return null; // CCCD là tùy chọn — để trống không lỗi
    }
    if (!ID_NUMBER_PATTERN.matcher(idNumber.trim()).matches()) {
        return "Căn cước công dân không đúng định dạng";
    }
    return null;
}
```

### B5. Gọi validate trong 3 hàm validate dữ liệu

`validateProactivelyCalculateExcelData` (1434), `validateAutomaticallyCalculateExcelData` (1741), `validateInvoiceReplacementExcelData` (2044) — thêm ngay sau block `validatePhoneNumber` (vd dòng 1501-1504), trong `// region validate buyer`.
*(`validateInvoiceAdjustmentExcelData` (2503) để đợt 2.)*

```java
var idNumberError = validateIdNumber(data.getBuyerIdNumber());
if (idNumberError != null) {
    listFailedInvoices.add(MessageFormat.format(errorKey, data.getRowNumber(), idNumberError));
}
```

### B6. Map vào `InvoiceBuyerRequest` — 3 chỗ của đợt 1

| Dòng | Hàm bao ngoài | Template | Đợt |
|---|---|---|---|
| ~582 | `generateRequestProactiveCalculateFromExcelData` (506) | AI | **1** |
| ~768 | `generateRequestAutomaticallyCalculateFromExcelData` (671) | AD | **1** |
| ~1091 | `generateRequestInvoiceReplacementFromExcelData` (943) | AL | **1** |
| ~~~1335~~ | `generateRequestInvoiceAdjustmentFromExcelData` (1190) | AR | 2 |

```java
if (StringUtils.isNotBlank(data.getBuyerIdNumber())) {
    buyerRequest.setIdNumber(data.getBuyerIdNumber().trim());
}
```
Đặt cạnh `setPhoneNumber` / `setEmail` (cùng style guard `isNotBlank`). Trống → không set → `id_number = null`. ✅ UC-02 AC1.

> **Dọn kèm:** dòng 596-601 có block `if (AnyFieldValidator.isValid(buyerRequest)) { invoiceRequest.setBuyer(buyerRequest); }` **lặp y hệt 2 lần**. Xóa 1 bản khi sửa tới đó.

### B7. Không có migration
`invoice_buyers.id_number` `varchar(50)` đã tồn tại. **Không chạy ALTER TABLE nào.**
(Lưu ý chung của dự án: `ddl-auto = none`, mọi thay đổi schema đều phải chạy tay — nhưng task này không cần.)

---

## Issue 2 — [FE] File mẫu mới (AD/AI/AL) + text ngày cập nhật

Repo `sapo-invoice-admin-frontend`.

1. Copy **3** file `.xlsx` từ `invoice-docs/docs/invoice/them-cot-cccd-file-import-hoa-don/` đè lên `src/assets/files/`, **giữ nguyên tên file cũ** → không phải sửa import ở `InvoiceImportModal.tsx:18-21`. Vite tự sinh hash mới.

   | File BA giao | Đè lên | Biến trong modal |
   |---|---|---|
   | `AD_..._Tich_tu_dong_...xlsx` | `mau_nhap_hoa_don_DEItyDnc.xlsx` | `importInvoiceAutomaticallyCalculateURL` |
   | `AI_..._Khong_Tich_tu_dong_...xlsx` | `mau_nhap_hoa_don_DEItyDnb.xlsx` | `importInvoiceProactivelyCalculateURL` |
   | `AL_..._thay_the_...xlsx` | `mau_nhap_hoa_don_DEItyFna.xlsx` | `importInvoiceReplacementSampleURL` |
   | ~~`AR_..._dieu_chinh_...xlsx`~~ | ~~`mau_nhap_hoa_don_DEItyFnb.xlsx`~~ | **KHÔNG đè — để đợt 2** |

   **Cẩn thận AD/AI dễ đảo:** `Automatically` = tích = `Dnc`, `Proactively` = không tích = `Dnb`.

2. `pages/invoice/components/modal/InvoiceImportModal.tsx` — thêm text `(cập nhật ngày: dd/MM/yyyy)` **cùng dòng, ngay sau** `<Link>` trong `StyledLinkDownloadFile` (dòng 253-264). `StyledLinkDownloadFile` vốn đã là `display: inline-flex` nên chỉ cần chèn thêm node, canh baseline khớp `StyledLink` (đang có `padding-top: spacing(2) + 1`).

   ```tsx
   <StyledLinkDownloadFile>
     <Icon source={DownloadIcon} color="interactive" />
     <StyledLink>
       <Link removeUnderline external url={...}>Tải file dữ liệu mẫu</Link>
     </StyledLink>
     {fieldValues.invoiceImportType !== Status.MODIFY ? (
       <StyledUpdatedAt>
         {/* TODO: cập nhật đúng ngày merge master trước khi uplive */}
         <Text as="span" color="subdued">(cập nhật ngày: 06/08/2026)</Text>
       </StyledUpdatedAt>
     ) : null}
   </StyledLinkDownloadFile>
   ```

   - Nguyên văn theo Figma: **`(cập nhật ngày: dd/MM/yyyy)`** — chữ thường, có dấu `:`, trong ngoặc đơn, màu xám.
   - **Ẩn khi chọn "Hóa đơn điều chỉnh"** (`Status.MODIFY`) — mẫu `AR` chưa đổi ở đợt 1. **Đợt 2 bỏ điều kiện này đi là mở lại.**
   - Dùng token màu/size của `@sapo/ui-components`, không hardcode màu.
3. Không đổi API contract, không đổi payload `createJobImportFileInvoice`. `getDownloadSampleLink` (dòng 108-127) giữ nguyên ở đợt 1. Phần còn lại của popup giữ nguyên 100% theo Figma.
4. **Definition of done của repo này:** `pnpm lint:fix && pnpm format`, xác nhận `pnpm lint` exit 0.

---

## Issue 3 — [BE] Test chống lệch cột *(khuyến nghị)*

Copy file mẫu vào `src/test/resources/import-templates/` (đợt 1: 3 file mới AD/AI/AL + **file AR hiện hành chưa đổi**, để test cũng khóa luôn cam kết "AR giữ nguyên"), viết test đọc file thật bằng POI và assert **mọi entry của enum** đều tìm thấy đúng `headerName` tại đúng `cellRange` — chính là logic `extractHeadersFromSheet` + so khớp ở `validateImportFile` (dòng 3278-3319), nhưng chạy tự động thay vì thử tay.

Giá trị: bắt sớm mọi lần BA đổi file mẫu mà dev quên đổi enum (và ngược lại). Đây là loại lỗi mà QA rất khó phát hiện — header vẫn "khớp" đủ để qua cửa, nhưng dữ liệu lệch trường.

---

## Issue 6 — [BUG, tách riêng] Dòng lỗi ở giữa hóa đơn → hóa đơn được tạo THIẾU dòng hàng

**Không sửa trong task CCCD** (đụng logic chung của cả 4 luồng import). Ghi lại để báo leader/BA quyết định riêng.

Cuối mỗi vòng validate, dòng nào phát sinh lỗi thì bị đánh cờ (dòng 1735-1737, và tương tự ở 2038, 2497, 2927):
```java
if (errorSizeBefore < listFailedInvoices.size()) {
    data.setHasError(true);
}
```
Khi dựng request (dòng 525-531, và 703 / 894 / 935 / 978 / 1225):
```java
if (data.isHasError()) {
    if (invoiceRequest != null) {
        applyFormOfDiscount(invoiceRequest);
        invoiceRequestMap.put(rowNumberHasHeader, invoiceRequest);  // ← vẫn ĐẨY hóa đơn dở dang vào map
    }
    invoiceRequest = null;   // ← các dòng hàng còn lại của HĐ này bị bỏ qua
    continue;
}
```

| Vị trí dòng lỗi | Kết quả |
|---|---|
| **Dòng đầu** hóa đơn (có "Ký hiệu*") | Cả hóa đơn bị bỏ — ✅ đúng mong đợi |
| **Dòng hàng thứ 2+** của hóa đơn nhiều dòng | ❌ Hóa đơn **vẫn được tạo** nhưng chỉ có các dòng hàng **trước** dòng lỗi → **tổng tiền sai**. Email chỉ báo "Hàng {n}: …", user dễ tưởng chỉ dòng đó hỏng |

Bug **có sẵn**, không do task CCCD gây ra (email/SĐT/thuế suất sai ở dòng hàng đều dính). Nhưng CCCD là cột **cấp hóa đơn** mà nhiều kế toán quen copy xuống mọi dòng của cùng 1 hóa đơn → xác suất chạm cao hơn email/SĐT nhiều. Cần verify lại trên dev trước khi raise chính thức (test case #14).

---

## Test plan

### Unit test (BE)
- `validateIdNumber` — **20 ca, đã chạy pass 06/08/2026**:
  - **null** → `null`/`""`/`"   "`
  - **Hợp lệ** (12 số, bắt đầu bằng `0`) → `"001099001234"`, `"012345678901"`, `"096099001234"`, `"099099001234"`, `"000000000000"`, `" 001099001234 "` (trim)
  - **Lỗi — không bắt đầu bằng `0`** → `"101099001234"`, `"112345678901"`, `"704099001234"`, `"840123456789"`, `"999999999999"`
  - **Lỗi — sai độ dài / ký tự** → `"00109900123"` (11), `"0010990012345"` (13), `"00109900123a"`, `"001 099 001234"`, `"００１０９９００１２３４"` (full-width), `"0010-9900-1234"`

> Ma trận test thủ công đầy đủ (giá trị, định dạng ô, HĐ nhiều dòng, cấu trúc file, SQL đối chiếu) tách sang [[epic-62-test-cases-cccd]].

### Test thủ công — ma trận bắt buộc (chạy cho **cả** Hóa đơn và HĐ từ máy tính tiền)

| # | Case | Kỳ vọng |
|---|---|---|
| 0 | **Regression HĐ điều chỉnh:** import bằng file mẫu `AR` **cũ, không đổi gì** | Vẫn import OK như trước — chứng minh đợt 1 không đụng nhánh điều chỉnh |
| 1 | Cả 3 loại file mẫu mới (AD/AI/AL), CCCD hợp lệ 12 số bắt đầu bằng `0`, ô định dạng Text | Import OK; kiểm DB `invoice_buyers.id_number` **còn nguyên số 0 đầu** |
| 2 | Cột CCCD **rỗng toàn bộ** | Import OK, `id_number = null`, không lỗi |
| 3 | CCCD 11 / 13 số, có chữ, có dấu `-` | Lỗi dòng *"Căn cước công dân không đúng định dạng"*, dòng đó không tạo HĐ, email báo cáo có "Hàng {n}: …" |
| 4 | **Dùng file mẫu CŨ** (thiếu cột CCCD) | Chặn ngay khi nhập: *"Nhập file thất bại — Không thể thực hiện hành động này: File nhập không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán và thực hiện tải lại file mẫu."* |
| 5 | Đổi tên cột "Căn cước công dân" thành tên lạ | Chặn theo cơ chế hiện có |
| 6 | Xóa cột CCCD / thêm cột mới | *"File nhập không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán và thực hiện tải lại file mẫu."* |
| 7 | HĐ **nhiều dòng hàng**, CCCD khác nhau giữa các dòng, **tất cả đều hợp lệ** | Lấy **dòng đầu tiên** (kiểm DB + màn chi tiết HĐ, ô "Căn cước công dân") |
| 8 | Ô CCCD **tự đổi sang định dạng Number**, gõ `001099001234` | Lỗi *"Căn cước công dân không đúng định dạng"* (Excel đã cắt số 0 → còn 10 chữ số) — xác nhận quyết định Q2 |
| 8b | Dùng **đúng file mẫu BA giao** (cột Text), gõ `001099001234` | Import OK, DB lưu **đủ 12 chữ số kể cả 2 số 0 đầu** |
| **14** | **HĐ 3 dòng hàng, CCCD sai ở dòng hàng thứ 2** | Verify Issue 6: dự kiến HĐ vẫn tạo nhưng **chỉ có dòng hàng 1** → nếu đúng thì raise bug riêng, **không sửa trong task này** |
| 9 | Kiểm **các cột sau CCCD** (SĐT, Email, người nhận, giao dịch, chiết khấu, toàn bộ dòng hàng) | **Không lệch trường** — đây là rủi ro chính, phải soi kỹ từng cột trên HĐ nháp tạo ra |
| 10 | Mẫu 4 (HĐ bán hàng dự trữ quốc gia), người mua không MST + có CCCD | Import được (trước đây bị `InvoiceCommonService:661` chặn) |
| 11 | Import CCCD → ký & phát hành | `CCCDan` xuất hiện đúng trong XML gửi CQT (xem Q5) |
| 12 | IDOR (AL): `Ký hiệu + Số HĐ gốc` trỏ hóa đơn tenant khác | **404**, không 403 |
| 13 | UI: text `(cập nhật ngày: …)` hiện **cùng dòng, sau link** tải mẫu, ở "Hóa đơn mới" và "Hóa đơn thay thế" | Đúng Figma; **ngày khớp ngày merge master thật** — không còn là ngày fix cứng tạm |
| 13b | UI: chọn **"Hóa đơn điều chỉnh"** | Text **bị ẩn**; link tải mẫu vẫn trả file `AR` cũ và import bình thường |

---

## Rủi ro

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Lệch chỉ số cột trong `readXxxExcelData` → dữ liệu vào sai trường **mà không báo lỗi** | **Cao** | Sửa index từ lớn xuống nhỏ; test case #9; Issue 3 |
| ~~Xung đột với `feature/import-invoice-total`~~ | ~~Cao~~ | ✅ Đã xử lý: hoãn `AR` sang đợt 2, đợt 1 không đụng file nào của nhánh điều chỉnh |
| Breaking change: file mẫu HĐ mới + thay thế cũ ngừng dùng được ngay khi deploy | Trung bình | Deploy BE+FE cùng lúc; cân nhắc banner cảnh báo (Q4); thông báo trước cho CS/vận hành |
| User nhầm tưởng mẫu HĐ điều chỉnh cũng đã đổi (do text ngày dùng chung) | Trung bình | Q4 — ẩn text khi chọn HĐ điều chỉnh |
| CCCD sai ở dòng hàng giữa HĐ → HĐ tạo thiếu dòng hàng, tổng tiền sai (bug có sẵn, CCCD làm dễ chạm hơn) | **Cao nếu xác nhận** | Test case #14 để verify; raise **Issue 6** riêng, không sửa trong task này |
| Số 0 đầu bị Excel cắt phía người dùng | Trung bình | Cột Text trong template + báo lỗi rõ ràng (Q2) |
| BE và FE lệch nhịp deploy | Trung bình | Ghi ràng buộc "cùng release" vào cả 2 issue |
| CCCD sai đi thẳng lên thông điệp CQT | Thấp (có validate) | Test case #11 |

---

## Checklist trước khi bắt đầu code

**Đợt 1 (AD/AI/AL):**
- [x] Q1 đã chốt: hoãn `AR`, chờ `feature/import-invoice-total` (2026-08-05)
- [x] Q2 đã chốt: Excel cắt số 0 đầu → **báo lỗi, không pad** (2026-08-05)
- [x] Q3 đã chốt: **validate mọi dòng, lấy giá trị dòng đầu tiên** (2026-08-05)
- [x] Q7 đã chốt: **không thêm cột "Số hộ chiếu"** đợt này (2026-08-05)
- [x] Q4 — **cách làm** đã chốt: `(cập nhật ngày: …)` cùng dòng sau link, ẩn khi chọn HĐ điều chỉnh (05/08/2026, đã đọc Figma)
- [x] Q4 — **nguồn ngày** đã chốt: phương án **A** — fix cứng ngày tạm + `// TODO` tại chỗ, sửa trước khi merge master (05/08/2026)
- [x] Đã tạo child issue [#125](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-service/-/work_items/125) ở project `sapo-invoice-admin-service`, đã link về [invoice-docs#62](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/work_items/62) (06/08/2026)

→ **Mọi câu hỏi nghiệp vụ khác đã chốt — đợt 1 code được ngay**, chỉ chừa lại giá trị `SAMPLE_FILE_UPDATED_AT`.

### ⛔ Trước khi merge master (đợt 1)

- [ ] Sửa ngày ở `// TODO` trong `InvoiceImportModal.tsx` = **ngày merge master thật** (ngày fix cứng tạm trông hợp lệ nên sẽ không tự lộ ra nếu quên)
- [ ] QA đối chiếu lại ngày hiển thị trên popup khớp ngày merge (test case #13)

**Đợt 2 (AR) — mở lại khi:** *(số biến thể đã xác minh 07/08/2026: **2**, không phải 1)*
- [ ] `feature/import-invoice-total` đã merge master
- [ ] **BA giao file mẫu thứ 5** "AR-tích tự động + CCCD" và cập nhật SRS §6.2 từ 4 → 5 file ← **chặn cứng**
- [ ] Rebase code đợt 1 lên master mới trước khi sửa nhánh điều chỉnh
- [ ] Code cho **2** enum: `InvoiceHeaderAdjustmentImport` (AR tích) + `InvoiceHeaderAdjustmentProactivelyCalculateImport` (AR bỏ tích, có khối tổng tiền) — mỗi cái đủ 5 bước enum/model/read/validate/generateRequest
- [ ] FE: đè file `mau_nhap_hoa_don_DEItyFnb.xlsx` + **bỏ điều kiện ẩn** `(cập nhật ngày: …)` khi chọn "Hóa đơn điều chỉnh"
- [ ] **Chạy lại toàn bộ Nhóm 4 test** sau rebase — nhánh đó siết header check thành `actualHeaders.size() != expectedHeaders.size()`, thừa 1 ô tiêu đề cũng bị chặn

---

## Cập nhật sau khi implement (06/08/2026)

Cursor đã code xong đợt 1, đã review + verify. Nhánh: BE `feat/import-invoice-buyer-id-number`, FE `feature/import-invoice-cccd-template`.

### Luật validate đã đổi: `^\d{12}$` → `^0\d{11}$`

**Chỉ áp cho luồng import**, tại `ImportInvoiceValidator.ID_NUMBER_PATTERN`. Form tạo/sửa hóa đơn **giữ nguyên** `^$|^[0-9]{12}$` ở `InvoiceBuyerRequest.idNumber` — ngoài phạm vi task.

Đường đi của quyết định, ghi lại để không lặp lại tranh luận:

1. Ban đầu code đúng SRS `^\d{12}$` → `101099001234` pass, người dùng thấy sai.
2. Đọc lại SRS: UC-02 AC2/AC3 + FR2 đều chỉ ghi 12 chữ số ASCII; *"giữ số 0 đầu"* nghĩa là **không làm mất**, không phải **bắt buộc có**. Vậy hành vi ban đầu **đúng SRS**.
3. Cân nhắc siết theo **mã tỉnh 001–096** (Thông tư 07/2016/TT-BCA, Phụ lục I) → **ĐÃ BỎ**. Lý do: cùng điều khoản đó cho phép 3 số đầu là **mã quốc gia** (TCVN 7217 / ISO 3166-1 numeric) với công dân VN đăng ký khai sinh ở nước ngoài. Mọi ràng buộc dựa trên tiền tố mã tỉnh đều chặn nhầm nhóm này. Thêm nữa, sáp nhập 63 → 34 tỉnh (01/07/2025) làm danh mục mã tỉnh không còn chắc chắn — không nên hardcode.
4. Chốt mức giữa: **bắt buộc số `0` đầu**, không kiểm mã tỉnh.

**Hạn chế đã biết và chấp nhận:** CCCD của công dân VN đăng ký khai sinh ở nước ngoài (`840…` Hoa Kỳ, `392…` Nhật, `704…`) **vẫn bị chặn nhầm**. Trường hợp hiếm.

**Còn nợ:** BA cập nhật SRS (UC-02 AC2/AC3, FR2) + mô tả issue [#125](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-service/-/work_items/125), nếu không QA đối chiếu SRS sẽ raise nhầm.

### Message lỗi template đổi theo Figma (06/08/2026)

SRS yêu cầu **3 message**. Kiểm tra thực tế:

| | Message | Điều kiện | Trạng thái |
|---|---|---|---|
| M1 | `Căn cước công dân không đúng định dạng` | Ô có nhập, sau trim không khớp regex → **lỗi dòng**, ghi email `Hàng {n}: {lý do}` | ✅ Có · **giữ nguyên** |
| M2 | `Nhập file thất bại` + `Không thể thực hiện hành động này: …` | Xóa cột / thêm cột / template cũ → **chặn ngay khi nhập**, không parse | ✅ Có · **đã đổi nội dung** |
| M3 | `Tên cột {Tên cột} không hợp lệ` | Đổi tên một cột | ❌ **KHÔNG tồn tại** |

**M2 — đã sửa theo Figma** [12881-93650](https://www.figma.com/design/7t7C9XzNP3nBJpBismG9zS/SAPO-E-INVOICE?node-id=12881-93650). Chuỗi do BE trả về, sửa 1 chỗ tại `InvoiceImportService` (~dòng 3342):

```java
// cũ:  "File nhập không đúng template"
"File nhập không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán và thực hiện tải lại file mẫu."
```

Hiển thị cuối cùng ghép từ 3 nơi: `<Banner title="Nhập file thất bại">` (FE:202) + `` `Không thể thực hiện hành động này: ${e.data.message}` `` (FE:94) + chuỗi BE ở trên.

> ⚠️ **KHÔNG chép chữ "sản phẩm" từ Figma.** Bản thiết kế ghi *"Nhập file **sản phẩm** thất bại!"* nhưng đây là popup **hóa đơn** — frame Figma tên `Popup / Import prd` (prd = product), tức được nhân bản từ popup import sản phẩm và quên sửa text. Trong code cả 3 popup (sản phẩm, khách hàng, hóa đơn) đều dùng `title="Nhập file thất bại"`. Cần designer sửa lại Figma.

**M3 — không implement.** Grep 0 hit ở `sapo-invoice-admin-service`, `sapo-invoice-admin-frontend`, `invoice-app` và jar `sapo-invoice-common-1.2.5`. SRS ghi *"theo cơ chế hiện có (docx mục 14 dòng 1934)"* → BA giả định message đã tồn tại, thực tế không. **Chốt: đổi tên cột dùng chung M2.**

**Còn nợ BA:** cập nhật SRS §6.3, UC-03 AC2/AC3, FR3 theo 2 điểm trên.

### File mẫu chỉ format Text vài dòng đầu — chốt KHÔNG sửa (07/08/2026)

Phát hiện khi test: cột CCCD trong file mẫu chỉ có định dạng Text ở **AD dòng 4–7 · AI dòng 4–8 · AL dòng 4–8**, cột không có style mặc định → từ dòng kế tiếp là General → Excel cắt số 0 đầu ngay lúc gõ.

**Quyết định: không sửa file mẫu ở đợt này, người dùng tự format cột thành Text.** Chấp nhận được vì hệ thống **báo lỗi rõ** khi số 0 bị cắt (`Căn cước công dân không đúng định dạng`) — dữ liệu sai không lọt xuống DB, chỉ là user phải nhập lại.

Đã thử một vòng file mẫu mới (07/08): 3 file `AD_HD_moi_*`, `AI_HD_moi_*`, `AL_HD_thay_the_*` — header khớp enum 100% nhưng **chỉ AL** được format cả cột (tới dòng 998), AD/AI vẫn 4–7. Đã **xóa cả 3**, giữ nguyên bộ file cũ `mau_nhap_hoa_don_DEIty*`.

> Nếu sau này muốn sửa: chọn **cả cột** (bấm chữ cái đầu cột) → Format Cells → Text → lưu. Bôi đen vùng có dữ liệu là **không đủ**, vì dòng trống chưa có ô nào để mang định dạng. Cũng **không** dùng Custom format `000000000000` — chỉ đệm khi hiển thị, giá trị thật vẫn là số.

Cân nhắc rẻ tiền cho BA nếu muốn giảm va chạm mà không đụng code: thêm 1 dòng ghi chú ngay trong file mẫu (ô trống phía trên vùng tiêu đề, hoặc sheet "Hướng dẫn") nhắc format cột CCCD/SĐT/MST thành Text trước khi nhập.

### Rà soát gap so với SRS (07/08/2026)

Đối chiếu từng acceptance criteria với code. **9 mục đạt đủ**, 4 mục lệch có chủ đích, 4 gap còn lại.

**✅ Đạt đủ:** UC-01 AC1–AC7 (cột đúng vị trí · map `id_number` · cột cấp hóa đơn lấy dòng đầu · áp cả 2 phân hệ · không tác động tiền/thuế · không đồng bộ ngược danh mục KH — `InvoiceImportService` grep `customer` = 0 hit) · UC-02 AC1 (trống → null) · UC-02 AC5 (không đối chiếu chéo MST) · UC-03 AC1/AC4 · out-of-scope sạch (`passport_id` 0 hit trong diff).

**⚠️ Lệch SRS có chủ đích — BA phải cập nhật SRS, nếu không QA raise nhầm cả 4:**

| SRS | SRS nói | Code làm |
|---|---|---|
| FR2 · UC-02 AC2/AC3 | `^\d{12}$` | `^0\d{11}$` |
| §6.3 · UC-03 AC2 | *"File nhập không đúng template"* | *"…không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán…"* |
| FR3 · UC-03 AC3 | `Tên cột {Tên cột} không hợp lệ` | Dùng chung message trên |
| §6.1 | *"không thay đổi bố cục popup"* | Thêm `(cập nhật ngày: …)` — mâu thuẫn nội bộ SRS vs work item + Figma |

**❌ Gap còn lại:**

**1. FR1 · UC-02 AC6 — thiếu template AR.** `validateIdNumber` gọi ở 3/4 hàm: `validateProactivelyCalculateExcelData` (1514) · `validateAutomaticallyCalculateExcelData` (1829) · `validateInvoiceReplacementExcelData` (2263). **Không có** ở `validateInvoiceAdjustmentExcelData` (2524). Xử lý ở đợt 2 — xem checklist cuối tài liệu, lưu ý **2 biến thể** và **file mẫu thứ 5 do BA giao**.

**2. UC-02 AC4 — tách 3 vế, chỉ 1 vế thuộc về code và vế đó đã đạt:**

| Vế | Thuộc về | Trạng thái |
|---|---|---|
| Cột CCCD định dạng Text `@` trên file mẫu | File mẫu | ⚠️ chỉ 4–8 dòng đầu — chốt không sửa |
| Parse đọc ô CCCD **dạng chuỗi**, không scientific notation | **Code** | ✅ **Đạt** — `ExcelUtils.getCellStringValue` dùng `toPlainString()` |
| Ô kiểu số → convert sang chuỗi **đủ chữ số, không mất số 0 đầu** | Code | ❌ **Bất khả thi** |

Vế 3 không phải "chưa làm" mà là **SRS viết sai kỹ thuật**: Excel cắt số 0 lúc user gõ, file lưu xuống đã là `1099001234`, code không còn gì để khôi phục. BA cần sửa AC, dev không code thêm được.

**3. UC-03 AC2 — thêm cột ở cuối không bị chặn. Gap này TỰ ĐÓNG ở đợt 2.** Logic có sẵn từ trước, task này không đụng (`git diff` trên khối so header = rỗng, chỉ đổi chuỗi message trong `if`). Và `origin/feature/import-invoice-total` **đã siết đúng chỗ đó**:

```java
// master hiện tại — chỉ kiểm cột thiếu
if (!missingHeaders.isEmpty()) {
// feature/import-invoice-total — kiểm thêm số lượng cột
if (!missingHeaders.isEmpty() || actualHeaders.size() != expectedHeaders.size()) {
```

→ Không cần mở issue riêng. Chỉ ghi vào test case S5: *master hiện tại dự kiến **LỌT**, sau khi nhánh đó merge phải **CHẶN***.

**4. File mẫu chỉ format Text 4–8 dòng đầu** — đã chốt không sửa, xem mục riêng phía trên.

### Kết quả verify

| Hạng mục | Kết quả |
|---|---|
| 3 enum ↔ header thật trong `.xlsx` | Khớp 100% (AD 37/37, AI 42/42, AL 46/46) — đối chiếu bằng script, theo đúng ngữ nghĩa `String.trim()` của Java |
| Chỉ số `case` trong 3 hàm `read*ExcelData` ↔ cột enum | Khớp toàn bộ, không cột dữ liệu nào bị bỏ sót |
| Nhánh HĐ điều chỉnh (`AR`) | `git diff` không chứa chữ `Adjustment` nào → đợt 2 không conflict |
| File mẫu FE | md5 đúng cặp (`Dnc`=AD tích, `Dnb`=AI không tích, `Fna`=AL), `Fnb` không đụng · cột CCCD định dạng Text |
| BE | `compileJava` OK · test CCCD **20/20 pass** · không gây thêm test fail nào (baseline HEAD cũng 47 fail) |
| FE | `pnpm lint` exit 0 · `pnpm build` exit 0 |

### Đã sửa trong lúc review

- **FE format:** Cursor format lại toàn file bằng formatter lạ (80 cột) thay vì `oxfmt` của repo → 142 dòng nhiễu, `pnpm lint` fail. Đã chạy lại `oxfmt`, diff còn 3 hunk.
- **Canh dọc text ngày:** dùng `align-items: center` trên `StyledLinkDownloadFile`. Không dùng `padding-top` vì `theme.spacing()` trả **chuỗi** (`"8px"`) — `spacing(2) + 3` ra `"8px3"`, CSS không hợp lệ, bị bỏ qua. Icon không bị ảnh hưởng vì `StyledIcon` có `margin: auto` (auto margin vô hiệu hóa `align-self`).
- **Cỡ chữ theo Figma:** `variant="bodySm"` = 12/16 (`fontSize75`/`fontLineHeight1`), khớp node `34591:255508` cao 16px. Màu `subdued` → `ink60` `#747C87` = `Ink/60` của Figma, vốn đã đúng.

### Bug phát hiện kèm — raise riêng, KHÔNG sửa trong #125

| # | Bug | Ảnh hưởng |
|---|---|---|
| 1 | `LinkComponent.tsx:27` — `{...rest}` đứng **sau** `target={target}`, mà ui-components luôn truyền `target: undefined` → đè mất `"_blank"`. Prop `external` **chết toàn app** | Mọi link tải file mẫu (hàng hóa, khách hàng, hóa đơn) **không tải được** ở môi trường không set `VITE_CDN_BASE_URL`: react-router chặn click → catch-all `routers.tsx:51` → về home, modal đóng. Prod dùng CDN khác origin nên react-router render `<a>` thuần → không lộ. Fix: đảo `{...rest}` lên trước ở cả 2 nhánh |
| 2 | 47 test fail sẵn trên master (Circuit Breaker, EasyCA, Template, Health, InvoicePreview, Product) | Đã xác nhận bằng baseline chạy trên worktree HEAD sạch — không phải do task này |
| 3 | `validateImportFile` chỉ kiểm cột **thiếu**, không kiểm cột **thừa** | Thêm cột mới ở **cuối** file có thể lọt qua, trái UC-03 AC2. Cần verify (test case S5) |
| 4 | Issue 6 — dòng lỗi ở giữa hóa đơn → HĐ tạo thiếu dòng hàng | Đã mô tả ở mục "Issue 6" phía trên. Verify bằng test case M5 |

### Bản vá chỉ dùng local

`local-only-download-link-target.patch` — thêm `target="_blank"` vào `InvoiceImportModal.tsx` để tải được file mẫu khi test local (workaround cho bug #1). **Để unstaged, không commit.** Gỡ: `git checkout -- <file>` · dùng lại: `git apply <patch>`.
