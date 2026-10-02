---
created: 2026-08-25 08:30
updated: 2026-08-27
status: Đã chốt Q1–Q5 — sẵn sàng child issue / implement
project: "[[10_Projects/sapo-invoice/README]]"
---

# Epic #80 — [V2] Tự động tạo & phát hành HĐ điều chỉnh cho đơn trả hàng 1 phần

- GitLab epic: [#80](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/80) (group `sapo-money/sapo-invoice`, assignee `congnv` + `phuongnt20`, milestone: chưa gán milestone riêng, label `workflow::ready`)
- SRS: `invoice-docs/.../tu-dong-tao-phat-hanh-hoa-don-dieu-chinh/srs.md` — **BA cập nhật** theo quyết định 2026-08-27 (dev không sửa invoice-docs)
- Repo triển khai: `sapo-einvoice-service` (BE) + `sapo-frontend-v3` (FE)
- Test case: [[epic-80-test-cases]]
- Quyết định Q1–Q5: [[epic-80-cau-hoi-po-ba]]

## ✅ Quyết định đã chốt (2026-08-27)

| #      | Chốt                                                                                                                               |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Q1** | UI + rule **theo Figma**; BE check `refundStatus`; không auto-lock. **BA** sửa SRS BR-V2-2.                                        |
| **Q2** | Chỉ toàn bộ → `["returned"]`; option gộp / chọn cả 2 → `["returned","partially_returned"]`. Runtime **2 engine** (full + partial). |
| **Q3** | **Có** job đối soát MVP (port V3).                                                                                                 |
| **Q4** | Làm tròn **mirror V3**: số từ dòng HĐ gốc + scale **0**. Không snapshot STP MVP.                                                   |
| **Q5** | Ledger + `order_return_ids` trên HĐ + **đẩy sang order như V3**; sync API với #64.                                                 |

### Child issues (đã tạo)

1. [#94](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/work_items/94) `[V2][BE] …` — assignees `duynd7`, `phuongnt20`
2. [#95](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/work_items/95) `[V2][FE] …` — assignees `duynd7`, `phuongnt20`

Chi tiết: [[epic-80-cau-hoi-po-ba]]

## Tóm tắt yêu cầu (sau chốt)

Cho phép merchant cấu hình để hệ thống **tự động tạo & phát hành hóa đơn điều chỉnh** khi đơn phát sinh trả hàng **một phần hoặc toàn bộ** (theo option Figma), với điều kiện phiếu trả `status = returned` **và đã hoàn tiền** (`refundStatus`). Trigger = Kafka từ V2-Order. Công thức phân bổ từ dòng HĐ gốc (đảo dấu, **scale 0 như V3**). Có ledger + job đối soát. Liên kết `order.invoices[].order_return_ids` như V3.

## 🆕 Cập nhật 2026-08-26 — Figma đã gắn vào epic, phát hiện lệch với SRS

Epic #80 đã được cập nhật (2026-08-25) — thêm link Figma: [SAPO-INVOICE-V2, node 224:33410](https://www.figma.com/design/eB5jx4MxReLJuyrlptKhs2/SAPO-INVOICE-V2?node-id=224-33410) (frame "Droplist" — mockup dropdown Trạng thái đơn hàng), và thread comment xác nhận "V3 epic #56" nên hiểu là **epic #64** (parent của issue #56) — "đúng r, như phần Hải đang làm nha" (dungntt6, 2026-08-25). Epic #64 **vẫn `state: opened`, không có tiến triển nào mới** kể từ hôm đó (kiểm tra lại 2026-08-26) — rủi ro cross-epic ở mục 1 dưới vẫn nguyên.

Đã mở Figma (`get_metadata` + `get_screenshot`, đọc chính xác text qua layer name) — **design KHÔNG khớp SRS ở đúng điểm SRS nhấn mạnh là khác biệt cốt lõi với V3:**

|                | SRS §6.1 (chốt 2026-08-21)                                                                                                                                                     | Figma (gắn 2026-08-25)                                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Tên option mới | "Đã hoàn trả một phần" (option riêng, auto-tick + khóa "Đã hoàn trả toàn bộ" khi chọn)                                                                                         | "**Đã hoàn trả toàn bộ và 1 phần**" (option gộp, đứng độc lập cạnh "Đã hoàn trả toàn bộ" — không thấy hành vi auto-tick/khóa nào trong mockup) |
| Helptext       | _"Áp dụng cho từng đơn trả hàng đã nhận hàng, bao gồm cả đơn hàng được hoàn trả toàn bộ."_ — SRS ghi rõ: _"V2 không đòi hoàn tiền → helptext V2 bỏ cụm 'và hoàn tiền' của V3"_ | _"Áp dụng cho đơn trả đã nhận hàng toàn bộ hoặc 1 phần trong đơn trả **và đã hoàn tiền**"_ — **vẫn giữ cụm "và đã hoàn tiền"**                 |

Cụm "và đã hoàn tiền" trong Figma **mâu thuẫn trực tiếp với BR-V2-2** (điều kiện kích hoạt V2 chỉ cần `order_return.status = "returned"`, **không** yêu cầu `refund_status = refunded` — đây là điểm SRS liệt kê là khác biệt **duy nhất** so với V3). Nhiều khả năng designer copy nguyên helptext của option "Đã hoàn trả toàn bộ" (option cũ, đúng là có yêu cầu hoàn tiền vì thuộc luồng điều chỉnh toàn bộ hiện tại — không do epic này đụng vào) sang option mới mà quên bỏ cụm đó theo đúng note kỹ thuật SRS đã ghi.

**→ Cần PO/BA xác nhận lại với designer trước khi FE build theo Figma này**, chọn 1 trong 2:

1. Sửa Figma: bỏ "và đã hoàn tiền" khỏi helptext option mới, đổi tên về đúng ý "một phần" nếu muốn giữ 2-option-auto-lock như SRS.
2. Sửa SRS: nếu 3-option-độc-lập (không auto-lock) là hướng thật sự chốt, và merchant **có** phải hoàn tiền mới kích hoạt được — thì BR-V2-2 sai và phải update lại + đổi cả BE (V2-Einvoice phải check thêm `refund_status`, không chỉ `order_return.status`).

Đây không phải lỗi chính tả nhỏ — nó quyết định BE có phải thêm điều kiện `refund_status` vào BR-V2-2 hay không. Nên hỏi PO **trước khi** dev bắt đầu phần điều kiện kích hoạt (Nhóm 3 test case, mục R2).

## Trả lời 2 câu hỏi trực tiếp

### 1. Có QA nào cần QA sớm không? → **Có, và gấp hơn SRS thể hiện**

SRS liên tục ghi "giữ nguyên như V3", "tái sử dụng cơ chế đã có" cho ledger/idempotency/retry/reconciliation. Đã verify code thật (`sapo-einvoice-service`) — **phần lớn các cơ chế đó KHÔNG tồn tại** trên nhánh hiện tại, phải xây mới. Đây không phải rủi ro nhỏ — nó đổi effort estimate và cần BA/tech lead xác nhận scope thật trước khi cam kết deadline. Xem bảng gap ở dưới — nên đưa outline test case (nhóm Ledger/Idempotency, STP inheritance, Reconciliation) cho QA **đọc trước khi code chạy**, giống format đã làm ở epic #61, để QA + dev thống nhất "cái gì coi là bug" trước khi cãi nhau lúc test.

Thêm 2 điểm cần QA/PO nhìn sớm, **không nằm trong SRS**:

- **Epic #64 / issue #56** (cơ chế `order_return_ids`) mà SRS §4.6 dẫn ra làm "khuôn mẫu đã chốt" — bản thân epic đó **đang `state: opened`, label `status::To do`**, chưa merge ở bất kỳ repo nào (order-service, SI, hay V3). Epic #80 không "làm theo cái đã có", mà đang **implement song song** với 2 nhánh khác cùng dùng chung khái niệm này.
- **Epic #69** (`[INVOICE-APP V3] Tự động tạo & phát hành HĐ điều chỉnh cho đơn hoàn hàng một phần`) — bản V3 mà SRS V2 này tự nhận là "mirror" — cũng **`state: opened`**, chưa xong. Cả 3 epic (#64, #69, #80) đều rơi vào milestone `R2026.08` (due 2026-08-31, tức **tuần này**) → rủi ro cả 3 đội cùng đua 1 deadline, cùng phát minh lại một cơ chế theo 3 cách hơi khác nhau nếu không đồng bộ thiết kế `order_return_ids` sớm.

### 2. Có thiếu Figma không? → **Ban đầu không cần, nhưng nay đã có link — và cần soát lại nội dung, không chỉ tick "đã có"**

Đã verify code `sapo-frontend-v3`: màn "Auto Invoice V2" + khối cấu hình HĐ điều chỉnh (`adjustment_order_configs`, `auto_adjustment_invoice_enabled`) **đã tồn tại đầy đủ**, đúng như SRS §6.1 tự nhận ("ĐÃ CÓ toàn bộ, chỉ BỔ SUNG 1 giá trị"). Cụ thể:

- Option "Trả hàng toàn bộ" đã có sẵn trong mảng hardcode `ADJUSTMENT_ORDER_STATUS_OPTIONS` (`src/page/Settings/Einvoices/components/AutoInvoiceConfig/constants.ts:40-47`).
- Helptext (`subtext`) đã có pattern sẵn, dùng lại nguyên component.
- Pattern "chọn giá trị X → hiện thêm UI" đã có tiền lệ gần giống (`showAdjustmentReturnDateFrom` ở `AutoInvoiceConfigPage.tsx:669-675`), tái dùng được.
- Không có design system mới, không có màn hình mới — vẫn đúng nhận định ban đầu là **không cần tạo mockup mới**.

→ **Cập nhật 2026-08-26:** epic đã được gắn link Figma thật (xem mục "Cập nhật" ở trên) — không phải vì thiếu Figma mà vì nhóm cần 1 mockup cụ thể để chốt UX (2 option auto-lock hay 3 option độc lập). Đã mở và soát nội dung Figma đó: **có lệch với SRS ở đúng phần business-rule quan trọng nhất (yêu cầu hoàn tiền hay không)** — xem chi tiết ở mục Cập nhật. Việc còn thiếu không phải "vẽ design mới" mà là **PO/BA đối chiếu Figma vs SRS và chốt lại 1 trong 2** trước khi FE build.

## ⚠️ Bảng đối chiếu giả định SRS vs thực tế code (đã verify, không phải suy đoán)

| SRS giả định                                                                                      | Thực tế `sapo-einvoice-service` (branch `dev-money/feature/shipping-fee-invoice-v2-dev2-SM-0`)                                                                                                                                                                                                                    | Risk                                                                  |
| ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| "Ledger `UNIQUE(store_id, order_return_id)`, claim trước khi tạo" đã có, dùng lại                 | **Không tồn tại.** Idempotency hiện tại = `AutoInvoiceResultRepository.existsBy...` (business check cấp **order**, không phải order_return) + Redis lock cấp order+flowType. Không có bảng ledger nào theo order_return_id. Phải tạo mới (bảng + migration + unique constraint).                                  | 🔴 HIGH                                                               |
| "Tái sử dụng job đối soát của luồng điều chỉnh toàn bộ đã có"                                     | **Không có job đối soát nào.** Duy nhất `@Scheduled` job hiện có là `AutoInvoiceNotificationJob` (gửi email, không phải quét đơn miss event). Câu "tái sử dụng, không viết mới" trong SRS BR-V2-7/§4.2 **sai với thực tế** — phải viết mới hoặc scope lại (bỏ reconciliation cho MVP + accept rủi ro miss event). | 🔴 HIGH — cần chốt với PO trước khi code                              |
| "Retry/DLT tái sử dụng cơ chế điều chỉnh toàn bộ"                                                 | **Có**, đúng — RabbitMQ DLX 2 tầng (`AutoInvoiceRetryConsumer` retry ngắn, `AutoPublishRetryConsumer` retry dài + cutoff 23:55). Tái dùng được thật.                                                                                                                                                              | 🟢 xác nhận đúng                                                      |
| "`order_line_item_id` bổ sung vào `einvoice.line_items[]`"                                        | Chưa có field này trên `EInvoiceLineItem`/`EInvoiceLineItemDTO`. Nguồn (`OrderReturnLineItemDomain`) **đã có sẵn** `orderLineItemId` — nửa việc còn lại là thread nó qua explode-combo (`EInvoiceServiceImpl.explodeCompositeLines` L3183) khi dựng dòng HĐ.                                                      | 🟡 MED — thêm cột + populate, không phải logic mới khó                |
| "`order.invoices[].order_return_ids` như V3 epic #56"                                             | **Chưa có ở bất kỳ đâu** — kể cả V3 cũng chưa (epic #64 `state: opened`). Không có cơ chế liên kết invoice↔order_return nào tồn tại để tham chiếu, kể cả cho luồng điều chỉnh toàn bộ hiện tại (match chỉ bằng `orderId`).                                                                                        | 🔴 HIGH — genuinely new, phối hợp với đội order-service/SI            |
| "HĐĐC kế thừa STP + `apply_decimal_rounding` snapshot từ HĐ gốc"                                  | **Không có field snapshot này trên `EInvoice`** ở branch hiện tại. Có nhánh liên quan `dev-money/feature/apply-flag-decimal-config-SM-1238` (chưa merge) nhưng làm theo hướng **flag cấp tenant**, không phải snapshot cấp invoice — khác hướng SRS §4.11.1 cần.                                                  | 🔴 HIGH — block đúng công thức làm tròn, cần chốt trước khi tính tiền |
| "`auto_invoice_config` (`adjustment_invoice_info_configs[]`, `adjustment_order_configs`, toggle)" | **Khớp đúng** — model, migration `V3__add_adjustment_fields...`, DTO đều có sẵn.                                                                                                                                                                                                                                  | 🟢 xác nhận đúng                                                      |
| "Phí VC `separate_line` — dùng lại BR-RT9 V3"                                                     | Logic thật (`ShippingFeeLineHelper`, `SapoInvoiceService.getShippingFeeSettings`) sống ở tầng build-invoice dùng chung, vừa hoàn thiện tuần này (epic #61) — **tái dùng được**, nhưng chưa từng chạy qua nhánh partial-return, cần test riêng khi nối vào.                                                        | 🟡 MED                                                                |

## 5 câu hỏi PO/BA — ĐÃ CHỐT (2026-08-27)

> ✅ Xem bảng quyết định đầu file + [[epic-80-cau-hoi-po-ba]]. Nội dung phương án A/B/C dưới đây giữ làm lịch sử điều tra.

---

### Q1 — UI option + có bắt hoàn tiền không? (Figma ≠ SRS / BR-V2-2)

**Vì sao hỏi:** Quyết định này đổi **cả FE copy + hành vi dropdown** lẫn **điều kiện kích hoạt BE**. Sai → merchant hiểu sai + tạo / không tạo HĐĐC sai.

| Nguồn                                                                                                             | Tên option mới                                      | Helptext                                                                                                               | Hành vi UI                                      | Điều kiện kích hoạt                                                |
| ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------ |
| **SRS §6.1 + BR-V2-2**                                                                                            | "Đã hoàn trả **một phần**"                          | _"Áp dụng cho từng đơn trả hàng đã nhận hàng, bao gồm cả đơn hàng được hoàn trả toàn bộ."_ — **bỏ** cụm "và hoàn tiền" | Chọn → **tự tích + khóa** "Đã hoàn trả toàn bộ" | Chỉ `order_return.status = "returned"` — **không** check hoàn tiền |
| **Figma** [node 224:33410](https://www.figma.com/design/eB5jx4MxReLJuyrlptKhs2/SAPO-INVOICE-V2?node-id=224-33410) | "Đã hoàn trả **toàn bộ và 1 phần**"                 | _"…toàn bộ hoặc 1 phần … **và đã hoàn tiền**"_                                                                         | 3 checkbox **độc lập**, không auto-lock         | Helptext gợi ý **có** yêu cầu hoàn tiền                            |
| **V3 đã ship** (`invoice-app`)                                                                                    | "Đã hoàn trả một phần" / value `partially_refunded` | Có cụm "và hoàn tiền"                                                                                                  | Có auto-tick + khóa (đúng SRS V3)               | Cần `restocked` **+** `refunded`                                   |

**Chọn 1:**

- [ ] **A — Theo SRS V2** (khuyến nghị kỹ thuật): sửa Figma (tên + helptext bỏ "hoàn tiền" + thêm auto-lock). BE **không** check `refund_status`.
- [ ] **B — Theo Figma**: sửa SRS BR-V2-2 + §6.1. BE **phải** check thêm điều kiện hoàn tiền (cần BA định nghĩa field V2 tương đương `refund_status` — V2 hiện dùng 1 trục `order_return.status`).
- [ ] **C — Hybrid**: giữ tên/layout Figma (3 option độc lập) nhưng **bỏ** yêu cầu hoàn tiền trong helptext + BE theo SRS.

**PO trả lời:** **\_** · Owner sửa Figma/SRS: **\_** · Deadline: **\_**

---

### Q2 — `condition_value` lưu gì? BE phân biệt full vs partial thế nào?

**Vì sao hỏi:** SRS §6.1 note kỹ thuật ghi mẫu lưu `["returned"]` — trùng value với option "toàn bộ" hiện tại. FE V2 hiện chỉ có:

```ts
{ value: "returned", label: "Trả hàng toàn bộ", ... }
```

BE (`AutoInvoiceExecutionServiceImpl.adjustmentOrderStatusValueMatches`): `value == "returned"` → gọi `isFullyReturned(order)` (chỉ full). Chưa có nhánh partial.

V3 tách 2 value rõ: `fully_refunded` / `partially_refunded`.

**Chọn 1:**

- [ ] **A — Value riêng** (khuyến nghị, mirror V3):
  - Toàn bộ: giữ `"returned"` (hoặc rename rõ hơn).
  - Một phần: thêm `"partially_returned"` (hoặc tên PO chọn).
  - Runtime: value partial → xử lý từng `order_return.status=returned` theo §4.3; value full → giữ `isFullyReturned`.
- [ ] **B — Cùng value `"returned"`**: FE chỉ khác label/helptext; BE **luôn** chạy cả full+partial khi config có `"returned"`. Khi đó option "toàn bộ" vs "một phần" trên UI **không còn ý nghĩa runtime** — chỉ còn marketing copy (cần PO xác nhận chấp nhận).
- [ ] **C — Gộp 1 option duy nhất** trên UI (như Figma "toàn bộ và 1 phần") + 1 value → BE luôn partial-capable; bỏ option "toàn bộ" riêng hoặc để làm alias.

**Phụ thuộc Q1.** Nếu chọn Q1-A (auto-lock) thì gần như buộc **A** hoặc logic tương đương.

**PO trả lời:** value partial = `__________` · value full = `__________` · Cách BE map: A / B / C

---

### Q3 — Job đối soát miss-event: trong MVP hay cắt?

**Vì sao hỏi:** SRS §4.2 viết _"Retry/đối soát đơn miss event: **tái sử dụng** cơ chế job đối soát của luồng điều chỉnh toàn bộ đã có — **không viết mới**"_.

**Thực tế code V2 (`sapo-einvoice-service`, branch hiện tại):**

- Chỉ có `@Scheduled` `AutoInvoiceNotificationJob` (gửi email thông báo) — **không** có job quét đơn trả miss Kafka.
- Luồng điều chỉnh **toàn bộ** cũng **không** có job đối soát tương đương.

**Thực tế V3 (`invoice-app`, đã có trên staging):**

- Có `PartialAdjustmentReconciliationScheduler` (cron `*/30` + cutoff 23:40) quét ledger `deferred`/stale — đây là job **mới của luồng partial**, không phải "đã có từ full".

**Chọn 1:**

- [ ] **A — Trong MVP** (khuyến nghị nếu Kafka at-least-once + downtime là rủi ro thật): port pattern V3 (`PartialAdjustmentReconciliationScheduler`) sang V2; effort ~1–2d sau khi có ledger. Sửa câu SRS "tái sử dụng" → "viết mới theo mẫu V3".
- [ ] **B — Cắt khỏi MVP**: miss event → merchant tạo tay / chờ event sau. Ghi known-limitation; QA **không** mở bug nhóm J. Effort 0; rủi ro vận hành cao hơn.
- [ ] **C — Phase 2 ngay sau uplive MVP**: ship không job, ticket follow-up có ngày.

**PO trả lời:** A / B / C · Nếu C thì ticket follow-up: **\_**

---

### Q4 — STP / `apply_decimal_rounding`: snapshot trên HĐ gốc hay đọc config tenant?

**Vì sao hỏi:** SRS §4.11.1 **đã chốt** HĐĐC kế thừa **`STP_gốc` + `apply_decimal_rounding` tại lúc phát hành HĐ gốc** — độc lập config store hiện tại. Có ví dụ: nếu dùng STP hiện tại = 0 trong khi gốc STP = 2 → dòng cuối ra `66.50` trên HĐ 0 số lẻ (**sai**).

**Thực tế:**

- `EInvoice` / `EInvoiceLineItem` trên V2 **chưa** có field snapshot STP / `apply_decimal_rounding`.
- Có nhánh song song `dev-money/feature/apply-flag-decimal-config-SM-1238` (flag **cấp tenant**, không phải snapshot cấp invoice) — **lệch hướng SRS**.
- Calculator partial **bắt buộc** biết scale làm tròn → chốt trước khi viết migration + unit test.

**Chọn 1:**

- [ ] **A — Snapshot trên HĐ** (đúng SRS §4.11.1, khuyến nghị): thêm cột trên `EInvoices` (bộ digit + `ApplyDecimalRounding`) **lúc phát hành HĐ gốc**; HĐĐC đọc từ HĐ gốc. Đồng bộ với đội SM-1238 để không làm 2 hướng.
- [ ] **B — Đọc config tenant lúc tạo HĐĐC**: nhanh hơn nhưng **sai** case đổi STP giữa chừng (SRS đã bác). Chỉ chấp nhận nếu PO **sửa SRS** và chấp nhận lệch 1đ / sai precision.
- [ ] **C — MVP tạm hardcode scale = …** (vd 0 hoặc 2) + ticket snapshot sau: chỉ khi PO chấp nhận lệch số trong giai đoạn.

**PO trả lời:** A / B / C · Owner đồng bộ SM-1238: **\_** · Scale hardcode nếu C: **\_**

---

### Q5 — `order.invoices[].order_return_ids`: contract chung với #64 / #69 hay V2 tự làm?

**Vì sao hỏi:** SRS §4.6 / §4.10 bảo V2 "làm đúng như V3 epic #56". Epic #64 (parent của issue mapping) + #69 (V3 partial) **vẫn OPEN**. V2 **zero** reference `order_return_ids` trong `sapo-einvoice-service`.

**V3 đã chốt trên code (staging, chưa master):**

- Cột `invoices.order_return_ids VARCHAR(500)` CSV (`"100,200"`).
- Ghi qua API order `POST .../invoices.json`.
- **Chống trùng không dựa cột này** — dùng bảng `order_return_adjustment_ledger` `UNIQUE(store_id, order_return_id)`.

**V2 khác kênh:** Kafka + Omni V2-Order (không phải cùng order-service V3). Cần biết:

1. Order V2 đã có / sẽ có field `order.invoices[].order_return_ids` chưa?
2. Ai sở hữu API ghi ngược (einvoice-service gọi order-service)?
3. Consumer 3 đường (client / ES / DB index) — epic #80 có phải làm đủ 3 không, hay chỉ ghi liên kết đủ chống trùng + truy vết?

**Chọn 1:**

- [ ] **A — Dùng chung contract CSV `varchar(500)` với #64/#69** (khuyến nghị): sync 1 buổi với đội #64; #80 chỉ implement phía einvoice ghi/đọc theo contract đã chốt; ES/filter có thể thuộc #64.
- [ ] **B — V2 tự thiết kế** (tên field/cột khác): chấp nhận drift V2↔V3; ghi rõ trong SRS.
- [ ] **C — MVP chỉ ledger nội bộ einvoice** (chống trùng); `order_return_ids` trên order **phase 2** — chấp nhận chưa lọc được HĐ theo đơn trả từ order UI cho đến phase 2.

**PO trả lời:** A / B / C · Buổi sync với: **\_** (ngày) · Scope ES/filter thuộc epic: #64 / #80 / sau

---

### Thứ tự hỏi đề xuất (1 buổi 30–45')

1. **Q1** (business rule + copy) → khóa BR-V2-2
2. **Q2** (value kỹ thuật) — phụ thuộc Q1
3. **Q4** (STP) — block migration
4. **Q5** (`order_return_ids`) — block liên kết / có thể song song Q3
5. **Q3** (job đối soát) — quyết scope MVP / effort

Sau khi tick xong → cập nhật SRS (nếu lệch Figma) + tạo child issues theo plan.

## Thiết kế — Backend (`sapo-einvoice-service`)

Theo dependency order (việc sau phụ thuộc việc trước):

1. 🔴 **Migration**: thêm cột `order_line_item_id BIGINT NULL` vào `EInvoiceLineItems`; thêm bảng ledger mới (đề xuất tên `AutoInvoiceReturnLedger` hoặc mở rộng `AutoInvoiceResults` thêm cột `OrderReturnId BIGINT NULL` + unique index `(TenantId, OrderReturnId) WHERE OrderReturnId IS NOT NULL`); thêm cột snapshot STP trên `EInvoices` (`DecimalDigit...`, `ApplyDecimalRounding BIT`) — **chốt với câu hỏi #2 trước khi viết migration này**. T-SQL, chạy tay từng môi trường (không có Flyway auto-run theo README repo — xác nhận lại, README ghi Flyway có nhưng project-instructions ghi rõ apply thủ công).
2. 🟡 Populate `order_line_item_id`: sửa `explodeCompositeLines`/`buildExplodeCompositeLineItem` (`EInvoiceServiceImpl.java:3183,3238`) + đường build dòng HĐ thường, thread `orderLineItemId` từ `OrderLineItemResponse` nguồn xuống `EInvoiceLineItem`.
3. 🔴 Ledger + idempotency cấp order_return: claim-before-create theo `(tenantId, orderReturnId)`, thay/bổ sung cho Redis lock cấp order hiện tại trong `AutoInvoiceExecutionServiceImpl`.
4. 🟡 Relax gate `isFullyReturned()` (`AutoInvoiceExecutionServiceImpl.java:343-377`) — đây là **thay đổi lõi**, không phải thêm nhánh mới: tách rõ 2 luồng full vs partial theo bảng phân loại `Σ_returned` vs `Σ_ordered` (SRS §4.3), dùng chung `resolveFlowContext()`.
5. 🟡 Công thức phân bổ (§4.7) — module tính mới, độc lập, nên viết unit test (dùng `hddc-tester-v2.html` làm oracle đối chiếu số).
6. 🟡 Combo mapping theo `order_line_item_id` (§4.4/§4.5) — build trên field mới ở bước 2.
7. 🔴 `order.invoices[].order_return_ids` — phối hợp thiết kế với #64 trước (câu hỏi #3), rồi mới build phần ghi/đọc phía V2.
8. 🟢 Nối phí VC `separate_line` vào luồng partial — dùng lại `ShippingFeeLineHelper` sẵn có, chỉ thêm điều kiện "đơn trả hoàn tất chuỗi".
9. ⚠️ Reconciliation job — **chờ chốt câu hỏi #1**; nếu làm, đây là `@Scheduled` job mới hoàn toàn, không phải sửa job cũ.
10. Kafka: không cần topic/consumer mới — `order_return` đã nằm trong payload `OrderConsumer` hiện tại (`OrderDomain.orderReturns[]`), chỉ cần mở rộng logic xử lý trong consumer đã có.

## Thiết kế — Frontend (`sapo-frontend-v3`)

Nhỏ, độc lập với backend, không block nhau — **nhưng chờ chốt câu hỏi #5 trước khi code**, vì nó đổi cả số lượng option lẫn có cần logic auto-lock hay không:

1. 🟢 `constants.ts:40-47` — thêm 1 phần tử vào `ADJUSTMENT_ORDER_STATUS_OPTIONS`. **Tên/label theo Figma thật là "Đã hoàn trả toàn bộ và 1 phần"** (không phải "Đã hoàn trả một phần" như SRS viết) — dùng tên nào cần chốt theo câu hỏi #5. Value đề xuất `partially_returned` hoặc theo đúng `condition_value` BE dùng — **xác nhận giá trị thật BE trả về**, SRS ghi API field lưu `["returned"]` giống hệt full-return, cần hỏi lại BE cách phân biệt 2 option trên UI nếu value trùng nhau.
2. 🟢 Helptext theo `subtext` có sẵn — **KHÔNG** copy nguyên văn helptext trong Figma hiện tại (có cụm "và đã hoàn tiền" sai theo BR-V2-2, xem mục Cập nhật) — chờ bản đã sửa từ PO/designer.
3. 🟡 Auto-tick + khóa "Trả hàng toàn bộ" khi chọn option mới — **SRS mô tả có, Figma mockup hiện KHÔNG thấy** (2 checkbox đứng độc lập, không liên động trong ảnh chụp). Nếu chốt theo hướng Figma (3 option độc lập) thì **bỏ luôn việc này**, không cần logic mới trong `OrderConditionRow.tsx` — giảm effort so với đánh giá ban đầu. Chỉ làm nếu BA xác nhận SRS đúng, Figma thiếu.

## QA nên bắt tay vào việc gì trước, việc gì sau

**Trước khi code chạy (làm ngay, song song với BE thiết kế):**

- Review + bổ sung [[epic-80-test-cases]], đặc biệt nhóm Ledger/Idempotency, STP inheritance, Reconciliation-gap — đây là nơi SRS và code lệch nhau nhiều nhất, cần thống nhất "kỳ vọng đúng" trước khi có báo cáo bug sai.
- Chuẩn bị dữ liệu test bằng `hddc-tester-v2.html` (đối chiếu công thức tiền độc lập với code) — làm ngay, không phụ thuộc code xong.
- Xác nhận với BA 3 câu hỏi mở ở trên trước khi dev bắt đầu phần ledger/STP/order_return_ids (nếu không, dev có thể phải làm lại).

**Sau khi code chạy:** phần còn lại (UI, combo, phí VC, regression) theo đúng nhịp thường — không cần review sớm hơn mức bình thường vì rủi ro thấp/đã có pattern rõ.

## Liên kết

- [[epic-80-test-cases]] — bộ test case
- [[omni-einvoice-service-tong-quan]] / [[omni-frontend-v3-einvoice-tong-quan]] — kiến trúc 2 repo
- [[epic-61-phi-van-chuyen-hoa-don-v2/epic-61-test-cases]] — phí VC `separate_line` tái dùng ở BR-V2-10
- GitLab: epic [#80](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/80) · epic [#64](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/64) (order_return_ids, chưa xong) · epic [#69](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/69) (V3 song song, chưa xong)
