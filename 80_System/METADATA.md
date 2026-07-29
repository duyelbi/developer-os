# Metadata Schema — Developer OS

> **Loại tài liệu:** Data contract
> **Phạm vi:** Field frontmatter (YAML) cho từng loại note — nền tảng để Dataview (Phase 5) truy vấn được
> **Không bao gồm:** Cách viết truy vấn Dataview cụ thể (thuộc Phase 5 — Dashboard, xem `ARCHITECTURE.md` §11)

---

## Mục lục

1. [Nguyên tắc](#1-nguyên-tắc)
2. [Field phổ quát](#2-field-phổ-quát)
3. [Schema theo loại note](#3-schema-theo-loại-note)
4. [Xung đột đã phát hiện & xử lý](#4-xung-đột-đã-phát-hiện--xử-lý)
5. [Định dạng giá trị](#5-định-dạng-giá-trị)
6. [Còn để mở](#6-còn-để-mở)
7. [Changelog](#7-changelog)

---

## 1. Nguyên tắc

Tài liệu này thay thế quy tắc "frontmatter tối thiểu tạm thời" ở `CONVENTION.md` §4 — từ giờ đây là nguồn chính thức duy nhất cho câu hỏi "note loại X cần field gì". Ba nguyên tắc chi phối:

- **Không thêm field ngoài schema ở đây.** Nếu một note cần dữ liệu mới, sửa tài liệu này trước, rồi mới thêm vào template — không âm thầm thêm field lẻ tẻ vào một note rồi để đó.
- **Field phải phục vụ mục đích cụ thể** (điều hướng, lọc trong Dataview sau này, hoặc phản ánh lifecycle). Không thêm field "để sau này có thể cần".
- **Nhất quán với Tag strategy đã chốt** (`ARCHITECTURE.md` §12.3): không dùng field `tags` để thay cho tổ chức bằng folder + wikilink.

---

## 2. Field phổ quát

Mọi note, không phân biệt loại, đều có:

| Field | Bắt buộc | Mô tả |
|---|---|---|
| `created` | Có | Thời điểm tạo note, định dạng `YYYY-MM-DD HH:mm` |

Note thuộc **Reference-based lifecycle** (Career, Core System — `ARCHITECTURE.md` §7.4) có thêm:

| Field | Bắt buộc | Mô tả |
|---|---|---|
| `updated` | Có | Lần cập nhật gần nhất, cùng định dạng với `created` |

Note thuộc Flow-based (Projects, Knowledge, Learning) và Log-based (Journal) **không cần** `updated` — Obsidian đã tự theo dõi "last modified" ở cấp file, không cần trùng lặp trong frontmatter.

---

## 3. Schema theo loại note

### 3.1 Knowledge (`20_Knowledge/`, template `Knowledge.md`)

| Field | Bắt buộc | Giá trị |
|---|---|---|
| `created` | Có | Datetime |
| `updated` | Có | Datetime — Knowledge có thể được bổ sung nhiều lần khi hiểu sâu hơn, nên giữ `updated` dù về lifecycle nó là Flow-based (ngoại lệ có chủ đích, xem §4) |

Không có field `tags` — xem §4.

### 3.2 Bug (`10_Projects/<ten-du-an>/`, template `Bug.md`)

| Field | Bắt buộc | Giá trị |
|---|---|---|
| `created` | Có | Datetime |
| `status` | Có | `Open` \| `In Progress` \| `Resolved` \| `Closed` |
| `priority` | Không | `P0` \| `P1` \| `P2` \| `P3` (P0 = chặn release) |
| `project` | Có | Wikilink tới README của dự án, vd `"[[10_Projects/ten-du-an/README]]"` |

### 3.3 Decision / ADR (template `Decision.md`)

| Field | Bắt buộc | Giá trị |
|---|---|---|
| `created` | Có | Datetime |
| `status` | Có | `Proposed` \| `Accepted` \| `Rejected` \| `Superseded` |

Khi một Decision bị thay thế, đổi `status` thành `Superseded` và thêm link tới quyết định mới trong nội dung — không xóa Decision cũ (Documentation as Code: lịch sử quyết định là tài sản).

### 3.4 SRS (template `SRS.md`)

| Field | Bắt buộc | Giá trị |
|---|---|---|
| `created` | Có | Datetime |
| `status` | Có | `Draft` \| `Approved` \| `Implemented` |

### 3.5 Project (README của `10_Projects/<ten-du-an>/`)

Chốt cùng lúc với Project entry thật đầu tiên (Sapo Invoice, Phase 4):

| Field | Bắt buộc | Giá trị |
|---|---|---|
| `created` | Có | Datetime |
| `status` | Có | `Active` \| `Paused` \| `Archived` |

Không thêm field mô tả danh sách repo con trong frontmatter (danh sách dài, không đều, không phù hợp query) — ghi trong nội dung note dưới dạng danh sách thường.

### 3.6 Career (`50_Career/`)

Chỉ dùng field phổ quát (`created`, `updated`) — Reference-based, xem §2. Chưa cần field riêng cho tới khi có nhu cầu cụ thể (vd. đo tiến độ mục tiêu).

### 3.7 Journal (`60_Journal/`)

Chỉ dùng `created` — Log-based, xem §2. Không có template riêng trong `40_Templates/` hiện tại; khi tạo, chỉ cần field này.

### 3.8 Learning (`70_Learning/`)

Chỉ dùng `created` — Flow-based, xem §2. Không có template riêng hiện tại.

### 3.9 Prompt (`30_AI/Prompts/`)

| Field | Bắt buộc | Giá trị |
|---|---|---|
| `created` | Có | Datetime |
| `scope` | Có | Mô tả ngắn phạm vi áp dụng, vd `"Master prompt — toàn bộ dự án"` hoặc `"Task-specific — code review"` |

Content Module AI Workspace (§3.1 `ARCHITECTURE.md`) — không dùng lifecycle Reference-based dù prompt có thể được sửa nhiều lần; `scope` đủ để phân biệt, chưa cần `updated` tới khi có nhiều prompt và cần biết cái nào mới nhất.

### 3.10 Rules (`30_AI/Rules/` và `10_Projects/<ten-du-an>/ai/`)

Cùng schema với Prompt (§3.9): `created` + `scope`.

Áp dụng cho cả hai nơi: `30_AI/Rules/` (nguyên tắc tổng quát, nhiều dự án) và `10_Projects/<ten-du-an>/ai/` (rules/prompt đặc thù một dự án — vd `10_Projects/sapo-invoice/ai/rules-backend.md`, dùng khi developer-os thay thế một AI toolkit riêng của dự án đó). Cùng schema vì cùng bản chất: tài liệu hướng dẫn AI, khác nhau ở phạm vi áp dụng (`scope` đã tự phân biệt, không cần field riêng).

### 3.11 Module Index (`README.md` của mỗi folder cấp 1: `00_Inbox/`, `20_Knowledge/`, `30_AI/`, `40_Templates/`, `50_Career/`, `60_Journal/`, `70_Learning/`, `80_System/`, `99_Archive/`)

| Field | Bắt buộc | Giá trị |
|---|---|---|
| `created` | Có | Datetime |

Không cần `status` hay `updated` — đây là trang chỉ mục tĩnh (mục đích module, link tới tài liệu/nội dung liên quan), không phải workflow item. Mục đích duy nhất: cho wikilink từ Home (`[[00_Inbox]]`...) có nơi thật để mở, thay vì trỏ vào folder không tồn tại dưới dạng note (Obsidian không tự mở folder qua wikilink).

`10_Projects/` cũng cần một README cùng schema này (chỉ `created`) để liệt kê danh sách dự án — khác với README của từng dự án con bên trong (dùng schema Project, §3.5).

---

## 4. Xung đột đã phát hiện & xử lý

Template `40_Templates/Knowledge.md` hiện có field `tags:` trong frontmatter — mâu thuẫn trực tiếp với Tag strategy đã chốt ở `ARCHITECTURE.md` §12.3 ("hầu như không dùng tag — dựa vào folder + wikilink"). Field này được tạo trước khi Tag strategy được quyết định chính thức.

**Xử lý:** xóa field `tags` khỏi `Knowledge.md`. Tổ chức Knowledge dựa vào tên file mô tả rõ + wikilink, đúng như `CONVENTION.md` §6 đã quy định.

---

## 5. Định dạng giá trị

- **Datetime:** `YYYY-MM-DD HH:mm`, khớp cú pháp Templater đang dùng (`<% tp.date.now("YYYY-MM-DD HH:mm") %>`).
- **Wikilink trong frontmatter:** luôn đặt trong dấu ngoặc kép để YAML không hiểu nhầm `[[...]]` là cú pháp mảng: `project: "[[10_Projects/ten-du-an/README]]"`.
- **Enum:** Title Case, khớp cách viết đã có sẵn trong template hiện tại (`Open`, `Accepted`...).

---

## 6. Còn để mở

| Chủ đề | Trạng thái |
|---|---|
| Field đo tiến độ cho Career | Chưa có nhu cầu cụ thể, chưa thiết kế |
| Field cho Journal/Learning ngoài `created` | Chưa có nhu cầu cụ thể |

---

## 7. Changelog

| Phiên bản | Ngày | Thay đổi |
|---|---|---|
| v1 | 2026-07-29 | Bản đầu tiên: field phổ quát, schema cho Knowledge/Bug/Decision/SRS, phát hiện và xử lý xung đột field `tags` trong template Knowledge |
| v1.1 | 2026-07-29 | Thêm §3.9 Prompt (`30_AI/Prompts/`) — field `scope`, cho artifact AI đầu tiên của vault |
| v1.2 | 2026-07-29 | Chốt §3.5 Project (field `status`) và thêm §3.10 Rules — cho Project entry Sapo Invoice và Rules đầu tiên (Phase 3-4) |
| v1.3 | 2026-07-29 | §3.10 mở rộng phạm vi sang `10_Projects/<ten-du-an>/ai/` — cho quyết định developer-os thay thế `ai-workspace` (AI toolkit riêng của dự án Sapo Invoice) |
| v1.4 | 2026-07-29 | Thêm §3.11 Module Index — schema cho README.md của mỗi folder cấp 1, sửa lỗi wikilink từ Home trỏ vào folder không có note thật |

---

_Tài liệu thuộc Core System. Khi thêm field mới cho bất kỳ loại note nào, cập nhật file này trước, rồi mới sửa template tương ứng._
