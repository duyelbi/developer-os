# Convention — Developer OS

> **Loại tài liệu:** Quy ước vận hành
> **Phạm vi:** Cách đặt tên, cấu trúc note, linking, tag, commit — áp dụng cho toàn vault
> **Không bao gồm:** Metadata schema đầy đủ (xem `METADATA.md`), workflow chi tiết (xem `WORKFLOW.md`, chưa viết)

---

## Mục lục

1. [Nguyên tắc nền](#1-nguyên-tắc-nền)
2. [Đặt tên file](#2-đặt-tên-file)
3. [Atomic Notes](#3-atomic-notes)
4. [Frontmatter tối thiểu](#4-frontmatter-tối-thiểu)
5. [Linking](#5-linking)
6. [Tag](#6-tag)
7. [Quy ước theo module](#7-quy-ước-theo-module)
8. [Git commit](#8-git-commit)
9. [Còn để mở](#9-còn-để-mở)
10. [Changelog](#10-changelog)

---

## 1. Nguyên tắc nền

Convention này cụ thể hóa 3 nguyên tắc từ `ARCHITECTURE.md` (§2) áp dụng trực tiếp vào thao tác hàng ngày: **Atomic Notes**, **Markdown First**, **Git Friendly**. Khi một tình huống không được quy định rõ ở đây, quay về 3 nguyên tắc này để tự quyết định, thay vì để trống hoặc tạo ngoại lệ tùy tiện.

---

## 2. Đặt tên file

### 2.1 Quy tắc chung — kebab-case

Note nội dung (Knowledge, Project note, Career, Journal...) đặt tên theo **kebab-case**: chữ thường, nối bằng dấu gạch ngang, không dấu tiếng Việt, không khoảng trắng.

```
react-server-components.md
adr-chon-message-queue.md
2026-07-29-standup.md
```

Lý do: link, CLI, URL và Git diff đều xử lý kebab-case sạch hơn tên có dấu cách/dấu tiếng Việt. Nội dung bên trong note vẫn viết tiếng Việt có dấu bình thường — quy tắc này chỉ áp dụng cho **tên file**.

### 2.2 Ký tự cấm

Không dùng trong tên file: `/ \ : * ? " < > |` và khoảng trắng.

### 2.3 Ngoại lệ có chủ đích

| Trường hợp | Quy tắc | Ví dụ |
|---|---|---|
| **Journal** (`60_Journal/`) | `YYYY-MM-DD.md` (daily), `YYYY-[W]WW.md` (weekly review) | `2026-07-29.md`, `2026-W30.md` |
| **Templates** (`40_Templates/`) | Title Case theo loại note — giữ nguyên như hiện có, vì đây là tên loại hiển thị trong menu Templater, không phải note nội dung | `Bug.md`, `Decision.md`, `Knowledge.md`, `SRS.md` |
| **File hệ thống** (`80_System/`) | UPPERCASE, không kebab-case — đánh dấu đây là tài liệu luật, không phải nội dung tri thức thông thường | `ARCHITECTURE.md`, `CONVENTION.md` |
| **README của module/project** | Luôn tên `README.md` | `10_Projects/crm-revamp/README.md` |

### 2.4 Không trùng tên

Không đặt hai file trùng tên dù khác thư mục — Obsidian wikilink phân giải theo tên file toàn vault, trùng tên gây link sai không báo lỗi.

---

## 3. Atomic Notes

- **Một note = một khái niệm, một quyết định, hoặc một sự kiện.** Nếu một note cần nhiều hơn 1 câu để trả lời "note này nói về cái gì", nhiều khả năng nó đang gộp nhiều chủ đề.
- **Dấu hiệu cần tách note:** một heading H2 trong note đủ nội dung để đứng độc lập, hoặc nội dung dưới heading đó có khả năng được link tới từ ngữ cảnh khác ngoài note hiện tại.
- **Không nhồi nội dung không liên quan** vào một note chỉ vì tiện lúc viết — chi phí tách note lúc viết luôn thấp hơn chi phí dọn dẹp sau này.

---

## 4. Frontmatter tối thiểu

Schema frontmatter đầy đủ theo từng loại note (Knowledge, Bug, Decision, SRS...) nay do `METADATA.md` quy định chính thức — xem tài liệu đó thay vì suy đoán từ template.

Quy tắc chung áp dụng mọi note, nhắc lại ngắn gọn ở đây (chi tiết xem `METADATA.md` §2):

```yaml
---
created: 2026-07-29 10:00
---
```

Note thuộc **Reference-based lifecycle** (Career, Core System — xem `ARCHITECTURE.md` §7.4) thêm field `updated`.

Không tự thêm field ngoài schema trong `METADATA.md` vào một note — nếu cần field mới, sửa `METADATA.md` trước.

---

## 5. Linking

- Ưu tiên tuyệt đối `[[wikilink]]` cho liên kết nội bộ trong vault.
- Dùng alias khi tên hiển thị cần khác tên file: `[[ten-file|Tên hiển thị]]`.
- **Không copy nội dung giữa các note** — luôn link tới nguồn duy nhất (One Source of Truth, `ARCHITECTURE.md` §2). Nếu thấy mình copy-paste một đoạn giữa hai note, đó là dấu hiệu cần tách atomic note riêng rồi link tới nó từ cả hai chỗ.
- Broken link (trỏ tới note chưa tồn tại) được chấp nhận tạm thời — Obsidian đánh dấu bằng màu khác, không phải lỗi cần sửa ngay. Dọn broken link định kỳ (theo Phase 6 — Automation trong Roadmap).

---

## 6. Tag

**Hầu như không dùng tag.** Tổ chức và tìm kiếm dựa vào folder (module) + wikilink, không dựa vào `#tag`.

Lý do: xây dựng và duy trì một taxonomy tag có kiểm soát tốn công sức liên tục và dễ rối theo thời gian (tag trùng nghĩa, tag mồ côi). Folder đã trả lời "thuộc module nào", wikilink đã trả lời "liên quan tới cái gì" — tag thêm vào không giải quyết vấn đề mới.

Ngoại lệ hẹp, không mở rộng thêm nếu chưa có nhu cầu thực tế:

| Tag | Ý nghĩa | Dùng khi |
|---|---|---|
| `#draft` | Note chưa hoàn thiện, chưa sẵn sàng tham chiếu | Đang viết dở, cần quay lại |

Nếu sau này Dashboard/Dataview (Phase 5) thực sự cần filter theo trạng thái mà folder không biểu diễn được, quay lại quyết định này thay vì âm thầm thêm tag mới.

---

## 7. Quy ước theo module

| Module | Quy ước |
|---|---|
| **Projects** (`10_Projects/`) | Mỗi dự án một folder con kebab-case: `10_Projects/<ten-du-an>/`. Bên trong tối thiểu `README.md`; SRS/Decision/Bug dùng template tương ứng, đặt phẳng ngay trong folder dự án, tên mô tả ngắn gọn kebab-case. Nếu dự án cần thay thế một AI toolkit riêng (như `ai-workspace` của Sapo Invoice), tạo thêm subfolder `ai/` chứa rules/prompt đặc thù dự án — chỉ tạo khi có nội dung thật để chuyển vào, không tạo trước. |
| **Knowledge** (`20_Knowledge/`) | **Flat** — không chia domain subfolder cho tới khi có nhu cầu thực tế (xem §9). Wikilink và tên file mô tả rõ chủ đề thay cho cấu trúc thư mục. |
| **AI Workspace** (`30_AI/`) | Theo cấu trúc mục tiêu đã định trong `ARCHITECTURE.md` §4.5 (`Prompts/`, `Claude/`, `Cursor/`, `Rules/`, `MCP/`, `Workflow/`) — tạo dần khi có nội dung thật, không tạo folder rỗng trước. |
| **Journal** (`60_Journal/`) | Một file một ngày, xem §2.3. Không tạo subfolder theo tháng/năm trừ khi số lượng file gây khó điều hướng. |
| **Career** (`50_Career/`) | Note sống (Reference-based), tên mô tả rõ mục đích: `goals.md`, `quarterly-review-2026-q3.md`, không dùng tên chung chung như `notes.md`. |
| **Templates** (`40_Templates/`) | Giữ Title Case như hiện có — xem ngoại lệ §2.3. |

---

## 8. Git commit

- Format: `type(scope): mô tả ngắn`, theo tinh thần Conventional Commits — `type` gồm `feat`, `chore`, `docs`, `fix`.
- Commit theo **cột mốc rõ ràng** (một tài liệu hoàn thành, một quyết định chốt xong), không commit từng note nháp nhỏ lẻ trong Inbox.
- Không commit file đã bị `.gitignore` loại trừ (workspace state, cache, plugin binary — xem `.gitignore` ở root).

---

## 9. Còn để mở

Một quyết định trong `ARCHITECTURE.md` §12.2 vẫn áp dụng **default tạm thời** (đúng tinh thần Evolutionary Design):

| Chủ đề | Default tạm thời trong Convention này | Khi nào xét lại |
|---|---|---|
| Knowledge taxonomy | Flat (§7) | Khi `20_Knowledge/` vượt khoảng 50 note và flat gây khó tìm |

Project skeleton đã chốt ở Phase 4 (project thật đầu tiên — Sapo Invoice): tối thiểu `README.md` với frontmatter `status` (xem `METADATA.md` §3.5), phần còn lại tự do — không có bộ file bắt buộc cố định. Tag strategy và naming convention đã chốt từ phiên trước — xem `ARCHITECTURE.md` §12.3.

---

## 10. Changelog

| Phiên bản | Ngày | Thay đổi |
|---|---|---|
| v1 | 2026-07-29 | Bản đầu tiên: naming (kebab-case), atomic notes, frontmatter tối thiểu, linking, tag (hầu như không dùng), quy ước module, git commit |
| v1.1 | 2026-07-29 | §4 trỏ sang `METADATA.md` làm nguồn chính thức cho schema frontmatter, thay vì quy tắc tạm thời |
| v1.2 | 2026-07-29 | §9: Project skeleton đã chốt (Phase 4, project Sapo Invoice) — chỉ còn Knowledge taxonomy là quyết định mở |
| v1.3 | 2026-07-29 | §7: thêm quy ước subfolder `ai/` trong project — cho quyết định developer-os thay thế AI toolkit riêng của dự án (Sapo Invoice / `ai-workspace`) |

---

_Tài liệu thuộc Core System. Khi quy ước thay đổi, cập nhật file này, rồi rà soát note hiện có nếu cần điều chỉnh theo._
