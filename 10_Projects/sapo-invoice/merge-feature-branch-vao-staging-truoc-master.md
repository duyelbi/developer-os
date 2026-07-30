---
created: 2026-07-30 11:30
status: Accepted
project: "[[10_Projects/sapo-invoice/README]]"
---

# Merge feature branch vào staging trước master — khi staging đã đi trước master rất xa

## Context

Repo `invoice-app`: `staging` thường xuyên đi trước `master` hàng trăm commit (lúc gặp việc này: 130 commit — extension field mapping, business location gating, error_code cho auto_invoice_results...). Quy trình chuẩn của dự án: 1 feature branch tạo từ `master` → merge vào `staging` để test trước → sau đó mới merge lên `master`.

Vấn đề: khi feature branch conflict với `staging` lúc tạo MR, cách resolve "mặc định" (nút Resolve conflicts của GitLab, hoặc `git merge staging` ngay trên feature branch) sẽ tạo merge-commit **ngay trên feature branch**, kéo theo toàn bộ lịch sử `staging` (kể cả các tính năng khác chưa lên `master`) làm parent của feature branch. Hậu quả: khi feature branch đó merge tiếp lên `master`, toàn bộ "rác" chưa được duyệt lên master của staging cũng đi theo.

## Decision

Không resolve conflict trên feature branch. Thay vào đó **merge theo chiều ngược lại** — merge feature branch VÀO một bản sao của staging, không phải merge staging vào feature branch:

```bash
git fetch origin
git checkout -b staging-merge-<ten-feature> origin/staging
git merge origin/<feature-branch>
# resolve conflict tại đây — branch tạm, KHÔNG phải feature branch gốc
```

Sau khi resolve xong và verify (xem mục Consequences), push thẳng lên `staging` (nếu không bị protected branch) hoặc tạo 1 MR nhỏ riêng `staging-merge-<ten-feature> → staging`:

```bash
git push origin staging-merge-<ten-feature>:staging
```

Feature branch gốc giữ nguyên — không đụng vào, để merge lên `master` sau vẫn sạch.

**Trước khi resolve nội dung xung đột thật sự**, tách file conflict thành 2 nhóm:
1. **File thật sự liên quan đến feature đang làm** — tự tin resolve (hiểu rõ cả 2 phía đang muốn gì).
2. **File hoàn toàn không liên quan** (feature branch chưa từng đụng vào — kiểm tra bằng `git log --name-only <merge-base>..<feature-branch> -- <file>` để chắc chắn) — đây là xung đột có sẵn giữa master/staging, không phải việc của feature branch này. Hỏi lại chủ dự án: đánh giá độ phức tạp (diff nhỏ/positional thường an toàn giữ nguyên staging; diff lớn/đụng logic thì nên hỏi người biết rõ 2 tính năng đó) trước khi quyết định giữ bên nào.

## Consequences

- **Bắt buộc build/test lại sau khi resolve xong toàn bộ, kể cả những file KHÔNG bị git báo conflict.** Trong lần áp dụng thực tế, git auto-merge (không báo conflict) đã âm thầm **nhân đôi 3 dòng field injection** (`@RequiredArgsConstructor` — cùng 1 dependency được thêm 2 lần ở 2 vị trí gần nhau bởi 2 nhánh khác nhau) tại `SapoInvoiceService.java`, `InvoiceWriteService.java`, `InvoiceBulkWriteService.java`. Đây là lỗi kinh điển của git 3-way merge line-based: không có conflict marker nào xuất hiện, nhưng code vẫn hỏng (duplicate field → lỗi biên dịch). **Không có conflict marker không đồng nghĩa merge đúng.**
- Cách phát hiện: `./gradlew clean compileJava compileTestJava` (clean để loại trừ nghi ngờ cache) + chạy lại toàn bộ test liên quan + lint frontend. Nếu nghi ngờ 1 nhánh (vd `staging`) tự nó có vấn đề từ trước, dùng `git worktree add /tmp/x origin/<branch> --detach` để build thử bản pristine, so sánh riêng biệt — không cần rời khỏi working tree hiện tại.
- Muốn xác nhận 1 conflict block có thật sự do feature branch gây ra không: `git diff origin/master origin/<feature-branch> -- <file>` — nếu rỗng, nghĩa là feature branch chưa từng sửa file đó, xung đột là do master/staging tự lệch nhau từ trước, không phải trách nhiệm của feature.

## Alternatives

- Rebase feature branch lên staging: cũng kéo theo lịch sử staging vào feature branch (rebase viết lại history dựa trên staging) — cùng vấn đề như merge thuận, còn thêm rủi ro force-push nếu branch đã lên MR khác (ví dụ MR draft → master cùng branch).
- Dùng nút "Resolve conflicts" của GitLab trên MR: về bản chất tạo merge-commit trên chính source branch — không tránh được vấn đề nêu trên.
