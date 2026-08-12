---
created: 2026-08-06 10:30
updated: 2026-08-07 (rà soát gap SRS; S5 sẽ tự đóng ở đợt 2)
status: Ready for QA
project: "[[10_Projects/sapo-invoice/README]]"
---

# Test case cột CCCD — issue #125

- Plan: [[epic-62-them-cot-cccd-file-import-hoa-don]] · Prompt Cursor: [[epic-62-cursor-prompt-implement]]
- Issue: [sapo-invoice-admin-service#125](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-service/-/work_items/125)

## Luật validate (chốt 06/08/2026 — KHÁC SRS v0.1)

```
^0\d{11}$
```

**Tùy chọn** — để trống thì `id_number = NULL`, không lỗi. Có nhập thì trim rồi phải khớp:
đúng **12 chữ số ASCII** và **bắt buộc bắt đầu bằng số `0`**.
Sai → lỗi dòng, message nguyên văn: **`Căn cước công dân không đúng định dạng`**

> ⚠️ SRS v0.1 (UC-02 AC2/AC3, FR2) ghi `^\d{12}$`, **không** có ràng buộc số 0 đầu. **Cần BA cập nhật SRS**, nếu không QA đối chiếu SRS sẽ raise nhầm khi `101099001234` bị chặn.

**Phạm vi:** chỉ luồng **import file** (`ImportInvoiceValidator.ID_NUMBER_PATTERN`). Form tạo/sửa hóa đơn **giữ nguyên luật cũ** `^$|^[0-9]{12}$` ở `InvoiceBuyerRequest.idNumber` — ngoài phạm vi task này. Hệ quả cần biết: cùng một số CCCD không có số 0 đầu, gõ tay ở form thì **được**, nhập bằng file thì **bị chặn**.

**Hạn chế đã biết (chấp nhận):** theo Thông tư 07/2016/TT-BCA, 3 số đầu của số định danh là mã tỉnh (001–096) **hoặc mã quốc gia** (TCVN 7217 / ISO 3166-1 numeric) với công dân VN đăng ký khai sinh ở nước ngoài — ví dụ `840…` (Hoa Kỳ), `392…` (Nhật). Những số này **không bắt đầu bằng 0** nên sẽ bị luật hiện tại chặn nhầm. Trường hợp hiếm, đã cân nhắc và chấp nhận.

## Vị trí cột CCCD theo template

| Mã     | Loại file nhập                              | File tải về                      | Cột CCCD            | Dòng dữ liệu bắt đầu |
| ------ | ------------------------------------------- | -------------------------------- | ------------------- | -------------------- |
| **AD** | Hóa đơn mới — **tích** "Tự động tính toán…" | `mau_nhap_hoa_don_DEItyDnc.xlsx` | **H**               | 4                    |
| **AI** | Hóa đơn mới — **không tích**                | `mau_nhap_hoa_don_DEItyDnb.xlsx` | **H**               | 4                    |
| **AL** | Hóa đơn thay thế                            | `mau_nhap_hoa_don_DEItyFna.xlsx` | **K**               | 4                    |
| **AR** | Hóa đơn điều chỉnh                          | `mau_nhap_hoa_don_DEItyFnb.xlsx` | _(chưa có — đợt 2)_ | —                    |

Ô mẫu dòng 4 trong file BA giao sẵn giá trị `001099001234`, định dạng **Text (`@`)**.

> ⚠️ **GIỚI HẠN ĐÃ BIẾT — chốt 07/08/2026: KHÔNG sửa, để người dùng tự xử lý.** File mẫu **chỉ định dạng Text cho vài dòng đầu**, phần còn lại của cột là General:
>
> | Template | Cột | Text ở dòng | Style mặc định cả cột | Từ dòng này trở đi **mất số 0 đầu** |
> | -------- | --- | ----------- | --------------------- | ----------------------------------- |
> | AD       | H   | 4–**7**     | General               | **8**                               |
> | AI       | H   | 4–**8**     | General               | **9**                               |
> | AL       | K   | 4–**8**     | General               | **9**                               |
>
> Kế toán import nhiều hóa đơn sẽ nhập từ dòng 8 trở đi và **mất số 0** — trên Excel nhìn vẫn bình thường, chỉ đến khi nhận email lỗi *"Căn cước công dân không đúng định dạng"* mới phát hiện.
>
> **Quyết định:** không sửa file mẫu ở đợt này. Người dùng tự format cột CCCD thành Text trước khi nhập. Hệ thống **báo lỗi rõ ràng** khi số 0 bị cắt, nên dữ liệu sai không lọt xuống DB — đây là lý do chấp nhận được.
>
> **Hướng dẫn cho người dùng / CS:** bấm vào **chữ cái đầu cột** (chọn cả cột — không phải bôi đen vài ô) → `Cmd/Ctrl + 1` → **Text** → *rồi mới gõ*. Format sau khi gõ **không** khôi phục được số 0 đã mất, phải nhập lại. Cách nhanh cho vài ô lẻ: gõ dấu nháy đơn phía trước, ví dụ `'001099001234`.
>
> ❌ **Đừng dùng Custom format `000000000000`** — chỉ đệm số 0 khi hiển thị, giá trị thật vẫn là số, import vẫn lỗi.
>
> Cột **"Số điện thoại"** và **"Mã số thuế người mua"** nhiều khả năng cũng bị tương tự (đều cần giữ số 0 đầu) — lỗi có sẵn từ trước, không thuộc task này.
>
> ✅ **Với QA:** bộ file test trong [`files/`](files/) dựng bằng script nên **không dính lỗi này** (mọi dòng đều `@Text`). Nhưng nếu **tự thêm dòng mới** vào các file đó, hoặc dựng file mới từ mẫu tải về, thì phải format cột thành Text **trước khi gõ**.

---

## Nhóm 1 — Giá trị CCCD · gộp chung **1 file**, mỗi dòng = 1 hóa đơn

> 📎 **File:** [01-AD-nhom1-gia-tri-cccd.xlsx](files/01-AD-nhom1-gia-tri-cccd.xlsx) · template **AD** (Hóa đơn mới, **tích** "Tự động tính toán…") · cột CCCD = **H** · dữ liệu dòng **4–22**
> ✅ Đã verify: cả 19 dòng đều định dạng `@Text` và lưu dạng chuỗi → giữ nguyên số 0 đầu, khoảng trắng và ký tự full-width đúng như bảng dưới.

Điền "Ký hiệu\*" ở mọi dòng để mỗi dòng thành một hóa đơn riêng. Dòng hợp lệ sẽ import, dòng lỗi bị bỏ và liệt kê trong email báo cáo.

| #   | Dòng Excel | Gõ vào ô CCCD                              | Kỳ vọng                                                              |
| --- | ---------- | ------------------------------------------ | -------------------------------------------------------------------- |
| V1  | 4          | _(để trống)_                               | ✅ Import OK · `id_number = NULL`                                     |
| V2  | 5          | `001099001234`                             | ✅ OK — ca chuẩn (001 = Hà Nội)                                       |
| V3  | 6          | `096099001234`                             | ✅ OK                                                                 |
| V4  | 7          | `079123456789`                             | ✅ OK — 079 = TP.HCM                                                  |
| V5  | 8          | `012345678901`                             | ✅ OK                                                                 |
| V6  | 9          | `099099001234`                             | ✅ OK — chỉ cần bắt đầu bằng `0`, **không** kiểm mã tỉnh              |
| V7  | 10         | `000000000000`                             | ✅ OK — số vô nghĩa nhưng vẫn khớp luật, đây là giới hạn đã biết      |
| V8  | 11         | `001099001234` _(1 dấu cách trước và sau)_ | ✅ OK — hệ thống trim · DB lưu **không** kèm dấu cách                 |
| V9  | 12         | `   ` _(chỉ dấu cách)_                     | ✅ OK · `id_number = NULL` — coi như để trống                         |
| E1  | 13         | `00109900123` _(11 số)_                    | ❌ Lỗi dòng                                                           |
| E2  | 14         | `0010990012345` _(13 số)_                  | ❌ Lỗi dòng                                                           |
| E3  | 15         | `00109900123a`                             | ❌ Lỗi dòng                                                           |
| E4  | 16         | `0010-9900-1234`                           | ❌ Lỗi dòng                                                           |
| E5  | 17         | `001 099 001234` _(dấu cách ở giữa)_       | ❌ Lỗi dòng                                                           |
| E6  | 18         | `００１０９９００１２３４` _(chữ số full-width)_       | ❌ Lỗi dòng                                                           |
| E7  | 19         | `101099001234`                             | ❌ Không bắt đầu bằng `0`                                             |
| E8  | 20         | `112345678901`                             | ❌ Không bắt đầu bằng `0`                                             |
| E9  | 21         | `999999999999`                             | ❌ Không bắt đầu bằng `0`                                             |
| E10 | 22         | `840123456789`                             | ❌ Bị chặn — mã quốc gia Hoa Kỳ, xem "Hạn chế đã biết" ở đầu tài liệu |

Kiểm ở email báo cáo: **10 dòng lỗi** (E1–E10 = dòng Excel 13–22), mỗi dòng có `Hàng {n}: Căn cước công dân không đúng định dạng`, và **số hàng trỏ đúng dòng Excel** tương ứng.

Cột **"Mã chứng từ gốc"** của mỗi dòng đã điền sẵn mã case (`V1`, `E7`…) và **tên người mua** có tiền tố case (`V2 Nguyen Van Anh`) → tra DB bằng `full_name` là ra ngay case nào.

---

## Nhóm 2 — Định dạng ô · file riêng, phải tự đổi format ô

> 📎 **File:** [02-AD-nhom2-dinh-dang-o.xlsx](files/02-AD-nhom2-dinh-dang-o.xlsx) · template **AD** · cột **H** · dữ liệu dòng **4–7**
> ✅ Đã verify trạng thái ô: `H4` = `@Text` chuỗi `001099001234` · `H5`/`H6` = **kiểu số** `1099001234` (Number/General) · `H7` = **kiểu số** `123456789012`

| #   | Dòng Excel | Định dạng ô                        | Gõ vào                                      | Kỳ vọng                                                                 |
| --- | ---------- | ---------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------- |
| F1  | 4          | **Text (`@`)** — mặc định file mẫu | `001099001234`                              | ✅ OK · DB đủ **12 ký tự**, còn nguyên 2 số `0` đầu                     |
| F2  | 5          | Đổi sang **Number**                | `001099001234`                              | ❌ Excel cắt số 0 ngay lúc gõ → file chỉ còn `1099001234` (10 số) → lỗi |
| F3  | 6          | **General**                        | `001099001234`                              | ❌ Như F2                                                               |
| F4  | 7          | **Number**                         | `123456789012` _(12 số, không có số 0 đầu)_ | ❌ Không bắt đầu bằng `0`                                               |

> Ô định dạng **Number luôn lỗi** — Excel không giữ được số `0` đầu, mà luật bắt buộc phải bắt đầu bằng `0`. Đây là hành vi đã chốt (Q2): **báo lỗi, không tự thêm `0`**.

> 📌 File số 2 đã **mô phỏng sẵn trạng thái sau khi Excel cắt số 0**: dòng F2/F3 lưu số `1099001234` với định dạng Number/General, dòng F4 lưu `123456789012`. Nếu muốn kiểm chứng đúng thao tác người dùng, mở file, xóa ô rồi tự gõ lại `001099001234` vào ô đã set Number — kết quả phải giống hệt.

---

## Nhóm 3 — Hóa đơn nhiều dòng hàng · 1 file

> 📎 **File:** [03-AD-nhom3-nhieu-dong-hang.xlsx](files/03-AD-nhom3-nhieu-dong-hang.xlsx) · template **AD** · cột **H** · dữ liệu dòng **4–18** (5 HĐ × 3 dòng hàng)

CCCD là cột **cấp hóa đơn** → chỉ đọc ở **dòng mở đầu hóa đơn** (dòng có "Ký hiệu\*"), nhưng **validate mọi dòng có giá trị**.

| #      | Dòng Excel | Bố trí                                                                        | Kỳ vọng                                                                                                                                                      |
| ------ | ---------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| M1     | 4–6        | HĐ 3 dòng hàng · CCCD `001099001234` chỉ ở dòng đầu                           | ✅ Lưu `001099001234`                                                                                                                                        |
| M2     | 7–9        | HĐ 3 dòng hàng · 3 CCCD **khác nhau nhưng đều hợp lệ** (`001…`/`079…`/`096…`) | ✅ Lưu giá trị **dòng đầu** (`001…`)                                                                                                                         |
| M3     | 10–12      | HĐ 3 dòng hàng · dòng đầu **trống**, dòng 2 có `079123456789` hợp lệ          | ✅ `id_number = NULL` — giá trị dòng 2 **không** được lấy                                                                                                    |
| M4     | 13–15      | HĐ 3 dòng hàng · dòng đầu **trống**, dòng 2 có `101099001234` **sai**         | ❌ Vẫn báo lỗi dòng 14 dù giá trị đó không được dùng                                                                                                         |
| **M5** | 16–18      | HĐ 3 dòng hàng · dòng đầu **hợp lệ**, dòng 2 CCCD **sai**                     | ⚠️ **Verify Issue 6** — dự kiến HĐ **vẫn được tạo** nhưng **chỉ có dòng hàng 1** → tổng tiền sai. Nếu đúng vậy thì **raise bug riêng, KHÔNG sửa trong #125** |

---

## Nhóm 4 — Cấu trúc file · mỗi case **1 file riêng**

| #      | File                                                                                          | Sửa gì trên file · đã verify cấu trúc                                       | Kỳ vọng                                                                                                                                                      |
| ------ | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| S1     | [04-AD-S1-file-mau-cu-khong-co-cot-cccd.xlsx](files/04-AD-S1-file-mau-cu-khong-co-cot-cccd.xlsx) | Không có tiêu đề "Căn cước công dân" · cột cuối lùi về **AD1**                | ❌ _Nhập file thất bại — Không thể thực hiện hành động này: File nhập không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán và thực hiện tải lại file mẫu._                                                                   |
| S2     | [05-AD-S2-xoa-cot-cccd.xlsx](files/05-AD-S2-xoa-cot-cccd.xlsx)                                  | Giống S1                                                                      | ❌ Như S1                                                                                                                                                    |
| S3     | [06-AD-S3-doi-ten-tieu-de-cccd.xlsx](files/06-AD-S3-doi-ten-tieu-de-cccd.xlsx)                  | `H2` đổi thành `CCCD` · cột cuối vẫn **AE1**                                  | ❌ **Cùng message với S1/S2**: _File nhập không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán và thực hiện tải lại file mẫu._. ⚠️ SRS ghi phải ra *"Tên cột {Tên cột} không hợp lệ"* — **message đó KHÔNG tồn tại trong code** (grep BE+FE = 0 hit), SRS dẫn nguồn từ docx cũ. Không phải bug của #125, nhưng cần BA sửa SRS |
| S4     | [07-AD-S4-chen-cot-moi-o-giua.xlsx](files/07-AD-S4-chen-cot-moi-o-giua.xlsx)                    | CCCD dời từ `H2` sang **`I2`** · cột cuối đẩy sang **AF1**                    | ❌ Bị chặn — mọi cột phía sau lệch vị trí                                                                                                                    |
| **S5** | [08-AD-S5-them-cot-o-cuoi.xlsx](files/08-AD-S5-them-cot-o-cuoi.xlsx)                            | CCCD vẫn `H2` · thêm **`AF2` = "Cột thêm ở cuối"**, mọi cột cũ giữ nguyên vị trí | ⚠️ **Master hiện tại: dự kiến LỌT** — `validateImportFile` chỉ kiểm cột thiếu, không kiểm cột thừa. **KHÔNG raise bug riêng**: `origin/feature/import-invoice-total` đã siết thành `!missingHeaders.isEmpty() \|\| actualHeaders.size() != expectedHeaders.size()` → sau khi nhánh đó merge (đợt 2) thì phải **CHẶN**. Chạy lại case này sau rebase |

> ⚠️ **S1 và S2 đang là 2 file giống hệt nhau** (đều là template hiện tại đã bỏ cột H). Muốn S1 đúng nghĩa "file mẫu cũ" thì phải lấy file `.xlsx` tải về từ **bản master trước khi merge #125** — nếu template cũ còn khác chỗ nào ngoài cột CCCD thì file mô phỏng này không phát hiện được.

---

## Nhóm 5 — Regression & phạm vi

| #      | Case                                                                                                                                                             | Kỳ vọng                                                                                                              |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| R1     | Import file mẫu **AR (điều chỉnh) cũ**, không sửa gì → [11-AR-dieu-chinh-giu-nguyen-R1.xlsx](files/11-AR-dieu-chinh-giu-nguyen-R1.xlsx) · ✅ đã verify md5 **trùng khớp** bản AR đang ship ở FE (`mau_nhap_hoa_don_DEItyFnb.xlsx`), **không** phải bản AR mới của BA | ✅ Vẫn OK như trước — chứng minh đợt 1 không đụng nhánh điều chỉnh                                                   |
| R2     | Chạy lại Nhóm 1 trên phân hệ **HĐ từ máy tính tiền**                                                                                                             | ✅ Kết quả giống hệt — 2 phân hệ dùng chung endpoint                                                                 |
| R3     | Chạy Nhóm 1 rút gọn trên **AI** (không tích) và **AL** (thay thế)                                                                                                | ✅ Giống AD                                                                                                          |
| **R4** | **Soi các cột SAU cột CCCD** trên HĐ nháp vừa tạo: SĐT, Email, người nhận, hình thức thanh toán, ngân hàng, loại tiền, tỷ giá, chiết khấu, **toàn bộ dòng hàng** | ✅ **Không lệch trường** — đây là rủi ro số 1 của task, phải soi từng cột                                            |
| R5     | **Form tạo hóa đơn** (không qua import): nhập CCCD `101099001234`                                                                                                | ✅ **Vẫn cho lưu** — form giữ luật cũ `^[0-9]{12}$`, ngoài phạm vi task. Đây là **lệch có chủ đích**, không phải bug |
| R6     | Form tạo hóa đơn: nhập `001099001234`                                                                                                                            | ✅ OK                                                                                                                |
| R7     | Mẫu 4 (HĐ bán hàng dự trữ quốc gia), người mua **không MST** + có CCCD hợp lệ                                                                                    | ✅ Import được (trước đây bị `InvoiceCommonService:661` chặn)                                                        |
| R8     | Import CCCD hợp lệ → ký & phát hành                                                                                                                              | ✅ `CCCDan` xuất hiện đúng trong XML gửi CQT                                                                         |
| R9     | **AL**: `Ký hiệu + Số HĐ gốc` trỏ hóa đơn của tenant khác → [10-AL-thay-the-nhom1-rut-gon-va-R9.xlsx](files/10-AL-thay-the-nhom1-rut-gon-va-R9.xlsx) (cột CCCD = **K**, dòng 4–8) | ✅ **404**, không phải 403                                                                                           |
| R10    | UI: text `(cập nhật ngày: …)` hiện **cùng dòng, sau link** tải mẫu ở "Hóa đơn mới" / "Hóa đơn thay thế"                                                          | ✅ Đúng Figma · **ngày khớp ngày merge master thật**                                                                 |
| R11    | UI: chọn **"Hóa đơn điều chỉnh"**                                                                                                                                | ✅ Text bị **ẩn** · link vẫn trả file `AR` cũ và import bình thường                                                  |

---

## 🗂 Bộ file test đã tạo — file nào ra kết quả nào

> Thư mục: [`files/`](files/) — nằm cạnh tài liệu này trong `epic-62-cccd/`. Tất cả dựng từ chính 3 file mẫu BA giao.
> Toàn bộ 10 file đã được **verify cấu trúc bằng script** (đọc XML thật): vị trí ô tiêu đề CCCD, cột cuối, kiểu ô và định dạng số. Kết quả ghi ở cột "Đã verify".

| #   | File                                                                                            | Template                          | Dòng dữ liệu              | Case                | Đã verify                                                | Kết quả mong đợi tổng thể                                                                                                     |
| --- | ----------------------------------------------------------------------------------------------- | --------------------------------- | ------------------------- | ------------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 01  | [01-AD-nhom1-gia-tri-cccd.xlsx](files/01-AD-nhom1-gia-tri-cccd.xlsx)                             | AD · CCCD ở **H**                 | 4–22 (19 dòng = 19 HĐ)    | V1–V9, E1–E10       | 19/19 dòng `@Text` + chuỗi · giữ đúng số 0 đầu           | **9 hóa đơn nháp được tạo** (V1–V9) · **10 dòng lỗi** (E1–E10 = hàng 13–22), message `Căn cước công dân không đúng định dạng` |
| 02  | [02-AD-nhom2-dinh-dang-o.xlsx](files/02-AD-nhom2-dinh-dang-o.xlsx)                               | AD · CCCD ở **H**                 | 4–7                       | F1–F4               | H4 Text · H5/H6/H7 **kiểu số** đúng như mô phỏng         | **1 HĐ được tạo** (F1) · **3 dòng lỗi** (F2, F3, F4)                                                                          |
| 03  | [03-AD-nhom3-nhieu-dong-hang.xlsx](files/03-AD-nhom3-nhieu-dong-hang.xlsx)                       | AD · CCCD ở **H**                 | 4–18 (5 HĐ × 3 dòng hàng) | M1–M5               | CCCD ở `H2`, cột cuối `AE1` — đúng template AD           | M1 `001099001234` · M2 `001099001234` (lấy dòng đầu) · M3 `NULL` · M4 **lỗi hàng 14** · M5 ⚠️ verify Issue 6                  |
| 04  | [04-AD-S1-file-mau-cu-khong-co-cot-cccd.xlsx](files/04-AD-S1-file-mau-cu-khong-co-cot-cccd.xlsx) | AD (bỏ cột H)                     | 4–5                       | S1                  | không có tiêu đề CCCD · cột cuối lùi về `AD1`            | ❌ _File nhập không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán và thực hiện tải lại file mẫu._                                                                                            |
| 05  | [05-AD-S2-xoa-cot-cccd.xlsx](files/05-AD-S2-xoa-cot-cccd.xlsx)                                   | AD (bỏ cột H)                     | 4–5                       | S2                  | giống hệt 04                                             | ❌ Như S1                                                                                                                     |
| 06  | [06-AD-S3-doi-ten-tieu-de-cccd.xlsx](files/06-AD-S3-doi-ten-tieu-de-cccd.xlsx)                   | AD (`H2` = `CCCD`)                | 4–5                       | S3                  | không còn chuỗi "Căn cước công dân" · cột cuối vẫn `AE1` | ❌ Bị chặn                                                                                                                    |
| 07  | [07-AD-S4-chen-cot-moi-o-giua.xlsx](files/07-AD-S4-chen-cot-moi-o-giua.xlsx)                     | AD (+1 cột, CCCD dời sang **I**)  | 4–5                       | S4                  | CCCD ở `I2` · cột cuối đẩy sang `AF1`                    | ❌ Bị chặn                                                                                                                    |
| 08  | [08-AD-S5-them-cot-o-cuoi.xlsx](files/08-AD-S5-them-cot-o-cuoi.xlsx)                             | AD (+`AF2` = "Cột thêm ở cuối")   | 4–5                       | S5                  | CCCD vẫn `H2`, cột cũ **không lệch** · thừa `AF2`        | ⚠️ Dự kiến **LỌT** trên master · sẽ **CHẶN** sau khi `feature/import-invoice-total` merge                                                                |
| 09  | ⛔ _chưa có_                                                                                     | **AI** · CCCD ở **H**             | —                         | V2, V8, E1, E10     | —                                                        | **Thiếu.** Tải `mau_nhap_hoa_don_DEItyDnb.xlsx` từ popup (bỏ tích "Tự động tính toán…") rồi dựng bổ sung                      |
| 10  | [10-AL-thay-the-nhom1-rut-gon-va-R9.xlsx](files/10-AL-thay-the-nhom1-rut-gon-va-R9.xlsx)         | AL · CCCD ở **K**                 | 4–8                       | V2, V8, E1, E10, R9 | CCCD ở `K2` · cột cuối `AM1` — đúng template AL          | 2 HĐ thay thế OK (V2, V8) · 2 dòng lỗi (E1, E10) · R9 → **404**                                                               |
| 11  | [11-AR-dieu-chinh-giu-nguyen-R1.xlsx](files/11-AR-dieu-chinh-giu-nguyen-R1.xlsx)                 | AR **cũ** (không có cột CCCD)     | 4–7 (data mẫu gốc)        | R1                  | md5 **trùng** `mau_nhap_hoa_don_DEItyFnb.xlsx` đang ship  | ✅ Import bình thường — chứng minh đợt 1 không đụng nhánh điều chỉnh                                                          |

### ⚠️ Phải sửa trước khi chạy

1. **Ký hiệu hóa đơn** — mọi file đang dùng `1C25TRR`. Thay bằng ký hiệu thật đang hoạt động của tenant test (cột `A` với AD, cột `A` + `D` với AL).
2. **File 10 (AL)** — cột `B` "Số hóa đơn gốc\*" đang là `00000003`–`00000006`, phải đổi thành số hóa đơn **có thật** trên tenant. Riêng dòng R9 (`00000099`) phải trỏ hóa đơn của **tenant khác** để kiểm 404.
3. **MST người mua** đang dùng `0110906446` của file mẫu — đổi nếu tenant test có ràng buộc riêng.
4. **File 08 (S5)** dùng nhân bản có thêm cột ở cuối; nếu import lọt, nhớ **xóa hóa đơn nháp** phát sinh trước khi chạy nhóm khác để không nhiễu kết quả DB.

### Case tự làm tay (không dựng file được)

R2, R4, R5, R6, R7, R8, R10, R11 — thao tác trên UI/DB, không phải case file.

### 📋 Bảng ghi kết quả

Tick khi chạy xong. Cột "Thực tế" chỉ điền khi **khác** kỳ vọng.

| Xong | File / Case                    | Kỳ vọng tóm tắt                             | Thực tế (nếu khác) |
| ---- | ------------------------------ | ------------------------------------------- | ------------------ |
| [ ]  | 01 · V1–V9                     | 9 HĐ nháp được tạo, `id_number` đúng 12 ký tự |                    |
| [ ]  | 01 · E1–E10                    | 10 dòng lỗi ở hàng 13–22                    |                    |
| [ ]  | 02 · F1–F4                     | 1 HĐ (F1) + 3 lỗi                           |                    |
| [ ]  | 03 · M1–M4                     | Lấy dòng đầu · M4 lỗi hàng 14               |                    |
| [ ]  | 03 · **M5** (Issue 6)          | HĐ tạo thiếu dòng hàng? → raise bug riêng   |                    |
| [ ]  | 04 · S1                        | Chặn: sai template                          |                    |
| [ ]  | 05 · S2                        | Chặn: sai template                          |                    |
| [ ]  | 06 · S3                        | Chặn                                        |                    |
| [ ]  | 07 · S4                        | Chặn                                        |                    |
| [ ]  | 08 · **S5**                    | Master: LỌT · sau đợt 2: CHẶN               |                    |
| [ ]  | 09 · AI *(chưa có file)*       | Giống 01 rút gọn                            |                    |
| [ ]  | 10 · AL + R9                   | 2 OK, 2 lỗi, R9 → 404                       |                    |
| [ ]  | 11 · R1 (AR cũ)                | Import bình thường                          |                    |
| [ ]  | R2 · phân hệ HĐ máy tính tiền  | Kết quả giống hệt AD                        |                    |
| [ ]  | **R4** · soi cột sau CCCD      | Không lệch trường — rủi ro số 1             |                    |
| [ ]  | R5 · form nhập `101099001234`  | **Vẫn cho lưu** (lệch có chủ đích)          |                    |
| [ ]  | R7 · mẫu 4 không MST + CCCD    | Import được                                 |                    |
| [ ]  | R8 · phát hành → XML CQT       | Có `CCCDan`                                 |                    |
| [ ]  | R10 / R11 · UI text ngày       | Đúng Figma · ẩn khi chọn HĐ điều chỉnh      |                    |

---

## Cách đối chiếu kết quả

**1. Database** — quan trọng nhất là `do_dai = 12` để chắc số `0` đầu không bị mất:

```sql
SELECT i.invoice_no,
       b.full_name,
       b.id_number,
       LENGTH(b.id_number) AS do_dai
FROM invoice_buyers b
JOIN invoices i ON i.id = b.invoice_id AND i.tenant_id = b.tenant_id
WHERE b.tenant_id = <tenant_id>
ORDER BY i.id DESC
LIMIT 30;
```

Vì `full_name` đã gắn tiền tố case, kết quả đọc thẳng ra được: `V2 Nguyen Van Anh | 001099001234 | 12`.

**2. Email báo cáo** — đúng số dòng lỗi, message nguyên văn, số hàng trỏ đúng dòng Excel.

**3. Màn chi tiết hóa đơn** — ô "Căn cước công dân" hiển thị đủ 12 số kể cả số `0` đầu.

## Gợi ý bộ file cần tạo _(bản gốc — đã hiện thực hóa ở bảng trên)_

| File | Template  | Nội dung                                             |
| ---- | --------- | ---------------------------------------------------- |
| 1    | AD        | Nhóm 1 — 19 dòng (V1–V9, E1–E10), mỗi dòng 1 hóa đơn |
| 2    | AD        | Nhóm 2 — 4 dòng, tự đổi định dạng ô từng dòng        |
| 3    | AD        | Nhóm 3 — 5 hóa đơn, mỗi HĐ 3 dòng hàng               |
| 4–8  | AD        | Nhóm 4 — mỗi case S1–S5 một file                     |
| 9    | AI        | Nhóm 1 rút gọn (V2, V8, E1, E10)                     |
| 10   | AL        | Nhóm 1 rút gọn + case R9                             |
| 11   | AR **cũ** | R1 — không sửa gì, chỉ để chứng minh không vỡ        |
