---
created: 2026-07-29 16:00
scope: "Rules Cursor/Claude — Backend Java Spring Boot (invoice-app, sapo-invoice-admin-service, sapo-pay-service)"
---

# Backend Rules — Java Spring Boot (Sapo Invoice)

Migrate từ `ai-workspace/rules/cursor-backend.md`. Dùng làm `.cursorrules`/`CLAUDE.md` ở root repo backend khi cần, hoặc tham chiếu trực tiếp từ đây.

## Architecture (DDD Layered — STRICT)

```
interfaces/rest/     ← Controllers only (validate input, inject context, delegate)
application/         ← Services (orchestrate), DTOs (Request/Response), Feign clients
domain/              ← Business logic: entities, value objects, repository INTERFACES
infrastructure/      ← JPA implementations, configs, Kafka/RabbitMQ consumers, jobs
```

**Layer dependency: chỉ đi xuống. Domain không import application/infrastructure.**

## Tech Stack

- Java 17 + Spring Boot 3.3.x + Gradle (Kotlin DSL)
- MariaDB + JPA/Hibernate 6.x — **NO Flyway, NO Liquibase** (manual SQL)
- Elasticsearch 8.8.x, Redis, Kafka, RabbitMQ, Quartz JDBC
- Lombok + MapStruct + OpenFeign
- Format: **Palantir Java** via Spotless — chạy `./gradlew spotlessJavaApply` trước khi commit

## Primary Keys — LONG (KHÔNG PHẢI UUID)

```java
// Multi-tenant EmbeddedId — BẮT BUỘC cho mọi domain entity
@Embeddable
public record InvoiceId(long id, long tenantId) {
    public static InvoiceId of(long id, long tenantId) {
        return new InvoiceId(id, tenantId);
    }
}

@Entity
public class Invoice extends AggregateRoot<Invoice> {
    @Id
    private InvoiceId id; // {long id, long tenantId}
}
```

## Multi-Tenancy — CRITICAL (không bao giờ bỏ qua)

- `tenantId` bắt buộc trong **MỌI** domain entity và query
- `tenantId` inject từ server-side auth context (`@TenantId`) — **KHÔNG BAO GIỜ** từ request body của client
- `@UserId long userId` cho user context injection
- Repository: dùng `findByIdAndTenantId(id, tenantId)` — **KHÔNG** `findById()` đơn thuần
- IDOR protection: trả **404** khi không có quyền — KHÔNG 403

```java
// ĐÚNG
Invoice invoice = invoiceRepository.findByIdAndTenantId(id, tenantId)
    .orElseThrow(NotFoundException::new);

// SAI — security hole
Invoice invoice = invoiceRepository.findById(id).orElseThrow(...);
```

## Domain Entities (AggregateRoot / NestedDomainEntity)

- Kế thừa `AggregateRoot<T>` (aggregate root) hoặc `NestedDomainEntity` (child entity) từ `sapo-invoice-common`
- Constructor: `@NoArgsConstructor(access = AccessLevel.PROTECTED)` — **KHÔNG** public default constructor
- **Factory methods**: `Invoice.create(...)`, `Invoice.of(...)` — **KHÔNG** copy state trực tiếp từ request
- **Business method names**: `publish()`, `cancel()`, `updateBuyer()`, `replaced()` — KHÔNG setters
- **Value objects**: `@Embedded` immutable objects (InvoiceDiscount, InvoiceCurrency, TemplateInfo)
- **Cross-aggregate refs**: dùng ID only — **KHÔNG** `@ManyToOne` qua aggregate boundary

```java
// ĐÚNG — business method + factory
@Entity
public class Invoice extends AggregateRoot<Invoice> {
    @NoArgsConstructor(access = AccessLevel.PROTECTED)

    public static Invoice create(long id, long tenantId, CreateInvoiceRequest request) {
        var invoice = new Invoice();
        invoice.id = InvoiceId.of(id, tenantId);
        invoice.status = InvoiceStatus.DRAFT;
        // validate invariants here
        return invoice;
    }

    public void publish() {
        if (this.status != InvoiceStatus.DRAFT) throw new BusinessException("...");
        this.status = InvoiceStatus.PUBLISHED;
        this.addDomainEvent(new InvoicePublishedEvent(this));
    }
}

// SAI — setter style
invoice.setStatus(InvoiceStatus.PUBLISHED);
```

## Read/Write Service Segregation (CQRS-lite)

- `XxxReadService`: `@Transactional(readOnly = true)` — **TUYỆT ĐỐI KHÔNG write** (silently ignored, risk partial saves)
- `XxxWriteService`: `@Transactional` trên **MỌI** method
- Services **return DTOs** — **KHÔNG BAO GIỜ** return domain entities (→ LazyInitializationException ngoài transaction)
- Lazy associations phải được fetch **TRONG transaction** trước khi map sang DTO

```java
// ĐÚNG
@Service
@Transactional(readOnly = true)
public class InvoiceReadService {
    public InvoiceResponse getById(long id, long tenantId) {
        Invoice invoice = repo.findByIdAndTenantId(id, tenantId).orElseThrow(...);
        return InvoiceResponse.from(invoice); // map TRONG transaction
    }
}

@Service
@Transactional
public class InvoiceWriteService {
    public InvoiceResponse publish(long id, long tenantId) { ... }
}
```

## Naming Conventions

- Controllers: `InvoiceController`, `DraftInvoiceController`
- Services: `InvoiceReadService`, `InvoiceWriteService`, `InvoiceBulkWriteService`
- DTOs: `InvoiceResponse`, `InvoiceFilterRequest`, `CreateInvoiceRequest`
- Repository (domain interface): `InvoiceRepository`
- Repository (JPA impl): `InvoiceJpaRepository`
- Enums: `@Enumerated(EnumType.STRING)`, `UPPER_SNAKE_CASE` values
- Boolean fields: `isActive`, `hasSignature`, `canCancel`, `shouldNotify` prefixes

## Imports — QUAN TRỌNG

```java
// ĐÚNG
import jakarta.persistence.*;          // Spring Boot 3.x dùng Jakarta EE
import jakarta.validation.constraints.*;
import org.apache.commons.lang3.StringUtils;    // isBlank(), isEmpty()
import org.apache.commons.collections4.CollectionUtils; // isEmpty()

// SAI
import javax.persistence.*;            // ← KHÔNG dùng javax.*
import org.springframework.util.StringUtils; // ← KHÔNG dùng Spring utils
```

## Lombok

- `@RequiredArgsConstructor` — constructor injection (KHÔNG field injection)
- `@Slf4j` cho logging
- `@Getter` trên entities — **KHÔNG** `@Setter`
- `@NoArgsConstructor(access = AccessLevel.PROTECTED)` cho domain entities
- **KHÔNG** dùng `@Data` (tạo mutable setters + equals/hashCode issues với JPA)

## API & Response Format

- Base path: `/api/` — **KHÔNG** `/api/v1/`
- Response DTOs được **auto-wrapped** với root key (snake_case pluralized class name)
- Request DTOs: thêm `@JsonRootName("_")` nếu expect plain body (không root key)
- **Không cần `@JsonProperty`** — camelCase Java fields auto-map sang snake_case JSON

## Validation

- `@Valid` trên **mọi** `@RequestBody` parameter
- `@Valid` trên **mọi** nested DTO field (cascading validation)
- `@ModelAttribute` cho filter/query params trên GET endpoints — **KHÔNG** `@RequestBody`

## Database Migrations (Manual — NO Flyway)

- Script naming: `V{n}__{description}.sql`
- **`tenant_id` bắt buộc** trong mọi table và column mới
- **NO `ddl-auto`** — Hibernate KHÔNG tự alter tables
- Apply thủ công bởi team (không tự động khi deploy)

## Transactions — Anti-patterns cần tránh

```
MISSING @Transactional trên WriteService  → multi-step ops có thể partial save
@Transactional(readOnly=true) mà có write  → silently ignored, risk data corruption
Lazy load NGOÀI transaction               → LazyInitializationException
Domain entity escape qua service boundary → detached entity issues
```

## Async Processing

- Domain events → Kafka/RabbitMQ consumers (infrastructure/job/)
- Scheduled tasks → Quartz JDBC (infrastructure/job/scheduled/)
- Kafka consumers: `@KafkaListener` trong infrastructure layer
- Event publishing: `this.addDomainEvent(new XxxEvent(...))` trong domain entity

## Security

- **KHÔNG log sensitive data** (invoiceNo, taxCode, certificate data)
- `tenantId` từ `@TenantId` annotation — KHÔNG từ client request
- Input validation qua Jakarta Bean Validation annotations

## var keyword

```java
// ĐÚNG — local variable với type obvious
var invoices = invoiceRepository.findAll();
var response = InvoiceResponse.from(invoice);

// SAI — KHÔNG dùng cho fields, params, return types
private var status; // ← SAI
public var getInvoice() { ... } // ← SAI
```

## Collections

```java
List<Invoice> items = new ArrayList<>();         // khởi tạo
return Collections.unmodifiableList(items);      // trả về từ domain
```

## Code Quality

- Chạy format trước khi commit: `./gradlew spotlessJavaApply`
- Test: `./gradlew test`
- Build: `./gradlew build`
- Docker: `./gradlew jib` (không cần Docker daemon)

---

_Nguồn: `ai-workspace/rules/cursor-backend.md`. Cập nhật rule mới ở đây (developer-os) trước — `ai-workspace` không còn là nguồn chính cho phần rules._
