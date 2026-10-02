---
created: 2026-09-30 11:30
status: E2E trên dev xong phần chính — còn một số case chưa chạy (xem cuối file)
project: "[[10_Projects/sapo-invoice/README]]"
---

# Epic #95 — Kết quả test (unit + E2E dev)

- Plan: [[epic-95-plan]] · Prompt: [[epic-95-cursor-prompt-implement]]
- Epic [#95](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/95) · BE sapo-invoice-admin-service#191 / !614 (draft → master) · FE sapo-invoice-admin-frontend#61 / !418 (draft → master), !419 (→ dev)
- BE lên `dev` bằng merge local: commit `4950fdd71` (resolve `ImportInvoiceValidator`, sửa `InvoiceVatsFromFilePublishTest` theo constructor dev 25 tham số)
- Môi trường E2E: `https://sapo-invoice-dev.sapocorp.vn` (bản build dev đã deploy BE + FE), tenant 4 (Công ty CP Công nghệ Sapo - Test 02, MST 0103243195-999), tài khoản Ngô Văn Công
- File test + script sinh: `scratchpad/e2e/` của phiên Claude (`build.py`, `01_happy.xlsx`, `02_errors.xlsx`, `05_happy_rerun.xlsx`, `03_old_template_untick.xlsx`, `04_new_template.xlsx`). Ký hiệu dùng: `1C26TZL` (nhiều thuế suất), `1C26TDK` (1 thuế suất)

## Unit test (BE) — 67/67 pass (feature branch và `dev` sau merge)

| Class | Case |
| --- | :-: |
| `InvoiceVatsFromFileTest` (domain create/update, hướng A2-b) | 6 |
| `InvoiceImportAdjustmentVatGroupTest` (reader, validate dòng/HĐ, generate) | 8 |
| `ImportInvoiceValidatorNormalizeVatRateTest` | 16 |
| `InvoiceVatsFromFilePublishTest` (XML theo cờ, flag false = như cũ) | 3 |
| `InvoicePublishServiceTest`, `ImportRowProcessorTest`, `ImportInvoiceValidatorIdNumberTest` (hồi quy) | 34 |

FE: `pnpm lint`, `pnpm typecheck`, `oxfmt --check` pass.

## E2E — đã chạy

### Template / FE

| ID | Case | Kết quả |
| --- | --- | :-: |
| HP-10 | Nhãn "cập nhật ngày": HĐ điều chỉnh tick → 19/08/2026; bỏ tick → 29/09/2026 | ✅ |
| HP-10 | Link tải file mẫu bỏ tick trả `mau_nhap_hoa_don_DEItyFnc-*.xlsx` 97.738 byte (bản có AT–AW) | ✅ |
| ED-06 | Bỏ tick + template bỏ-tick **bản cũ** → chặn *"Nhập file thất bại — … File nhập không đúng mẫu. Vui lòng kiểm tra lại lựa chọn tự động tính toán và thực hiện tải lại file mẫu."* | ✅ (local) |
| ER-08a | Tick + template mới (có AT–AW) → chặn cùng thông báo | ✅ (local) |

### Import thành công (history `01_happy` 4/7 do 3 HĐ gốc đã có nháp từ lần test cũ; chạy lại `05_happy_rerun` 3/3)

| HĐ nháp | Case | Kết quả lưu |
| --- | --- | --- |
| 275061 | HP-01 / ED-03: dòng 8% thuế 21.601, file khai 21.600 | Bảng `8% 270000/21600/291600; 5% 420000/21000/441000` ✅ |
| 275060 | HP-03/HP-04: không khai AT–AW | Tự dẫn xuất từ dòng hàng `10% 100000/10000` ✅ |
| 275059 | HP-05/06/07: không dòng hàng; số âm; KCT trống; `21000.4567` | `8% -100000/-8000/-108000; KCT 0/0/0; 5% 420000/21000.46/441000` ✅ |
| 275058 | HP-11 + ED-01: 1 dòng hàng, 2 nhóm (3.6 + dòng chỉ khai VAT 10) | `3.6%` lưu đúng dạng, không sinh dòng hàng rỗng ✅ |
| 275057 | HP-12: không dòng hàng, AN–AS trống | 2 nhóm theo file, tổng HĐ 0 ✅ |
| 275056 | HP-02: mẫu 1 thuế suất W=8 | `8% 270000/21600/291600` ✅ |
| 275055 | A3: W=3.6, AT=3.6 | `vat_name = "3.6%"` (không còn `KHAC:`) ✅ |
| — | Reader đọc đủ 7 HĐ (code cũ dừng ở dòng chỉ khai AT–AW) | ✅ |
| — | HĐ gốc đang có HĐ điều chỉnh nháp → *"Hóa đơn đang có hóa đơn thay thế/điều chỉnh chưa xử lý"* (hành vi có sẵn) | ✅ |

### Import lỗi (`02_errors`: success 1, fail 7)

| ID | Thông báo thực tế | |
| --- | --- | :-: |
| ER-01 | Hàng 4: Thuế suất 8% bị nhập trùng trong khối Tổng tiền theo từng thuế suất | ✅ |
| ER-02 | Hàng 7, 8: Thuế suất không hợp lệ (`abc`, `8%`) | ✅ |
| ER-03 | Hàng 9: Tổng tiền chưa thuế không hợp lệ | ✅ |
| ER-04 | Hàng 10: Thuế suất không được để trống | ✅ |
| ER-05 | Hàng 11: Mẫu hóa đơn 1C26TDK chỉ hỗ trợ nhập một thuế suất trong khối Tổng tiền theo từng thuế suất | ✅ |
| ER-06 | Hàng 13: Mẫu hóa đơn 1C26TDK có Thuế suất trong khối Tổng tiền theo từng thuế suất không khớp với Thuế GTGT cả hóa đơn | ✅ |
| ER-07 | Hàng 14: Mẫu hóa đơn 1C26TDK cần có Thuế GTGT trên cả hóa đơn | ✅ |
| ER-09 | HĐ hợp lệ trong file có lỗi vẫn tạo (275062) | ✅ |

Nhận xét nhỏ: danh sách lỗi trong lịch sử import không sort theo số dòng (lỗi cấp HĐ append sau lượt lỗi dòng → "Hàng 4" đứng sau "Hàng 14").

### Hướng A2-b (Lưu trên màn chi tiết)

| Case | Kết quả |
| --- | :-: |
| 275061 mở chi tiết → "Lưu" không sửa (PUT 200, `is_auto_calculate` mặc định false) → bảng vẫn 21.600 | ✅ |
| 275058 bật "Tự động tính toán" → "Lưu" → bảng tính lại từ dòng hàng (chỉ còn 10%) | ✅ |

### XML sau phát hành (HSM SoftDream dev, không gửi email) — CQT test cấp mã (202) cả 3

| HĐ | Số | `THTTLTSuat` | Tổng HĐ | |
| --- | --- | --- | --- | :-: |
| 275061 (qua "Lưu & Phát hành") | 1C26TZL 00000159 | `8%/270000/21600`, `5%/420000/21000` | `TgTCThue 0`, `TgTThue 0`, `TgTTTBSo 0` | ✅ |
| 275056 (mẫu 1 thuế suất) | 1C26TDK 00000571 | `8%/270000/21600` | 270000 / 21600 / 291600 | ✅ |
| 275055 (thuế suất khác) | 1C26TDK 00000572 | **`KHAC:3.6%`**/100000/3600 | 100000 / 3600 / 103600 | ✅ |

- **Rủi ro #3 (plan):** 275061 có tổng nhóm ≠ tổng HĐ (0) → CQT **test** vẫn cấp mã. Chưa xác nhận môi trường thật.
- `TTHDLQuan` trỏ đúng HĐ gốc (`TCHDon=2`).
- Giới hạn: case 275056 có AU/AV = AP/AQ nên XML không phân biệt nguồn; nhánh mẫu 1 thuế suất lấy bảng đã lưu được cover bởi unit test `createInvoiceVatsUsesStoredTableWhenFlagTrueIncludingSingleRate`.

## Case chưa chạy E2E

| ID | Case | Ghi chú |
| --- | --- | --- |
| — | Mẫu 1 thuế suất có `AV ≠ AQ` → XML lấy AV | Chứng minh nguồn XML mẫu 1 thuế suất trên môi trường thật |
| HP-08 | Nhóm KCT/KKKNT có tiền, **XML `TThue = 0`** (B5) | Mới test KCT trống (275059 chưa phát hành) |
| HP-09 | `AW ≠ AU + AV` giữ nguyên | Cơ chế giống các case khác, rủi ro thấp |
| ED-04 | Mọi giá trị = 0 | Rủi ro thấp |
| ED-05 | Khai thiếu mức thuế so với dòng hàng | Rủi ro thấp |
| ER-08b | Bỏ tick + upload template tick | Cơ chế chặn như ED-06 |
| ER-10 | Mẫu bán hàng / PXK khai AT–AW | Tenant 4 chưa có HĐ gốc mẫu 2 đã phát hành |
| ED-07 | Import nhánh tick (hồi quy) trên bản dev mới | |
| ED-08 | HĐ gốc thuộc tenant khác → lỗi "HĐ gốc không tồn tại" | |
| — | "Lưu & Phát hành" sau khi **sửa dòng hàng** (bỏ tick) → XML vẫn theo file | Logic giống "Lưu" không sửa |
| — | "Xem trước" PDF trên form sửa (nghi `InvoicePreviewService` dựng từ request → bảng tính lại) | Cần xem có lệch XML không |
| — | HĐ điều chỉnh mẫu MTT (`1C26M…`) khai AT–AW | |
| — | Hồi quy import HĐ gốc / HĐ thay thế | Code không đổi reader của 2 luồng này |

## Dữ liệu test còn trên tenant 4

- Đã phát hành (không xoá được): 1C26TZL 00000159, 1C26TDK 00000571, 1C26TDK 00000572.
- Nháp: 275004–275006 (tạo bởi code cũ khi test local), 275057–275060, 275062.
- 3 HĐ gốc TZL 156/154/153 đang bị chặn lập điều chỉnh do có nháp 275004–275006.
