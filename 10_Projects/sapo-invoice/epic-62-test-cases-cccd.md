---
created: 2026-08-06 10:30
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
| **AR** | Hóa đơn điều chỉnh                          | `mau_nhap_hoa_don_DEItyFnb.xlsx` | *(chưa có — đợt 2)* | —                    |

Ô mẫu dòng 4 trong file BA giao sẵn giá trị `001099001234`, định dạng **Text (`@`)**.

---

## Nhóm 1 — Giá trị CCCD · gộp chung **1 file**, mỗi dòng = 1 hóa đơn

Điền "Ký hiệu*" ở mọi dòng để mỗi dòng thành một hóa đơn riêng. Dòng hợp lệ sẽ import, dòng lỗi bị bỏ và liệt kê trong email báo cáo.

| # | Gõ vào ô CCCD | Kỳ vọng |
|---|---|---|
| V1 | *(để trống)* | ✅ Import OK · `id_number = NULL` |
| V2 | `001099001234` | ✅ OK — ca chuẩn (001 = Hà Nội) |
| V3 | `096099001234` | ✅ OK |
| V4 | `079123456789` | ✅ OK — 079 = TP.HCM |
| V5 | `012345678901` | ✅ OK |
| V6 | `099099001234` | ✅ OK — chỉ cần bắt đầu bằng `0`, **không** kiểm mã tỉnh |
| V7 | `000000000000` | ✅ OK — số vô nghĩa nhưng vẫn khớp luật, đây là giới hạn đã biết |
| V8 | ` 001099001234 ` *(1 dấu cách trước và sau)* | ✅ OK — hệ thống trim · DB lưu **không** kèm dấu cách |
| V9 | `   ` *(chỉ dấu cách)* | ✅ OK · `id_number = NULL` — coi như để trống |
| E1 | `00109900123` *(11 số)* | ❌ Lỗi dòng |
| E2 | `0010990012345` *(13 số)* | ❌ Lỗi dòng |
| E3 | `00109900123a` | ❌ Lỗi dòng |
| E4 | `0010-9900-1234` | ❌ Lỗi dòng |
| E5 | `001 099 001234` *(dấu cách ở giữa)* | ❌ Lỗi dòng |
| E6 | `００１０９９００１２３４` *(chữ số full-width)* | ❌ Lỗi dòng |
| E7 | `101099001234` | ❌ Không bắt đầu bằng `0` |
| E8 | `112345678901` | ❌ Không bắt đầu bằng `0` |
| E9 | `999999999999` | ❌ Không bắt đầu bằng `0` |
| E10 | `840123456789` | ❌ Bị chặn — mã quốc gia Hoa Kỳ, xem "Hạn chế đã biết" ở đầu tài liệu |

Kiểm ở email báo cáo: **10 dòng lỗi** (E1–E10), mỗi dòng có `Hàng {n}: Căn cước công dân không đúng định dạng`, và **số hàng trỏ đúng dòng Excel** tương ứng.

---

## Nhóm 2 — Định dạng ô · file riêng, phải tự đổi format ô

| # | Định dạng ô | Gõ vào | Kỳ vọng |
|---|---|---|---|
| F1 | **Text (`@`)** — mặc định file mẫu | `001099001234` | ✅ OK · DB đủ **12 ký tự**, còn nguyên 2 số `0` đầu |
| F2 | Đổi sang **Number** | `001099001234` | ❌ Excel cắt số 0 ngay lúc gõ → file chỉ còn `1099001234` (10 số) → lỗi |
| F3 | **General** | `001099001234` | ❌ Như F2 |
| F4 | **Number** | `123456789012` *(12 số, không có số 0 đầu)* | ❌ Không bắt đầu bằng `0` |

> Ô định dạng **Number luôn lỗi** — Excel không giữ được số `0` đầu, mà luật bắt buộc phải bắt đầu bằng `0`. Đây là hành vi đã chốt (Q2): **báo lỗi, không tự thêm `0`**.

---

## Nhóm 3 — Hóa đơn nhiều dòng hàng · 1 file

CCCD là cột **cấp hóa đơn** → chỉ đọc ở **dòng mở đầu hóa đơn** (dòng có "Ký hiệu*"), nhưng **validate mọi dòng có giá trị**.

| # | Bố trí | Kỳ vọng |
|---|---|---|
| M1 | HĐ 3 dòng hàng · CCCD `001099001234` chỉ ở dòng đầu | ✅ Lưu `001099001234` |
| M2 | HĐ 3 dòng hàng · 3 CCCD **khác nhau nhưng đều hợp lệ** (`001…`/`079…`/`096…`) | ✅ Lưu giá trị **dòng đầu** (`001…`) |
| M3 | HĐ 3 dòng hàng · dòng đầu **trống**, dòng 2 có `079123456789` hợp lệ | ✅ `id_number = NULL` — giá trị dòng 2 **không** được lấy |
| M4 | HĐ 3 dòng hàng · dòng đầu **trống**, dòng 2 có `101099001234` **sai** | ❌ Vẫn báo lỗi dòng 2 dù giá trị đó không được dùng |
| **M5** | HĐ 3 dòng hàng · dòng đầu **hợp lệ**, dòng 2 CCCD **sai** | ⚠️ **Verify Issue 6** — dự kiến HĐ **vẫn được tạo** nhưng **chỉ có dòng hàng 1** → tổng tiền sai. Nếu đúng vậy thì **raise bug riêng, KHÔNG sửa trong #125** |

---

## Nhóm 4 — Cấu trúc file · mỗi case **1 file riêng**

| # | Sửa gì trên file | Kỳ vọng |
|---|---|---|
| S1 | Dùng **file mẫu CŨ** (chưa có cột CCCD) | ❌ *Nhập file thất bại — Không thể thực hiện hành động này: File nhập không đúng template* |
| S2 | **Xóa** hẳn cột CCCD | ❌ Như S1 |
| S3 | **Đổi tên** tiêu đề `Căn cước công dân` → `CCCD` | ❌ Bị chặn |
| S4 | **Chèn cột mới vào giữa** (vd ngay trước cột CCCD) | ❌ Bị chặn — mọi cột phía sau lệch vị trí |
| **S5** | **Thêm cột mới ở CUỐI**, sau cột cuối cùng | ⚠️ SRS nói phải chặn, nhưng `validateImportFile` trên master **chỉ kiểm cột thiếu**, không kiểm cột thừa → nhiều khả năng **LỌT**. Nếu lọt → raise bug riêng |

---

## Nhóm 5 — Regression & phạm vi

| # | Case | Kỳ vọng |
|---|---|---|
| R1 | Import file mẫu **AR (điều chỉnh) cũ**, không sửa gì | ✅ Vẫn OK như trước — chứng minh đợt 1 không đụng nhánh điều chỉnh |
| R2 | Chạy lại Nhóm 1 trên phân hệ **HĐ từ máy tính tiền** | ✅ Kết quả giống hệt — 2 phân hệ dùng chung endpoint |
| R3 | Chạy Nhóm 1 rút gọn trên **AI** (không tích) và **AL** (thay thế) | ✅ Giống AD |
| **R4** | **Soi các cột SAU cột CCCD** trên HĐ nháp vừa tạo: SĐT, Email, người nhận, hình thức thanh toán, ngân hàng, loại tiền, tỷ giá, chiết khấu, **toàn bộ dòng hàng** | ✅ **Không lệch trường** — đây là rủi ro số 1 của task, phải soi từng cột |
| R5 | **Form tạo hóa đơn** (không qua import): nhập CCCD `101099001234` | ✅ **Vẫn cho lưu** — form giữ luật cũ `^[0-9]{12}$`, ngoài phạm vi task. Đây là **lệch có chủ đích**, không phải bug |
| R6 | Form tạo hóa đơn: nhập `001099001234` | ✅ OK |
| R7 | Mẫu 4 (HĐ bán hàng dự trữ quốc gia), người mua **không MST** + có CCCD hợp lệ | ✅ Import được (trước đây bị `InvoiceCommonService:661` chặn) |
| R8 | Import CCCD hợp lệ → ký & phát hành | ✅ `CCCDan` xuất hiện đúng trong XML gửi CQT |
| R9 | **AL**: `Ký hiệu + Số HĐ gốc` trỏ hóa đơn của tenant khác | ✅ **404**, không phải 403 |
| R10 | UI: text `(cập nhật ngày: …)` hiện **cùng dòng, sau link** tải mẫu ở "Hóa đơn mới" / "Hóa đơn thay thế" | ✅ Đúng Figma · **ngày khớp ngày merge master thật** |
| R11 | UI: chọn **"Hóa đơn điều chỉnh"** | ✅ Text bị **ẩn** · link vẫn trả file `AR` cũ và import bình thường |

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

**2. Email báo cáo** — đúng số dòng lỗi, message nguyên văn, số hàng trỏ đúng dòng Excel.

**3. Màn chi tiết hóa đơn** — ô "Căn cước công dân" hiển thị đủ 12 số kể cả số `0` đầu.

## Gợi ý bộ file cần tạo

| File | Template | Nội dung |
|---|---|---|
| 1 | AD | Nhóm 1 — 20 dòng (V1–V9, E1–E11), mỗi dòng 1 hóa đơn |
| 2 | AD | Nhóm 2 — 4 dòng, tự đổi định dạng ô từng dòng |
| 3 | AD | Nhóm 3 — 5 hóa đơn, mỗi HĐ 3 dòng hàng |
| 4–8 | AD | Nhóm 4 — mỗi case S1–S5 một file |
| 9 | AI | Nhóm 1 rút gọn (V2, V8, E1, E10) |
| 10 | AL | Nhóm 1 rút gọn + case R9 |
| 11 | AR **cũ** | R1 — không sửa gì, chỉ để chứng minh không vỡ |
