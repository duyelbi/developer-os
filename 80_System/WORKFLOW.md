# Workflow — Developer OS

> **Loại tài liệu:** Hướng dẫn thao tác
> **Phạm vi:** Chi tiết hóa Data Flow ở `ARCHITECTURE.md` §6 thành các bước cụ thể — dùng template nào, đổi field nào, khi nào chuyển trạng thái
> **Không bao gồm:** Lý do thiết kế luồng (xem `ARCHITECTURE.md` §6), schema field (xem `METADATA.md`)

---

## Mục lục

1. [Luồng chính — Developer Workflow](#1-luồng-chính--developer-workflow)
2. [Luồng phụ: Bug](#2-luồng-phụ-bug)
3. [Luồng phụ: Decision (ADR)](#3-luồng-phụ-decision-adr)
4. [Luồng phụ: Learning → Knowledge](#4-luồng-phụ-learning--knowledge)
5. [Luồng phụ: Journal](#5-luồng-phụ-journal)
6. [Checklist nhanh](#6-checklist-nhanh)
7. [Còn để mở](#7-còn-để-mở)
8. [Changelog](#8-changelog)

---

## 1. Luồng chính — Developer Workflow

Mở rộng `ARCHITECTURE.md` §6.1 thành thao tác cụ thể theo từng bước:

| Bước | Hành động | Template / field liên quan |
|---|---|---|
| **Requirement** | Ghi vấn đề cần giải vào `10_Projects/<ten-du-an>/`. Nếu chưa rõ dự án nào, ghi tạm vào `00_Inbox` rồi promote sau (`CONVENTION.md` §7.5). | `SRS.md`, `status: Draft` |
| **Claude** | Dùng Claude Code phân tích, làm rõ yêu cầu, sinh hướng tiếp cận. Ghi lại phân tích trực tiếp trong SRS hoặc note riêng cùng dự án. | — |
| **Planning** | Chốt hướng đi, chia việc. Nếu có quyết định kỹ thuật đáng ghi nhớ (chọn thư viện, đổi kiến trúc), tạo Decision. Cập nhật SRS `status: Approved`. | `Decision.md`, `status: Proposed` → `Accepted` |
| **Cursor** | Hiện thực hóa code. Không ghi log implementation chi tiết vào vault trừ khi có quyết định/bài học đáng giữ lại. | — |
| **Code Review** | Nếu phát hiện lỗi, tạo Bug note. Nếu review sinh ra bài học kỹ thuật, ghi lại (tạm thời trong Project, sẽ promote ở bước sau). | `Bug.md`, `status: Open` |
| **Knowledge** | Trước khi đóng SRS (`status: Implemented`), rà soát xem có bài học nào đủ ổn định để promote sang `20_Knowledge/` không (`CONVENTION.md` §7.5 — quy tắc promote). | `Knowledge.md` |
| **Archive** | Khi dự án hoặc feature không còn active, chuyển toàn bộ folder dự án sang `99_Archive/` (giữ nguyên cấu trúc con). | — |

---

## 2. Luồng phụ: Bug

```text
Phát hiện bug → tạo Bug note (status: Open)
      → xác định priority (P0–P3, xem METADATA.md §3.2)
      → sửa xong → status: Resolved
      → xác nhận không tái phát → status: Closed
```

- Bug note luôn đặt trong folder dự án liên quan, field `project` trỏ wikilink tới README dự án đó.
- Bug không tự động promote sang Knowledge. Chỉ khi nguyên nhân gốc rễ là một pattern có thể tái sử dụng (không riêng dự án này), tách thành Knowledge note riêng và link ngược từ Bug.

---

## 3. Luồng phụ: Decision (ADR)

```text
Có quyết định kỹ thuật cần ghi nhớ → tạo Decision (status: Proposed)
      → thảo luận/xác nhận → status: Accepted
      → (nếu sau này bị thay thế) → status: Superseded, link tới Decision mới
```

Tiêu chí tạo Decision: quyết định ảnh hưởng lâu dài hoặc khó đảo ngược (chọn công nghệ, đổi kiến trúc, đổi convention). Không tạo Decision cho lựa chọn nhỏ, dễ đổi.

---

## 4. Luồng phụ: Learning → Knowledge

```text
Đang học (70_Learning/) → thực hành trong Project hoặc qua AI
      → hiểu và áp dụng được ít nhất 1 lần (điều kiện promote, CONVENTION.md §7.5)
      → tạo Knowledge note, KHÔNG copy nguyên note Learning
      → note Learning có thể giữ lại làm lộ trình/log học, không xóa
```

---

## 5. Luồng phụ: Journal

```text
Cuối ngày/tuần → ghi vào 60_Journal/YYYY-MM-DD.md
      → nếu có insight đủ giá trị tái sử dụng → tách thành Knowledge/Project note/Career note riêng
      → Journal gốc giữ nguyên, không archive theo khối (ARCHITECTURE.md §7.3)
```

---

## 6. Checklist nhanh

- Bắt đầu việc mới, chưa rõ thuộc đâu → ghi `00_Inbox`.
- Bắt đầu một dự án/feature → `SRS.md` trong `10_Projects/<ten-du-an>/`.
- Quyết định kỹ thuật đáng nhớ → `Decision.md`.
- Gặp lỗi → `Bug.md`, gắn `project`.
- Học được điều tái dùng được → `Knowledge.md`, không tag, tên file mô tả rõ.
- Cuối ngày → `Journal`.
- Dự án/feature xong → rà soát promote Knowledge → chuyển vào `99_Archive/`.

---

## 7. Còn để mở

Workflow cho Career (review định kỳ) và AI asset improvement (`ARCHITECTURE.md` §6.4) chưa chi tiết hóa — chưa có đủ thực tế sử dụng để viết cụ thể hơn mức đã mô tả ở `ARCHITECTURE.md`. Bổ sung khi có nhu cầu thật (Evolutionary Design).

---

## 8. Changelog

| Phiên bản | Ngày | Thay đổi |
|---|---|---|
| v1 | 2026-07-29 | Bản đầu tiên: luồng chính chi tiết hóa từ ARCHITECTURE §6, luồng phụ Bug/Decision/Learning/Journal, checklist nhanh |

---

_Tài liệu thuộc Core System. Khi luồng thực tế thay đổi, cập nhật file này trước, rồi rà soát Template/METADATA nếu field bị ảnh hưởng._
