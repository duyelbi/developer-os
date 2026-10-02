---
created: 2026-08-27
updated: 2026-09-08
status: Đã chốt Q1–Q5 — Q2 đính chính 2026-09-08 (partially_returned = option gộp)
project: "[[10_Projects/sapo-invoice/README]]"
refs:
  - epic #80
  - Plan: [[epic-80-plan]]
  - Figma: SAPO-INVOICE-V2 node 224:33410
  - V3 ref: invoice-app partial (staging)
---

# Epic #80 — Quyết định PO/BA (Q1–Q5)

> Tài liệu này **đã chốt** (2026-08-27). Chi tiết phân tích / phương án cũ giữ ở [[epic-80-plan]].

## Bảng quyết định

| #      | Chủ đề                      | Quyết định                                                                                                                                                                                                                                                                 |
| ------ | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q1** | UI + hoàn tiền              | **Theo Figma** (text + **rule BE**). Option mới: _"Đã hoàn trả toàn bộ và 1 phần"_ + helptext có _"đã hoàn tiền"_. Checkbox độc lập, **không** auto-lock. BE check `order_return.refundStatus` (cùng `status = returned`). **BA sửa SRS** BR-V2-2 / §6.1 cho khớp.         |
| **Q2** | `condition_value` + runtime | Chỉ toàn bộ → `["returned"]`. Option gộp **“Đã hoàn trả toàn bộ và 1 phần”** → FE lưu **`["partially_returned"]`** (không bắt buộc kèm `returned`). Chọn cả 2 option UI → `["returned","partially_returned"]`. Runtime **2 engine**: trả đủ lần đầu → Full; trả dở / hoàn tất chuỗi → Partial. `partially_returned` **bao phủ** cả trả đủ lẫn trả dở. |
| **Q3** | Job đối soát                | **Có trong MVP** — port `PartialAdjustmentReconciliationScheduler` (V3). **BA sửa SRS** §4.2: viết mới theo mẫu V3, không “tái sử dụng job full”.                                                                                                                          |
| **Q4** | Làm tròn / STP              | **Mirror V3**: kế thừa số đã chốt trên dòng HĐ gốc + `MONEY_SCALE = 0`. **Không** snapshot STP §4.11 trong MVP. **BA ghi chú SRS** §4.11.                                                                                                                                  |
| **Q5** | `order_return_ids`          | **Làm như V3**: ledger chống trùng bắt buộc + lưu trên HĐ + **đẩy `order.invoices[].order_return_ids` sang Order**. Chi tiết API/format sync epic #64 khi implement lớp sync.                                                                                              |

## Q2 — Mapping config (chi tiết đã chốt — đính chính 2026-09-08)

| Merchant chọn (UI)                    | `condition_value[]`                  | Gate + engine |
| ------------------------------------- | ------------------------------------ | ------------- |
| Chỉ **Đã hoàn trả toàn bộ**           | `["returned"]`                       | Chỉ đơn trả đủ → **FullEngine** |
| Chỉ **Đã hoàn trả toàn bộ và 1 phần** | `["partially_returned"]`             | Trả đủ **hoặc** trả dở. Trả đủ lần đầu → **FullEngine**; trả dở / hoàn tất chuỗi → **PartialEngine** |
| Chọn **cả 2**                         | `["returned", "partially_returned"]` | Giống option gộp (dedupe). Trả đủ lần đầu → Full; trả dở → Partial |

> **Đính chính:** FE **không** gộp lưu `returned` khi chỉ tick option gộp. BE coi `partially_returned` đã bao phủ trả đủ — không đòi `condition_value` có `returned` mới Full.

```
config chỉ ["returned"]
  → FullEngine khi isFullyReturned (+ refundStatus)
  → trả dở: skip (không fallback Full)

config có ["partially_returned"]  (± "returned")
  → router Σ / isFullyReturned / hasPriorPartial:
       partial              → PartialEngine (1 HĐĐC / 1 order_return)
       full lần đầu         → FullEngine (copy HĐ gốc)  // kể cả chỉ partially_returned
       hoàn tất chuỗi       → PartialEngine
```

Gate phiếu trả (cả 2 nhánh khi bật trả hàng):  
`order_return.status == "returned"` **AND** `refundStatus` ∈ {`paid`, `refunded`} (Omni V2 dùng `paid`).

## Q5 — 2 lớp (như V3)

1. **Ledger** `UNIQUE(tenantId, orderReturnId)` — claim trước tạo HĐ
2. **`order_return_ids`** trên HĐ einvoice + sync sang Omni V2-Order (`order.invoices[]`)

## Việc sau chốt

**BA / `invoice-docs` (không do dev update):**

- [ ] Cập nhật SRS: BR-V2-2 (+ hoàn tiền), §6.1 (Figma, bỏ auto-lock), §4.2 (job mới), §4.11 (MVP scale=0 mirror V3)
- [ ] Comment quyết định lên GitLab epic #80 (nếu cần)

**Dev / tracking:**

- [x] Ghi quyết định Q1–Q5 vào developer-os (`epic-80-cau-hoi-po-ba`, `epic-80-plan`)
- [x] Tạo 2 child issues (#94 BE, #95 FE) — assignees `duynd7` + `phuongnt20`

## Child issues GitLab (đã tạo 2026-08-27)

Assignee: `duynd7` (Nguyễn Đức Duy) + `phuongnt20` (Nguyễn Thùy Phương) · Parent: epic [#80](https://git.dktsoft.com:2008/groups/sapo-money/sapo-invoice/-/work_items/80)

| #                                                                                        | Title                                                               |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| [#94](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/work_items/94) | `[V2][BE] Tự động tạo & phát hành HĐ điều chỉnh cho đơn trả 1 phần` |
| [#95](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/invoice-docs/-/work_items/95) | `[V2][FE] Bổ sung option "Đã hoàn trả toàn bộ và 1 phần" (Figma)`   |

> Work item GitLab nằm dưới project `invoice-docs` chỉ để gắn hierarchy epic (cùng pattern epic #61). **Nội dung SRS trong repo invoice-docs do BA cập nhật** — không nằm trong phạm vi dev.
