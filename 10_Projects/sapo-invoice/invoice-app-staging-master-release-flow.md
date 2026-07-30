---
created: 2026-07-30 12:00
status: Accepted
project: "[[10_Projects/sapo-invoice/README]]"
---

# Quy trình release staging → master (invoice-app)

## Context

`invoice-app` (repo `bizweb-vnext-microservices/app/invoice-app`) không cho phép merge thẳng lên `master` chỉ vì code compile/lint sạch — cần quy trình duyệt qua người, không phải quyết định kỹ thuật đơn thuần.

## Decision

- **Merge lên `master` luôn chờ tester test trên `staging` trước.** Không tự merge/đề xuất merge chỉ vì staging build xanh.
- **Nếu phát hiện bug trên staging:** sửa trực tiếp trên feature branch gốc (vd `feat/popup-auto-invoice-fail-v3`), sau đó **tạo MR mới vào staging lại**, hoặc **merge thẳng vào staging không cần MR** — cả 2 cách đều chấp nhận được cho repo này.
- **Trước khi merge master:** tester + BA phải đánh giá trên staging là không còn bug và xác nhận **có thể uplive**. Sau đó **leader** review, và **leader** là người thực hiện merge master — không phải dev, không phải AI.

## Consequences

- MR vào master nên tạo ở dạng **Draft** ngay từ đầu (không phải chờ có bug mới chuyển draft) — chỉ chuyển Ready sau khi có xác nhận từ tester/BA.
- Khi làm việc cùng AI (Claude/Cursor): AI không được tự ý merge hay thúc đẩy merge MR vào master, kể cả khi mọi kiểm tra kỹ thuật (compile, test, lint) đều pass — quyết định "sẵn sàng uplive" thuộc về người, không phải máy.
- Nếu feature branch cần merge lại vào staging nhiều lần (sau mỗi lần sửa bug), áp dụng cùng lưu ý ở [[merge-feature-branch-vao-staging-truoc-master]] nếu staging lúc đó đã tiếp tục đi xa hơn master.

## Alternatives

- Không có — đây là quy trình tổ chức đã chốt (vai trò tester/BA/leader), không phải lựa chọn kỹ thuật có thể thay thế.
