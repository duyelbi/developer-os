---
created: 2026-08-19
status: Chờ BA giao file thứ 5
project: "[[10_Projects/sapo-invoice/README]]"
---

# Bàn giao BA — thiếu 1 file mẫu import HĐ điều chỉnh (AR)

Liên quan: [[epic-62-them-cot-cccd-file-import-hoa-don]] · WI [invoice-docs#62](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/work_items/62) · issue [#125](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-service/-/work_items/125)

## Vấn đề một câu

Task **"nhập tổng tiền hóa đơn theo file"** (đã lên master ngày 18/08) đã tách hóa đơn điều chỉnh thành **2 mẫu file khác nhau**. BA giao 4 file cho task CCCD nên file AR chỉ phủ được **1 trong 2** mẫu đó. **Cần thêm 1 file thứ 5.**

## Vì sao HĐ điều chỉnh cần 2 file

Trong popup import, khi chọn "Hóa đơn điều chỉnh" có checkbox **"Tự động tính toán giá trị tổng tiền"**:

| Lựa chọn | Ý nghĩa | File mẫu |
|---|---|---|
| **Tích** | Hệ thống tự tính tổng tiền từ các dòng hàng hóa | **45 cột** — không có khối "Tổng tiền hóa đơn" |
| **Bỏ tích** | Lấy tổng tiền theo giá trị **đã điền sẵn trên file** | **52 cột** — có thêm khối "Tổng tiền hóa đơn" (6 cột) |

Hai mẫu giống hệt nhau ở 45 cột đầu, chỉ khác đúng khối cuối:

```
Tổng tiền hóa đơn  (chỉ có ở mẫu BỎ TÍCH)
├ Tổng tiền hàng            ├ Tổng tiền thuế
├ Tổng tiền chiết khấu      ├ Tiền thuế GTGT được giảm
└ Tổng tiền chưa thuế       └ Tổng tiền thanh toán
```

> **Lưu ý về hiểu nhầm trước đây:** trước tháng 8/2026 hệ thống chỉ kiểm cột **thiếu**, không kiểm cột **thừa** — nên file 52 cột nạp được cho cả 2 lựa chọn, dễ tưởng "tích hay bỏ tích cũng như nhau". Task tính tổng đã siết lại: **thừa cột cũng bị chặn**. Từ giờ mỗi lựa chọn phải đúng file của nó.

## File BA đã giao ứng với mẫu nào

File `AR_Hoa_don_HD_dieu_chinh_mau_nhap_hoa_don.xlsx` (24/07) có **53 cột** = mẫu **BỎ TÍCH** (52 cột) + 1 cột CCCD. ✅ Dùng được ngay cho nhánh bỏ tích.

**Còn thiếu:** mẫu **TÍCH TỰ ĐỘNG** + CCCD → phải có **46 cột**.

## Cách làm nhanh nhất (đã kiểm chứng)

Đã đối chiếu bằng chương trình: **46 cột đầu (A→AM) của file BA đã giao chính xác bằng file thứ 5 cần có.** Nên:

> Mở file `AR_Hoa_don_HD_dieu_chinh_mau_nhap_hoa_don.xlsx` đã giao → **xóa khối "Tổng tiền hóa đơn" (cột AN đến AS)** → lưu thành file mới.

Không phải dựng lại layout, không phải căn merge lại. Xong là ra đúng file thứ 5.

## File kèm trong thư mục này

| File | Vai trò |
|---|---|
| `AR-tich-tu-dong__HIEN-HANH-chua-co-CCCD.xlsx` | Mẫu **tích tự động** đang chạy thật trên production (45 cột). Đây là file gốc cần thêm CCCD |
| `AR-bo-tich__HIEN-HANH-chua-co-CCCD.xlsx` | Mẫu **bỏ tích** đang chạy thật (52 cột) — để đối chiếu |
| `AR-bo-tich__BA-DA-GIAO-co-CCCD.xlsx` | File BA giao 24/07 (53 cột) — đã đúng cho nhánh bỏ tích |

## Vị trí cột CCCD (giống hệt 3 mẫu AD/AI/AL đã duyệt)

Chèn cột **"Căn cước công dân"** vào **K2:K3**, giữa "Người mua hàng" và "Số điện thoại". Khối merge "Thông tin người mua" mở rộng `F1:L1` → `F1:M1`. Mọi cột từ K trở đi dịch phải 1 cột:

| Tiêu đề | Hiện tại | Sau khi thêm CCCD |
|---|---|---|
| Thông tin người mua | F1:L1 | **F1:M1** |
| Người mua hàng | J2:J3 | J2:J3 |
| **Căn cước công dân** | — | **K2:K3** ← thêm mới |
| Số điện thoại | K2:K3 | L2:L3 |
| Email | L2:L3 | M2:M3 |
| Thông tin người nhận | M1:N1 | N1:O1 |
| Thông tin giao dịch | O1:S1 | P1:T1 |
| Chiết khấu cả hóa đơn | T1:U2 | U1:V2 |
| Thuế GTGT cả hóa đơn (%) | V1:V3 | W1:W3 |
| Thông tin hàng hóa, dịch vụ | W1:AL1 | X1:AM1 |
| Tổng tiền | AL2:AL3 | AM2:AM3 |

**Định dạng ô cột CCCD phải là Text (`@`)** — giống 4 file đã giao. Để General/Number thì Excel cắt số 0 đầu ngay lúc người dùng gõ (`001099001234` → `1099001234`), server không khôi phục được và sẽ báo lỗi định dạng.

## Cách tự kiểm trước khi giao

File đúng phải có **đúng 46 tiêu đề** ở 3 dòng đầu. Thừa hoặc thiếu 1 cột là hệ thống chặn toàn bộ file với thông báo *"File nhập không đúng mẫu…"*.

## Phương án thay thế — nếu BA muốn giữ 1 file duy nhất

Về mặt code, `InvoiceHeaderAdjustmentImport` (mẫu 45 cột) chỉ được dùng ở **đúng 1 chỗ** trong toàn hệ thống. Bỏ nhánh đó đi, luôn nhận mẫu 52 cột cho HĐ điều chỉnh thì:

- 1 file mẫu AR phục vụ cả tích lẫn bỏ tích → **không cần file thứ 5**
- Khi tích, hệ thống đọc khối tổng tiền rồi **bỏ qua**, tự tính từ dòng hàng — đúng như spec hiện tại
- File BA đã giao là đủ, làm được ngay

Đánh đổi: khách đang giữ file AR 45 cột cũ sẽ bị chặn — nhưng dù sao họ cũng phải tải lại vì có cột CCCD mới.

→ **Cần BA quyết:** giao thêm file thứ 5, hay gộp về 1 mẫu duy nhất.
