---
created: 2026-10-05 15:30
status: Đang làm — FE màn danh sách xong với mock (chưa commit), chờ BE sửa API theo SRS v0.21
project: "[[10_Projects/sapo-invoice/README]]"
---

# Epic #100 — [SI] Nhật ký hoạt động (log action) — ghi nhận sự kiện & màn tra cứu

- GitLab epic: [#100](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/100) (author `minhvtn2`, assignee `xamlt` · `phuongnt20` · `congnv`, labels `System::SI` · `T::Newfeature` · `tier::2`)
- Việc của mình (`duynd7`): **#24 Màn tra cứu (FE)** — chính; **#20 Nhật ký Xử lý hóa đơn (BE)**
- SRS (repo `invoice-docs`, `docs/invoice/nhat-ky-hoat-dong/`): `srs-tra-cuu-nhat-ky.md` **v0.21 (2026-10-02)** · `srs-ghi-nhan-su-kien.md` v0.50 · `bang-tong-hop-thao-tac.md` v0.37 (96 mã sự kiện, mẫu câu từng dòng) · `su-kien-a1…a6-*.md` (Phụ lục A theo nhóm)
- Thiết kế kỹ thuật: `invoice-docs` MR !156 `thiet-ke-ky-thuat.md` (chưa merge)
- Figma: [SAPO-E-INVOICE `35096:157917`](https://www.figma.com/design/7t7C9XzNP3nBJpBismG9zS/SAPO-E-INVOICE?node-id=35096-157917) (`xamlt`, 2026-09-30)

## Tóm tắt

Ghi nhận **ai làm gì, trên đối tượng nào, lúc nào, từ IP nào** trong SI và cho Chủ DN / Kế toán trưởng tự tra cứu. Kiến trúc: các bảng `_logs` có sẵn (+ `setting_change_logs` mới cho nhóm Cấu hình) → Debezium CDC → Kafka → service **`activity-log`** mới (monorepo `sapo-invoice-services`) chiếu vào Elasticsearch → `GET /api/activity_logs`. FE dựng câu mô tả + link từ dữ liệu có cấu trúc (không render HTML từ bản ghi — BR12).

## Child issues (repo `sapo-invoice-services`)

| # | Việc | Assignee | Trạng thái (2026-10-05) |
|---|---|---|---|
| #17 (#0) | Nền tảng: pipeline ingest → ES + query API | congnv | Done Code — MR !14 **chưa merge** |
| #25 (#1) | Cross-cutting: envelope IP/UA, retention, DLT | congnv | Done Code |
| #18 (#2) | Nhóm Cấu hình (diff trước→sau) | congnv | Wait to Test |
| #19 (#3) | Hóa đơn đầu ra | trongns | To do (chưa có MR) |
| #20 (#4) | **Xử lý hóa đơn (TBSS/thay thế/điều chỉnh)** | **duynd7** | To do |
| #21/#22 (#5/#6) | Danh mục · Đăng ký phát hành | manhtv3 | To do |
| #23 (#7) | Hóa đơn đầu vào | hungnt10 | To do |
| #24 (#8) | **Màn tra cứu (FE)** | **duynd7** | Đang làm |
| #26 (#9) | Lọc theo người thao tác + API list-actors | congnv | To do |

## Trạng thái phụ thuộc BE (đã kiểm, không đoán)

| Phần | Nhánh / MR | Vào `dev`? | Vào `master`? |
|---|---|---|---|
| Quyền `activity_log` | admin-service !607 `feat/activity-log-permission` | ✅ | ❌ |
| Emit nhóm Cấu hình (`setting_change_logs`) | admin-service `feat/activity-log-setting-change-logs` | ✅ | ❌ |
| Actor = OAuth app | admin-service !609 `feat/activity-log-actor-oauth` | ❌ | ❌ |
| Service `activity-log` + query API | services !14 `feat/activity-log-service` → master | ⚠️ không kiểm được (quyền) | ❌ |

- **Service `activity-log` đã chạy trên dev**: `GET /api/activity_logs` ở `sapo-invoice-dev.sapocorp.vn` trả 401 body `{"error":"unauthorized","error_description":"Authentication is required"}` — khác body 401 của admin-service (`{"error":"Unauthorized"}`, kể cả path không tồn tại) → gateway đã route sang service mới.
- **Quyền repo:** tài khoản `duynd7` chỉ có **Planner (level 15)** ở `sapo-invoice-services` → không clone/đọc file/xem nhánh (403); đọc code qua **API diff của MR** (`/merge_requests/14/changes`). **Phải xin quyền Developer trước khi làm #20.**
- Quy trình của congnv ở admin-service: nhánh feature → merge thẳng `dev` để test, MR vào `master` để mở chờ.

## Lệch SRS v0.21 ↔ issue #24 / API hiện tại

Chốt (user, 2026-10-05): **làm theo SRS mới nhất, congnv sẽ sửa API.**

| Hạng mục | Issue #24 / API !14 | SRS v0.21 |
|---|---|---|
| Phân trang | cursor + "Xem thêm" (`next_cursor`), không có tổng | **Theo số trang** 20/50/100 + "Từ a đến b trên tổng n" |
| Lưu bộ lọc thành tab | Có | **Không** (AC12) |
| Lọc Kết quả | Không có `result` | Có (Thành công/Thất bại) |
| Lọc Người thao tác | `actor_ids` | Cặp `actorType`+`actorId`, mục "Hệ thống" (`actorType=system`), tìm theo đuôi SĐT — API list-actors (#26) |
| Ô tìm kiếm | `actor_name` hoặc tiền tố `object_code` | + **số hóa đơn kèm ký hiệu**, không phân biệt dấu (AC5) |
| Giới hạn | — | Chỉ hiện 90 ngày gần nhất (AC8) |

## Hợp đồng API hiện tại (MR !14)

- `GET /api/activity_logs` — `from`, `to` (Instant), `function_codes[]`, `action_codes[]`, `operation_types[]`, `actor_ids[]`, `query`, `limit`, `cursor` → `{ activity_logs: ActivityEvent[], next_cursor }` (phẳng, `@JsonRootName("_")`).
- `GET /api/activity_logs/{id}` → `ActivityEvent` (chi tiết popup). Cross-tenant → 404; thiếu quyền → 403.
- Quyền: `hasAnyAuthority(full, activity_log)`.
- `ActivityEvent` (lib `sapo-invoice-common` 1.2.8): `event_code, function_code, action_code, operation_type, object_type, object_id, object_code, actor_type, actor_id, actor_name, actor_client_id, result, occurred_at, ip_address, user_agent, channel, changes[], detail`.
- ⚠️ BE ghi `actor_type = app` cho đối tác OAuth, SRS gọi `oauth2`. `event_code` BE viết thường (`config_role_update`), SRS viết hoa (`CONFIG_ROLE_UPDATE`) → FE so sánh sau khi `toUpperCase()`.

## Thư viện component

- Repo đang migrate `@sapo/ui-components` → `@sapo-finance/components`. Package DS **3.2.0 đã có trên master và dev** (registry đã có 4.0.0), nhưng **0 màn trên master dùng DS** — các màn đã migrate chỉ ở nhánh `ds-migration` (chưa merge).
- DS 3.2.0 đủ ~90% cho thiết kế: `Filters`, `FilterPanel`, `DateTimeFilter`, `PaginationBar`, `Modal`, `Badge`, `SystemState`. Thiếu: component **timeline**; `DateTimeFilter` là 3 tab preset, lệch lưới preset của Figma.
- **Chốt (user): làm bằng thư viện CŨ.** Hệ quả: job `verify` chạy `ds:scan --check` sẽ **đỏ** (473 → 479 file) — khi mở MR cần người duyệt `--allow-increase` + ghi lý do (luật repo chỉ cho dùng khi tăng có chủ ý).

## Figma — có gì

- **Màn danh sách (~9 frame):** danh sách nhóm theo ngày, hover, loading, rỗng, không kết quả, dropdown Thời gian, drawer Bộ lọc khác + panel con.
- **Popup "Chi tiết hoạt động" (~20 frame):** khung cố định (Thiết bị/IP · User-Agent · Thông tin thao tác · Nội dung chi tiết / Nội dung thay đổi). Case vẽ **chủ yếu nhóm Cấu hình** + nhập file + Hệ thống + Thất bại. Sticky note PD: *chỉ vẽ case mẫu* — case còn lại theo khung chung + Phụ lục A. Nhóm Hóa đơn/Xử lý HĐ/Danh mục/Đăng ký chưa có khung riêng → hỏi `xamlt`.

## FE #24 — đã làm (2026-10-05)

Nhánh `feat/activity-log-screen` (tách `origin/master`), repo `sapo-invoice-admin-frontend`, **chưa commit**.

| File | Nội dung |
|---|---|
| `src/types/activity-log.ts` | Type dùng chung theo `ActivityEvent` (snake_case) |
| `pages/setting/pages/activity-log/constants.ts` | 18 chức năng / 6 nhóm, 15 thao tác, màu badge, kết quả, mặc định 30 ngày |
| `.../hooks/useActivityLogFilters.ts` | Bộ lọc + từ khóa + trang lưu URL; đổi điều kiện → trang 1; chọn lại "30 ngày qua" = mặc định (không chip) |
| `.../components/ActivityLogFilters.tsx` | `Filters` cũ: Thời gian (shortcut) + drawer Người thao tác / Chức năng (gom nhóm) / Thao tác / Kết quả; chip + `labelValues` |
| `.../components/ActivityLogTimeline.tsx` | Timeline nhóm ngày (`d 'tháng' M, yyyy`, giờ theo `useDatetime`) |
| `.../utils/describeActivityLog.ts` | Dựng câu theo khuôn Bảng tổng hợp 3.2 (Đã… / …không thành công / Thêm mới thất bại bỏ mã); mẫu riêng cho nhóm Cấu hình + vài sự kiện đại diện, còn lại câu chung |
| `.../utils/getActivityLogObjectUrl.ts` | Link theo `objectType`; không link khi Xóa / `configuration` / nhập-xuất file / HĐ đầu vào |
| `.../utils/mockActivityLogs.ts` + `api.ts` | Mock 28 bản ghi qua `queryFn` — đổi sang `fetchWithBQ` khi có API mới |
| Quyền / route / menu | `Permissions.ACTIVITY_LOG`, checkbox nhóm Cấu hình (0/9), route `settings/activity_logs`, mục menu cuối Cấu hình |

Kết quả: lint ✅ · typecheck ✅ · test 95/95 (9 test mới cho dựng câu/link) · `ds:scan --check` ❌ (đã biết).

**Test trên Chrome (local dev, 2026-10-05) — pass:** menu, danh sách, phân trang (25 bản ghi, 2 trang, 50/trang), Thời gian "Hôm nay" + chip, lọc kết hợp Chức năng + Kết quả, tìm không dấu ("hung"), không kết quả + "Xem tất cả hoạt động" (xóa cả từ khóa), khoảng ngoài 90 ngày, link điều hướng SPA, `labelValues` trong drawer, console sạch. Đã sửa sau test: câu chung hạ cả chữ viết tắt ("hđ" → giữ "HĐ"), thêm mẫu `MISTAKE_SEND` / `*_STATEMENT_SIGN`.

**Chưa test được:** trạng thái "Chưa có hoạt động", lỗi, 403 (mock không sinh); link mở "Bản ghi không tồn tại" vì id mock.

**Quyết định nhỏ khi tài liệu lệch nhau:** ô tìm kiếm theo SRS (không SĐT, Figma có SĐT) · câu rỗng mặc định theo SRS · HĐ đầu vào không link (Bảng tổng hợp 02/10 thắng SRS IV.1) · màu badge các thao tác chưa có trong Figma tự đặt (SRS câu G10).

**Còn lại:** popup chi tiết · nối API thật · câu mô tả ~60 mã còn lại · tìm theo đuôi SĐT (#26) · trạng thái lỗi/403 thật.

## BE #20 — Xử lý hóa đơn

- Bảng `invoice_mistake_logs`, `invoice_statement_logs` (admin-service, có trên `dev`) **đã đúng dạng canonical** (`tenant_id, <obj>_id, verb, data, actor, created_at`) → `CanonicalLogAdapter` đọc thẳng. Thiếu cột `ip_address/user_agent/channel` (thuộc #25, blocker A5 — IP sau CDN).
- Việc: Debezium connector + `CanonicalLogMapping` + consumer (mẫu `InvoiceLogProjectorConsumer`) + topic/group trong config-override `sapo-invoice-activity-log.yml` + restart. Playbook: `services/activity-log/HUONG-DAN-TICH-HOP-BE.md` (trong MR !14).
- Code nền chỉ có ở nhánh `feat/activity-log-service` → **checkout từ nhánh này** (hoặc `dev` nếu đã merge), merge `dev` để test — không chờ master.
- Cần hỏi congnv: (1) base nhánh #20 từ đâu, !14 đã vào `dev` services chưa; (2) `CanonicalLogMapping` gán **1 `functionCode` cố định / bảng** → tách `invoice_replacement` vs `invoice_adjustment` cần intent resolver (`ProjectorConfig` đang rỗng) — ai làm.

## Chạy local / test — lưu ý

- `.env` dùng SSL mkcert trên `sapo-invoice-dev.sapocorp.vn:443` → cần dòng `127.0.0.1 sapo-invoice-dev.sapocorp.vn` trong `/etc/hosts` (đang comment).
- `node_modules/.vite/deps` thuộc **root** (lần trước chạy `sudo`) → Vite báo `EACCES`; sửa: `sudo chown -R $(whoami) node_modules/.vite`.
- Browser tích hợp của Claude chặn script Vite (`ERR_BLOCKED_BY_CLIENT`) → test qua **Claude in Chrome**.
- SSO đăng nhập ở `accounts-staging.sapo.vn` — tự đăng nhập, không để AI nhập mật khẩu.

## Câu hỏi mở

| # | Câu hỏi | Hỏi ai |
|---|---|---|
| 1 | Hợp đồng API mới: tham số phân trang, trường tổng, `result`, `actor_types`, endpoint list-actors | congnv |
| 2 | Bản API trên dev là commit nào của !14 | congnv |
| 3 | Popup cho nhóm Hóa đơn / Xử lý HĐ / Danh mục / Đăng ký | xamlt |
| 4 | Màu badge 9 thao tác chưa có trong Figma; badge có đổi màu khi thất bại (G10) | xamlt / minhvtn2 |
| 5 | Feature flag (tên, hành vi khi tắt) — chưa đạt DoR | BA/PO |
| 6 | Duyệt `--allow-increase` cho màn mới dùng thư viện cũ | lead FE / người phụ trách DS |
| 7 | Quyền Developer repo `sapo-invoice-services` | lead |
