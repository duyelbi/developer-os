---
created: 2026-10-05 15:30
status: Đang làm — FE màn danh sách (mock) draft !424/!425; BE #20 xong code (!618/!624 admin, !21/!23 services), config-override + connector ✅; **services đã vào dev** (`8293356`, 2026-10-08) — chờ pipeline deploy + admin !624 để test e2e
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
| #19 (#3) | Hóa đơn đầu ra | trongns | To do (chưa có nhánh, 2026-10-07) |
| #20 (#4) | **Xử lý hóa đơn (TBSS/thay thế/điều chỉnh)** | **duynd7** | services ✅ vào dev (!23 merged 2026-10-08); admin !624 (→dev) chờ merge; !618 / !21 (→master) draft |
| #21/#22 (#5/#6) | Danh mục · Đăng ký phát hành | manhtv3 | Consumer đã vào `dev` (`1aa6ee7`, 2026-10-06, nhánh `feat/activity-log-catalog-registration`) |
| #23 (#7) | Hóa đơn đầu vào | hungnt10 | To do |
| #24 (#8) | **Màn tra cứu (FE)** | **duynd7** | Đang làm |
| #26 (#9) | Lọc theo người thao tác + API list-actors | congnv | To do |

## Trạng thái phụ thuộc BE (đã kiểm, không đoán)

| Phần | Nhánh / MR | Vào `dev`? | Vào `master`? |
|---|---|---|---|
| Quyền `activity_log` | admin-service !607 `feat/activity-log-permission` | ✅ | ❌ |
| Emit nhóm Cấu hình (`setting_change_logs`) | admin-service `feat/activity-log-setting-change-logs` | ✅ | ❌ |
| Actor = OAuth app | admin-service !609 `feat/activity-log-actor-oauth` | ❌ | ❌ |
| Service `activity-log` + query API | services !14 `feat/activity-log-service` → master | ✅ | ✅ merge 2026-10-07 08:38 (`68fcc61`, nhánh nguồn đã xóa) |

- **Service `activity-log` đã chạy trên dev**: `GET /api/activity_logs` ở `sapo-invoice-dev.sapocorp.vn` trả 401 body `{"error":"unauthorized","error_description":"Authentication is required"}` — khác body 401 của admin-service (`{"error":"Unauthorized"}`, kể cả path không tồn tại) → gateway đã route sang service mới.
- **Quyền repo:** ~~Planner (15) qua group → 403~~ → **đã được cấp Developer (30) cấp project (2026-10-07)**. Đã clone `~/invoice/sapo-invoice-services` (đang ở `dev`). Ghi nhớ: Reporter (20) mới clone được; Developer (30) mới push/mở MR; **không cần Owner**.
- **Lib `sapo-invoice-common`** (`sapo-invoice-libs/sapo-invoice-common`): !15 capture-kit ✅ master (2026-09-22); !16 model + `ActorType.app` (1.2.8) ❌ còn mở dù 1.2.8 đã có trên Nexus.
- **admin-service `master`** chỉ có !584 `feature/decimal-config-log` (bảng `decimal_configuration_logs`, 2026-09-23) — bản làm sớm, đã bị `setting_change_logs` thay ở nhánh `feat/activity-log-setting-change-logs` (chỉ vào `dev`, **chưa có MR vào master**).
- Quy trình của congnv ở admin-service: nhánh feature → merge thẳng `dev` để test, MR vào `master` để mở chờ.
- ⚠️ **2026-10-08: `master` admin-service bị force-push** — gỡ bộ refactor khóa số hóa đơn MR !521 (~47 commit, backup ở `backup/inv-no-1.2a-snapshot` / !623), master = `fc31a940e` + `0ac40c682` (hungnt10). Nhánh tách từ master cũ (`45528e216`) sẽ kéo bộ đó quay lại master → phải rebase. Kiểm: `git reflog show origin/master` thấy `forced-update`. **Điểm chung master ∩ dev = `fc31a940e`** — tách từ đây thì 1 nhánh MR sạch vào cả master lẫn dev. MR !614 (#95) không bị ảnh hưởng (tách từ `3d6e0beda`, merge thử sạch).

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

Nhánh `feat/activity-log-screen` (tách `origin/master`), repo `sapo-invoice-admin-frontend`, commit `72a356b3` + `69745e2e` (sửa link biên bản → `/admin/invoice-statement/:id`; `.../replaced-invoices/statement/:id` nhận **id hóa đơn**). Draft MR: [!424 → master](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-frontend/-/merge_requests/424) (19 file) · [!425 → dev](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-frontend/-/merge_requests/425) (37 file — kéo theo 3 commit master chưa vào dev: tool DS + `/shipit`, **chốt giữ nguyên**).

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

**Còn lại:** popup chi tiết · nối API thật · câu mô tả ~60 mã còn lại (gồm mã mới của #20: `MISTAKE_CREATE/_UPDATE/_DELETE`, `*_STATEMENT_CREATE/_UPDATE/_SEND/_DELETE/_BUYER_SIGNED` đang rơi về câu chung) · tìm theo đuôi SĐT (#26) · trạng thái lỗi/403 thật.

## BE #20 — Xử lý hóa đơn (implement 2026-10-07/08)

### Điều tra (tóm tắt)
- 2 bảng `invoice_mistake_logs` / `invoice_statement_logs` đúng dạng canonical nhưng `verb` thô: gửi CQT, CQT phản hồi, ký, gửi bên mua, bên mua ký, rollback đều `update`. `data` = snapshot; biên bản có `document_type` (`cancel/replace/modify`).
- Chỉ copy consumer (như #21/#22 của manhtv3) → sai mã sự kiện, sinh bản ghi rác khi CQT phản hồi (BR16), không tách Thay thế/Điều chỉnh.
- Lỗ hổng `CanonicalLogAdapter` (chung, của congnv — **không sửa**, để congnv phân công): `action_code = verb` thô, không set `object_code`, không bỏ được row không intent, 1 `functionCode`/bảng. Ảnh hưởng cả #19, #21/#22.
- Lib có sẵn 3 cơ chế intent: `IntentEventResolver` (luật T1, đọc `data.events`), `@ActivityLog` (aspect chưa viết), `activity_outbox` (chưa có consumer). `ProjectorConfig` registry đang rỗng.
- **Chốt hướng A** (producer phát domain event — khớp playbook mục 9).

### admin-service — domain event (!618 → master, !624 → dev; commit `75eedffce`)
| Aggregate | Event | Mã sự kiện |
|---|---|---|
| `InvoiceMistake` | `Created` (cờ `external` = request chỉ có `detailOthers`), `Updated` (`updateInfo`), `Sent` (`updateStatus(sent)` — chỉ luồng gửi CQT thành công), `Deleted` (`markDeleted()`) | `mistake_create` / `_create_external` / `_update` / `_send` / `_delete` |
| `InvoiceStatement` | thêm `getEvents()` `@JsonGetter`; `Created`, `Updated`, `SellerSigned`/`BuyerSigned` (chỉ khi `applyDigitalSignature` **chuyển** sang `*_signed`), `SentToBuyer` (`markSent`), `Deleted` — mang `documentType` | `replacement_statement_*` / `adjustment_statement_*` |

- Domain event **không** publish qua Spring — chỉ serialize vào `data` của log, xóa sau persist.
- Rủi ro đã chặn: `InvoiceMistakeStatusNotificationConsumer` đọc lại `data.events` qua `EventUtils.unmarshalEvents` (nuốt lỗi → rỗng → mất thông báo CQT). Event mới theo khuôn `InvoiceMistakeAcceptEvent`; test round-trip xác nhận. Event biên bản ở package mới `statement.event` (ngoài danh sách EventUtils quét).
- Test: 12 test mới (gồm test khóa tên trường `data`: `ref_no`, `details`, `tax_authority_notification_no`, `document_no`, `invoice_id`, `event_name`, `recent_status`, `external`). Full suite: 1 fail `InvoiceSellerSqlTest` **có sẵn trên master** (thiếu `toInvoiceDate`).

### services — projector (!21 → master, !23 → dev; commit `b3a8f9d`)
- `InvoiceProcessingLogAdapter` — **adapter riêng** (playbook mục 5), không đụng `CanonicalLogAdapter`/`ProjectorConfig`: dùng canonical cho actor/envelope/occurredAt; `IntentEventResolver` registry cục bộ → ghi đè `eventCode/actionCode/operationType`; `functionCode` theo `document_type`; `objectCode` = mã TB / số biên bản; `detail` = `status_from/status_to` (+ `invoice_count`, `tax_authority_notification_no` / `invoice_id`); không intent hoặc `cancel` → `null` (bỏ qua).
- `InvoiceMistakeLogProjectorConsumer`, `InvoiceStatementLogProjectorConsumer` + topic/group `application.yml`. Test 16/16 module.
- ✅ **!23 → dev đã merge (2026-10-08 09:55)** — cách làm (user chọn): `git checkout dev` + pull mới nhất → `git merge --no-ff origin/feat/activity-log-invoice-processing` → resolve `application.yml` giữ cả hai phía (4 topic/group Danh mục + 2 của #20; YAML 9/9) → test activity-log 16/16 + compile e-document → **push thẳng `dev`** (`632f537..8293356`) → GitLab tự đánh dấu !23 merged. Không merge dev ngược vào nhánh feature → !21 (→master) vẫn sạch.
- Merge kéo theo vào dev: hotfix e-document !19 của congnv (`5c270aa`, `TaxDocumentPublishService` — đã trên master từ 05/10; cũng là lý do title !23 bị lấy theo commit đó).
- Pipeline dev [#1137103](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-services/-/pipelines/1137103): test → package activity-log + e-document → deploy (= restart activity-log với consumer + config mới).

### Quy ước team: mỗi nhóm một adapter riêng (điều tra 2026-10-08)
User/congnv: `CanonicalLogAdapter` **chỉ dùng cho `invoice_logs`** — nhóm khác viết adapter riêng.

| Issue | Người | Nhánh / MR | Adapter | Mã sự kiện | `action_code` | Bỏ row không intent |
|---|---|---|---|---|---|---|
| #19 HĐ đầu ra | trongns | chưa có nhánh | (`CanonicalLogAdapter` / `invoice_logs`) | — | — | — |
| #21/#22 Danh mục + Đăng ký | manhtv3 | `feat/activity-log-catalog-registration`, !20 → master (fix `32be38b` 07/10 chưa vào dev) | `CatalogRegistrationLogAdapter` | suy từ `verb`, **VIẾT HOA** (`CUSTOMER_CREATE`) | ⚠️ `verb` thô (`add`) | ❌ |
| #23 HĐ đầu vào | hungnt10 | `feat/activity-log-invoice-collector` (chưa MR) | `InputInvoiceLogAdapter` | domain event, registry **`ProjectorConfig` chung** + enum `InputInvoiceEventCode`, viết thường | ✅ | ✅ |
| #20 Xử lý HĐ | duynd7 | !21 / !23 | `InvoiceProcessingLogAdapter` | domain event, registry **cục bộ**, viết thường | ✅ | ✅ |

- hungnt10 viết **playbook mục 10** — pattern "tái dùng `_logs` + domain event + adapter riêng, không event → bỏ" — #20 cùng hướng.
- Lệch cần thống nhất: hoa/thường của `eventCode` (chỉ manhtv3 viết HOA); `action_code` thô của manhtv3 làm bộ lọc Thao tác FE ("Thêm mới" = `create`) không ra dữ liệu Danh mục.
- manhtv3 sửa `ActivityIndexer` (bắt 409 qua `ResponseException`) — file chung, chưa vào dev/master.
- Merge vào master sẽ conflict nhỏ `application.yml` giữa !21, !20, nhánh hungnt10 (cùng khối topic/group) — giữ tất cả dòng.

### Nhánh — quy ước user chốt
- **Mỗi repo 1 nhánh** `feat/activity-log-invoice-processing`, MR vào master + dev từ cùng nhánh. Đã đóng !619/!22 và xóa nhánh `-dev` (2026-10-08). Repo không có `staging`.

### Chưa làm (follow-up)
- `MISTAKE_PREVIEW`, `MISTAKE_NOTIFY_SEND`, `*_ATTACH/_DETACH`, `REPLACEMENT_CREATE` (không ghi vào 2 bảng log → cần outbox / `@ActivityLog`).
- `result = failure`, số lượt gửi–ký, cột IP/UA/channel (#25).
- Lệch SRS D10: SRS cho sửa biên bản đã `buyer_signed`, code đang chặn — không đổi.

### Hạ tầng: Debezium · config-override · restart (2026-10-08)
**Debezium connector** = CDC trong Kafka Connect: đọc binlog MariaDB, mỗi INSERT/UPDATE ở bảng được theo dõi → 1 message vào topic `sapo_invoice.raw.<db>.<table>`. activity-log không đọc DB admin, chỉ nghe topic. "Thêm connector cho bảng" = thêm bảng vào danh sách bảng của connector (hạ tầng, ngoài code — DevOps/congnv). Kafka Connect REST trực tiếp (8083) không vào được từ máy, nhưng có **Kafka Connect UI** `http://192.168.12.25:8200/#/cluster/kafka-connect-1` + REST proxy `http://192.168.12.25:8200/api/kafka-connect-1` (`/connectors`, `/connectors/<name>/status`, `/connectors/<name>/topics`). Tên topic = `database.server.name` (`sapo_invoice.raw`) + `.<db>.<table>`.

| Bảng | Connector/topic | Ghi chú |
|---|---|---|
| `invoice_mistake_logs` | ✅ connector `sapo_invoice_invoice_mistake_logs.v1.2` → topic **`sapo_invoice.raw.sapo_invoice.invoice_mistake_logs`** (xác nhận qua `/topics`) | ❓ `sapo-invoice-admin.yml` dòng 49 khai `..._invoice_invoice_mistake_logs` (hungnt10, `888f607`, 2024-10-28 — **có từ trước, không do #20**) — **chưa xác nhận là lỗi**, xem mục dưới |
| `invoice_statement_logs` | ✅ **tạo 2026-10-08**: `invoice.sapo_invoice.invoice_statement_logs.v1.0` (congnv chỉ cách: tham khảo connector `invoice_logs`, đặt tên `invoice.<db>.<table>.v1.0`) — connector + task `RUNNING` | Topic `sapo_invoice.raw.sapo_invoice.invoice_statement_logs` chỉ xuất hiện khi bảng có dòng mới (`snapshot.mode=SCHEMA_ONLY`) |

**config-override** = repo `sapo-money/sapo-invoice/dev-ops/config-override` (nhánh `dev`; prod: `dev-ops/prod-config-override`), config server đọc lúc service khởi động. `application.yml` trong code chỉ có tên mặc định, **tên topic thật nằm ở đây**. User có Developer (30). Repo commit thẳng `dev` là chủ yếu.
- ✅ **Đã push thẳng `dev` `85724fd` + sửa tên topic mistake `f22ae37` (2026-10-08)** — `sapo-invoice-activity-log.yml` thêm `invoice-mistake-log` / `invoice-statement-log` + group `sapo-invoice.activity-log.invoice-mistake` / `.invoice-statement`. Group riêng — dùng chung group admin-service thì 2 bên giành message.
- ⚠️ Push rule "author phải là member": repo clone mới lấy email global `duylanh1818@gmail.com` → bị chặn. Đặt local `DuyND7 <duynd7@sapo.vn>` cho mọi repo công việc (`git config --local user.email duynd7@sapo.vn`).
- Clone: `~/invoice/dev-ops-config-override`.

**❓ Topic `invoice-mistake-log` trong `sapo-invoice-admin.yml` — cần xác nhận, chưa phải lỗi chắc chắn (2026-10-08)**
- Chắc chắn: key dùng bởi 2 consumer profile `job` — `InvoiceMistakeESIndexConsumer` (index ES; **màn danh sách thông báo sai sót đọc từ ES** qua `InvoiceMistakeSearchService` ← `InvoiceMistakeController`) và `InvoiceMistakeStatusNotificationConsumer`. Config-override chỉ có giá trị tên kép, không file nào ghi đè. 25 connector dev **không** cái nào ghi topic tên kép.
- Nghi vấn: nếu thật sự sai từ 2024 thì thông báo sai sót mới trên dev không lên danh sách — khó không ai phát hiện → có thể vẫn chạy vì: (1) config gốc `invoice-config-server` (user chỉ Planner, không đọc được) ghi đè giá trị lúc chạy; (2) topic tên kép có tồn tại, do nguồn khác ghi (vd connector v1.0/v1.1 cũ); (3) lỗi có thật nhưng chưa ai để ý (ít khả năng).
- Xác nhận: lập 1 thông báo sai sót mới trên dev → có lên danh sách = chạy đúng (dòng config chỉ là giá trị bị ghi đè / tên cũ); không lên = lỗi thật → báo hungnt10/congnv. Hoặc nhờ xem consumer group `sapo-invoice.invoice-mistake-es-index` đọc topic nào.
- #20 **không** bị ảnh hưởng — activity-log có config riêng, đã trỏ đúng topic connector đang ghi.

**Tạo connector (cách đã làm 2026-10-08):** Kafka Connect UI → **NEW** → **MySqlConnector** → khung PROPERTIES dán config chép từ `sapo_invoice_invoice_logs.v1.1`, chỉ đổi `name`, `table.whitelist`, `message.key.columns`, `database.history.kafka.topic` (`history_sapo_invoice.sapo_invoice.raw.<table>.v1.0`) → điền `database.password` (copy từ connector cũ — **user tự điền**, AI không nhập mật khẩu) → hết dòng đỏ validate → CREATE. Bản config không có mật khẩu: `~/invoice/dev-ops-config-override/.local/invoice_statement_logs.connector.properties` (đã exclude khỏi git).

**Restart activity-log — vì sao/thế nào:** Spring Boot đọc config server + chốt topic `@KafkaListener` **chỉ lúc khởi động**; code mới cần image mới. Merge services vào `dev` → CI `test activity-log` → `package activity-log` (jib) → trigger pipeline deploy (`STACK_DEPLOYMENT_TOKEN`) → container mới = restart. Config merge **trước** deploy thì không cần restart riêng; sửa config **sau** deploy → Retry job `package activity-log` của pipeline `dev` mới nhất (hoặc nhờ congnv/DevOps). `auto-offset-reset: latest` → group mới chỉ nhận thao tác sau khi khởi động.

### Chạy admin-service local (IntelliJ) để test
- Run config "Dev" = `ACTIVE_PROFILES=dev` → config server dev (`192.168.12.25:20888`) → **ghi thẳng DB dev dùng chung**, Kafka/TVAN dev. Không bật profile `job` → consumer Kafka của admin không chạy local.
- FE local trỏ service local: `.env` bỏ comment `SERVER_PROXY_API_URL=http://localhost:8080`.
- Test được ngay: `data.events` trong `invoice_mistake_logs` / `invoice_statement_logs` (DB dev). Vì ghi cùng DB dev, khi connector + services !23 đã lên dev thì thao tác từ local cũng chảy sang activity-log dev — không bắt buộc deploy !624.
- Không test trọn ở local: bên mua ký qua link email (`statement.url` trỏ domain dev → chạy bản deploy cũ) — gọi thẳng endpoint ký bên mua vào `localhost:8080`; gửi CQT cần tenant có chứng thư.
- An toàn: consumer thông báo CQT bản cũ trên dev gặp event lạ → `continue`, không lỗi.

### Test trên dev (sau khi merge)
**Điều kiện:** services ✅ đã vào dev (chờ pipeline #1137103 deploy xong) · admin-service !624 merge/deploy **hoặc** chạy local nhánh feature (ghi cùng DB dev) · config-override ✅ · connector 2 bảng ✅ · `auto-offset-reset: latest` → chỉ thao tác MỚI. Kiểm thêm: sau thao tác biên bản đầu tiên, topic `sapo_invoice.raw.sapo_invoice.invoice_statement_logs` phải hiện ở `…/api/kafka-connect-1/connectors/invoice.sapo_invoice.invoice_statement_logs.v1.0/topics`.

| Thao tác (SI dev) | Kỳ vọng `event_code` |
|---|---|
| Thông báo sai sót: Lưu (HĐ trong SI) / HĐ ngoài hệ thống | `mistake_create` / `mistake_create_external` |
| Sửa · Gửi CQT · Xóa | `mistake_update` · `mistake_send` (1 bản ghi; signing + CQT phản hồi **không** sinh) · `mistake_delete` |
| Biên bản thay thế: Lưu → Ký → Gửi | `replacement_statement_create` → `_sign` → `_send` |
| Bên mua ký qua link email | `replacement_statement_buyer_signed` (actor Hệ thống) |
| Sửa / Xóa biên bản · biên bản điều chỉnh | `_update` / `_delete` · `adjustment_statement_*` |

Kiểm từng tầng:
1. DB: `SELECT id, verb, JSON_EXTRACT(data,'$.events') FROM invoice_mistake_logs ORDER BY id DESC LIMIT 5;` (tương tự `invoice_statement_logs`).
2. API (FE còn mock): `https://sapo-invoice-dev.sapocorp.vn/api/activity_logs?function_codes=invoice_mistake,invoice_replacement,invoice_adjustment` — kiểm `event_code`, `action_code` (create/send/sign…, không phải add/update), `object_code`, `object_id`, `actor_name`, `detail.status_from/status_to`.
3. Phủ định: CQT phản hồi / rollback ký → không có bản ghi mới.
4. Rỗng → kiểm lần lượt: log có dòng mới? connector chạy, topic khớp config-override? activity-log restart bản mới? (playbook mục 8).

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
| ~~7~~ | ~~Quyền Developer repo `sapo-invoice-services`~~ — ✅ đã cấp 2026-10-07 | — |
| ~~8~~ | ~~#20 hướng A hay B~~ — ✅ chốt A, đã implement (2026-10-07) | — |
| ~~9~~ | ~~Connector `invoice_statement_logs`~~ — ✅ tạo 2026-10-08 | — |
| 12 | ❓ Xác nhận topic `invoice-mistake-log` của admin-service (`..._invoice_invoice_mistake_logs`, có từ 2024) lúc chạy thật là gì — lập thông báo sai sót mới trên dev xem có lên danh sách không; không lên thì báo | hungnt10 / congnv |
| 10 | Khi nào merge lib !16 / `setting-change-logs` / quyền !607 vào master (!14 đã merge 2026-10-07) | congnv |
| ~~11~~ | ~~Ai sửa `CanonicalLogAdapter` chung~~ — chốt: chỉ cho `invoice_logs`, nhóm khác adapter riêng | — |
| 13 | Thống nhất hoa/thường `eventCode` + `action_code` thô của nhóm Danh mục | congnv / manhtv3 |
