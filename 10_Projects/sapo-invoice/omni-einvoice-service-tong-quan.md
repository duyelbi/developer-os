---
created: 2026-08-11 08:30
status: Implemented
project: "[[10_Projects/sapo-invoice/README]]"
---

# `sapo-einvoice-service` — tổng quan kiến trúc

Microservice hóa đơn điện tử **phía Sapo Omni (core)**, không thuộc nhóm repo `sapo-money/sapo-invoice`. Đây là nơi Omni tạo/phát hành hóa đơn cho đơn hàng, và **gọi sang Sapo Invoice (SI) như một trong 4 provider**.

- Path: `/Users/sapo/invoice/sapo-einvoice-service/`
- Remote: `git.dktsoft.com:2008/sapo-core/sapo-microservices/sapo-einvoice-service.git`
- Branch mặc định: `master` (không có `staging` như invoice-app — xem [[10_Projects/sapo-invoice/invoice-app-staging-master-release-flow]] để đối chiếu, quy trình khác nhau)
- Branch convention thực tế: `dev-money/feature/<mô-tả>-SM-<số>`, `dev-money/hotfix/<mô-tả>`, merge thẳng vào `master`

## Vị trí trong hệ sinh thái

```text
Sapo Omni (core)                          Sapo Invoice (SI)
┌─────────────────────────┐               ┌──────────────────────────┐
│ sapo-frontend-v3        │               │ sapo-invoice-admin-*     │
│  page/EInvoice          │               │ invoice-app              │
│         │               │               │ sapo-pay-service         │
│         ▼ /admin/*.json │               └──────────▲───────────────┘
│ sapo-einvoice-service   │──── provider ────────────┘
│  (repo này)             │──── provider ────► MeInvoice / SInvoice / VnInvoice
└─────────────────────────┘
```

`SI` trong docs của repo này = **SapoInvoice**, tức sản phẩm ở nhóm repo `sapo-money/sapo-invoice`. Xem `docs/invoice-metadata/SI-api-guide.md`.

## Stack

| Thành phần | Giá trị |
|---|---|
| Runtime | Java 11, Spring Boot **2.1.0.RELEASE** (cũ) |
| Parent POM | `vn.sapo.services:sapo-dependencies:2.0.4`, lib nội bộ `sapo-common:1.5.9-rc1` |
| DB | **SQL Server** (T-SQL) — xem cảnh báo bên dưới |
| Migration | Flyway, `src/main/resources/db/migration/`, hiện có V1→V7 |
| Cache | Redis (Jedis 2.9.0) + Hazelcast 3.10.4 — hai tầng |
| Messaging | Kafka 2.2.6 (event) + RabbitMQ (bulk action, retry) |
| Config | Spring Cloud Config Server, **`failFast: true`** — thiếu config server là app không start |
| HTTP client | OpenFeign | 
| Mapping | MapStruct 1.3.1 |
| Build/Deploy | Maven + Jib (`mvn compile jib:build`), GitLab CI include template `sapo-core/gitlab-ci-template` |

Profile → config label: `local`/`dev2` → `local-spring-2`, `staging` → `staging-spring-2`, `live` → `spring-2`.

## ⚠️ Mâu thuẫn tài liệu trong repo — DB là SQL Server

`docs/project-context.md` và `docs/brownfield-architecture.md` ghi **PostgreSQL**. Sai.
`CLAUDE.md` ghi SQL Server, và đây mới đúng — bằng chứng trong chính repo:

- Migration dùng T-SQL: `IF NOT EXISTS (SELECT * FROM sys.tables ...)`, `BIGINT IDENTITY(1,1)`, `NVARCHAR(MAX)`, `DATETIME2`, `SYSDATETIME()`, `GO`
- Playbook điều tra query `GETUTCDATE()`, `SELECT TOP 1`

→ Khi làm schema, luôn viết T-SQL. Đừng tin `project-context.md` ở mục database. (Cùng dạng bẫy với [[10_Projects/sapo-invoice/README|ddl-auto ở admin-service]] — tài liệu trong repo không đồng bộ với thực tế.)

## Kiến trúc lớp

```text
controller/        REST, base path /admin/einvoices, @SapoPreAuthorize
    ↓
service/           orchestration
  publisher/       Factory + Strategy theo provider
  workflow/        download / send mail / preview (+ execution per provider)
  autoinvoice/     xuất hóa đơn tự động
    ↓
domain/            JPA entity DDD — EInvoice là aggregate root
    ↓
repository/        Spring Data JPA + Specification
```

Mỗi provider có bộ riêng đủ 5 tầng: `clients/{provider}/`, `service/publisher/{provider}/`, `service/workflow/execution/{provider}/`, `domain/{provider}/`, `controller/{provider}/`. Provider: `meinvoice`, `sinvoice`, `vninvoice`, `sapo_invoice`.

## Entry point cần nhớ

| Vai trò | File |
|---|---|
| Main | `src/main/java/vn/sapo/services/SapoEinvoiceServiceApplication.java` |
| Aggregate root | `domain/EInvoice.java` |
| Service chính (~1700 dòng) | `service/impl/EInvoiceServiceImpl.java` |
| Factory provider | `service/publisher/EInvoicePublishingServiceFactory.java` |
| Controller chính | `controller/EInvoiceController.java` |
| Auto invoice — nơi quyết định xuất/không xuất | `service/autoinvoice/impl/AutoInvoiceExecutionServiceImpl.java` |
| Kafka: order → tạo draft | `consumer/kafka/OrderConsumer.java` |
| RabbitMQ: bulk + retry | `consumer/rabbitmq/` (`InvoiceBulkActionPublishConsumer`, `AutoInvoiceRetryConsumer`, `AutoPublishRetryConsumer`) |
| Job thông báo | `job/AutoInvoiceNotificationJob.java` |
| QR công khai | `controller/qr/PublicQrInvoiceController.java` |

## Luồng chính

**Tạo draft từ order:** Kafka `OrderConsumer` → `EInvoiceServiceImpl.createDraft()` → `OrderConverter` → lưu draft → publish domain event.

**Phát hành:** `EInvoiceController.publish()` → `EInvoicePublishingServiceFactory.getPublishingProvider(provider)` → `{Provider}Service.publish()` → Feign gọi provider → cập nhật status + audit log.

**Bulk (SapoInvoice):** controller → đẩy message RabbitMQ → `InvoiceBulkActionPublishConsumer` → xử lý từng invoice, retry khi lỗi (4 lần, backoff 1s→10s, 20 concurrent consumer).

**Auto invoice:** `OrderConsumer` (chỉ chạy khi `ENABLE_ORDER_CONSUMER=true`) → `AutoInvoiceExecutionServiceImpl.processAutoInvoice()` → duyệt 9 "gate" → ghi kết quả vào bảng `AutoInvoiceResults`. Chi tiết gate: [[10_Projects/sapo-invoice/omni-einvoice-dieu-tra-su-co-prod]].

## Sự thật lúc runtime (đọc từ log dev2, 2026-08-11)

Vài thứ chỉ lộ ra khi xem log chạy thật, không có trong docs:

- **Web server là Jetty, không phải Tomcat** — `JettyWebServer`, `JettyConfig$JettyGracefulShutdown` (do `sapo-common` cấu hình). Lắng nghe **port 80** trong container, không phải 8080.
- Khởi động mất **~55 giây** — đừng tưởng treo.
- **2 HikariPool** (`HikariPool-1`, `HikariPool-2`) → service có 2 datasource.
- Kafka broker dev2: `192.168.12.70:9092`. Hai consumer group:
  - `dev2-sapo-einvoice` — nghe `DEV2_SAPO_ORDER.dbo.OrderLogs`, `DEV2_SAPO_ORDER_SHARD2.dbo.OrderLogs`, `DEV2_SAPO_PURCHASE_ORDER.dbo.PurchaseOrderLogs`
  - `dev2_einvoice_invalid_cache_from_core` — nghe `Accounts`, `AccountRoles`, `Locations`, `Tenants`, `PaymentMethods`, `OrderSources`, `PartnerLogs` (đúng luồng invalidate cache ở `consumer/invalid_cache/`)
- **Tên topic xác nhận SQL Server + sharding**: dạng `{DB}.dbo.{Table}` là CDC của SQL Server, và có hẳn `..._SHARD2` ngay ở dev2 → mô hình shard mô tả trong [[10_Projects/sapo-invoice/omni-einvoice-dieu-tra-su-co-prod]] không chỉ có ở prod. Thêm một bằng chứng nữa DB **không phải PostgreSQL**.
- Warning vô hại, bỏ qua: `Failed to register application ... at spring-boot-admin ([http://localhost:8769/instances]): Connection refused` — chỉ là không đăng ký được với Spring Boot Admin.

## Quy tắc code bắt buộc

- **Factory cho provider** — không `new` service provider trực tiếp
- **`BigDecimal` + `RoundingMode.HALF_UP`** cho mọi phép tiền — cấm `double`/`float`
- **Mọi query phải lọc `tenantId`** — thiếu là rò rỉ dữ liệu giữa tenant
- **Enum value viết thường**: `draft`, `published`, `deleted`, `creating`
- **Business method thay setter** trên entity: `invoice.publishInvoice(...)`, không `setStatus(...)`; state change thì `addDomainEvent(...)`
- **Constructor injection** qua `@RequiredArgsConstructor` — không field injection
- **`java.util.Date` / `Instant` (UTC)** — không `LocalDateTime`
- **Dùng cached wrapper** (`clients/cache/OrderClientService`...) thay vì gọi thẳng Feign client
- **Java 11**: không record/sealed/text block
- Quy ước tên: bảng PascalCase (`EInvoices`), cột camelCase (`tenantId`), endpoint snake_case (`/create_draft`)

## Nợ kỹ thuật đã biết (repo tự ghi nhận)

| Mức | Vấn đề |
|---|---|
| CRITICAL | **Không có test nào** — `src/test/` không tồn tại trên ~578 file Java. `mvn test` luôn pass vì rỗng. |
| CRITICAL | Bug enum: `EInvoiceStatus.SIGNING` có value `"singing"` (thiếu chữ n) — `domain/enumeration/EInvoiceStatus.java:4` |
| CRITICAL | Typo lịch sử: package `base/exeption/`, class `SapoInvoiceExeption`/`MeinVoiceExeption`/`SInvoiceExeption`. **Không đổi tên** — code mới phải theo. Thiếu `VnInvoiceExeption`. |
| HIGH | `consumer/kafka/EInvoicePublishingConsumer.java` — listener bị comment out toàn bộ, dead code, không có giải thích |
| HIGH | `service/BaseService.java` dùng `@Autowired` field injection cho 7 dependency — trái chính chuẩn của repo, lan sang mọi service kế thừa |
| HIGH | Trùng util ngày: `DateUtil.java` (250 dòng) vs `DateUtils.java` (25 dòng) |
| HIGH | `pom.xml` khai báo `spring-boot-starter-data-jpa` 2 lần (dòng 48 và 69) |

## Tài liệu trong repo đáng đọc

- `CLAUDE.md` — chuẩn nhất về DB và quy tắc code
- `docs/brownfield-architecture.md` — thực trạng + nợ kỹ thuật (657 dòng)
- `docs/architecture/` — 12 file: coding-standards, component-architecture, data-models-and-schema-changes, security-integration…
- `docs/automatic-invoice-issuance/` — implementation plan, api-reference, 5 story
- `docs/features/scan-qr-enter-invoice-info/` — PRD/SRS/API/task-list cho luồng QR
- `docs/invoice-metadata/` — brief + SI API guide (metadata `ref_source_code`, `vat_pit_category_code`)
- `README.md` — 1118 dòng, đầy đủ nhưng dài

Repo cài **BMAD v6** (`_bmad/`, ~70 skill trong `.claude/skills/`) — mở Claude Code trong repo này sẽ tự nạp toàn bộ skill `bmad-*`.

## Liên kết

- Frontend tương ứng: [[10_Projects/sapo-invoice/omni-frontend-v3-einvoice-tong-quan]]
- Điều tra sự cố prod: [[10_Projects/sapo-invoice/omni-einvoice-dieu-tra-su-co-prod]]
