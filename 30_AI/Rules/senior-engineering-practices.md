---
created: 2026-07-29 15:00
scope: "Master rule — nguyên tắc AI collaboration áp dụng cho mọi dự án"
---

# Senior Engineering Practices

Nguyên tắc chung khi cộng tác với AI (Claude, Cursor...) trên bất kỳ dự án nào — rút ra từ kinh nghiệm thực tế xây dựng `ai-workspace` cho dự án Sapo Invoice (xem [[10_Projects/sapo-invoice/README]]), sau đó tổng quát hóa: bỏ phần đặc thù Java/React, giữ lại phần đúng với mọi stack.

Không copy nguyên tắc dưới đây vào một dự án cụ thể — dự án nào cần bản đặc thù stack, viết riêng trong `ai-workspace`/rules-file của dự án đó (One Source of Truth: nguyên tắc chung ở đây, chi tiết stack ở project).

---

## 1. Quy trình "senior mode"

```
Hiểu yêu cầu → Xác định phạm vi/dự án → Đọc rules & context liên quan
→ Approach ngắn (trước khi code) → Thay đổi nhỏ, review được → Verify
```

Không nhảy thẳng vào code khi chưa xác định rõ phạm vi ảnh hưởng và đã đọc convention của dự án đó.

## 2. Đánh dấu giả định rõ ràng

Khi phải giả định điều gì đó chưa được xác nhận (yêu cầu chưa rõ, hành vi hệ thống chưa kiểm chứng), đánh dấu bằng ⚠️ ngay trong output — không âm thầm giả định rồi trình bày như sự thật.

## 3. Risk level cho quyết định

Mọi quyết định kỹ thuật đáng kể nên đi kèm mức rủi ro: **LOW / MED / HIGH**. Giúp người đọc (hoặc Claude ở phiên sau) biết cái gì cần xem kỹ trước khi chấp nhận.

## 4. Thứ tự ưu tiên khi review code

```
Security > Correctness > Performance > Readability
```

Khi review, chỉ ra vấn đề theo đúng thứ tự này — không dành nhiều công sức bàn về style code trong khi có lỗ hổng bảo mật chưa được nhắc tới.

## 5. Xử lý bug: root cause trước, triệu chứng sau

Khi phân tích bug, bắt đầu bằng giả thuyết nguyên nhân gốc rễ, không chỉ liệt kê triệu chứng. Đưa 2-3 phương án fix kèm đánh đổi, để người quyết định chọn — không tự chọn 1 phương án duy nhất khi có đánh đổi đáng cân nhắc.

## 6. Chọn công cụ/MCP theo loại tác vụ, không theo thói quen

Trước khi thực hiện một tác vụ, xác định loại tác vụ trước (tra cứu docs thư viện, query dữ liệu, test UI, thao tác git, suy luận nhiều bước phức tạp...), rồi chọn công cụ/MCP phù hợp nhất cho loại đó. Danh sách MCP cụ thể (endpoint DB, profile browser...) thuộc về từng dự án — xem `AGENTS.md`/`ai-workspace` của dự án đó, không lặp lại ở đây.

## 7. Review code: trích dẫn cụ thể, đưa code đã sửa

Khi review, luôn tham chiếu file + dòng cụ thể, và đưa code đã sửa thay vì chỉ mô tả vấn đề bằng lời — giảm vòng lặp qua lại không cần thiết.

---

## Nguồn gốc & cách cập nhật

Rút ra từ `ai-workspace/rules/claude-instructions.md` và `AGENTS.md` (dự án Sapo Invoice, workspace `/Users/sapo/invoice/`). Khi phát hiện một nguyên tắc mới đúng cho nhiều dự án (không chỉ một dự án cụ thể), thêm vào đây. Nguyên tắc chỉ đúng cho một dự án/stack cụ thể thì để lại trong `ai-workspace` của dự án đó.
