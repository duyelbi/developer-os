---
created: 2026-07-31
status: Proposed
scope: "sapo-invoice-admin-frontend — cách thực thi refactor theo slice dọc (từng feature/màn hình), kiểm soát rủi ro"
---

# Playbook refactor theo từng màn hình

> Chiến lược thực thi cho [[10_Projects/sapo-invoice/refactor-frontend-performance]]. File kia = chẩn đoán + nguyên nhân gốc; file này = cách chia việc và checklist lặp lại.

## 1. Cái KHÔNG chia theo màn hình được

Trước khi chia dọc, phải chấp nhận có một lõi ngang không cắt được. Ép nó vào slice màn hình sẽ **tăng** rủi ro: endpoint dùng chung ở trạng thái nửa vời còn nguy hiểm hơn sửa một lần.

| Việc | File | Vì sao không cắt được |
|---|---|---|
| 4 mutation invalidate chết | `src/api.ts` (2) + `pages/invoice-collector/api.ts` (2) | Là bug correctness, không thuộc màn hình nào |
| Tách tag `savedSearch` theo `type` | `src/api.ts` | **92 file / 20 feature** cùng chạm `SavedSearch`. Đổi shape `providesTags` là đổi hợp đồng cho mọi consumer cùng lúc |
| Gộp `getProfile` → `getCurrentUser` | `src/api.ts` + `pages/account/api.ts` | Endpoint chung, 9 call site rải nhiều feature |
| `keepUnusedDataFor` cho endpoint dùng chung | `src/api.ts` | `tenant`, `tenant_settings`, `certificates`, `tax_authorities`, `decimal_configurations` — mọi màn hình dùng |
| Phá waterfall `<Outlet/>` | `pages/admin/components/AdminLayout.tsx` | Một file, ảnh hưởng mọi route |
| `manualChunks` | `vite.config.ts` | Cấu hình build |
| Middleware đếm request (baseline) | `src/store/` | Phải có trước mới đo được từng slice |

**Tổng ~1,5 ngày.** Gọi là **Sprint 0**. Làm xong mới bắt đầu chia màn hình — vì nếu không, mỗi slice sẽ phải tự vá lại cùng một chỗ.

> Điểm dễ nhầm: tag `savedSearch` *trông* như việc của từng màn hình (mỗi màn hình có bộ lọc riêng) nhưng thực chất là hợp đồng dùng chung. Đây là hạng mục duy nhất trong Sprint 0 có thể gây regression rộng — nên đi kèm smoke test cả 20 màn hình danh sách.

## 2. Cái chia theo màn hình được

Phần còn lại — chiếm phần lớn khối lượng — cắt sạch theo `src/pages/<feature>/`, vì mỗi feature đã có sẵn `api.ts`, `hooks/`, `components/`, `routes.tsx` riêng.

| Việc | Phân bố |
|---|---|
| Xoá `refetchOnMountOrArgChange` | 117 chỗ, nằm trong từng feature |
| Tag granularity cho domain riêng | mỗi `pages/<feature>/api.ts` |
| Gom invalidate cho bulk N+1 | 13 file, mỗi cái thuộc 1 feature |
| Hạ state xuống đúng tầng, `memo`, `selectFromResult` | từng màn hình |
| Dynamic import lib nặng | `invoice-statement`, `e-document`, `template` |
| Xoá component trùng, chuyển sang DS | từng màn hình |

## 3. Phát hiện quyết định thứ tự: 24 feature nhưng chỉ ~5 khuôn

`e-document/*` là **bản sao cấu trúc** của các module invoice-side, cùng quy ước đặt tên file:

| e-document | Bản gốc | Khuôn file chung |
|---|---|---|
| `e-document/registration` | `registration` | `XList.tsx` · `XListPage.tsx` · `XManagerPage.tsx` · `XTable.tsx` · `routes.tsx` |
| `e-document/taxpayer` | `customer` | ″ |
| `e-document/template` | `template` | ″ |
| `e-document/tax-document` | `invoice` | ″ |
| `e-document/tax-document-mistake` | `invoice-mistake` | ″ |
| `e-document/transmission-history` | `transmission-history` | ″ |

Năm khuôn lặp lại trong toàn repo:

| # | Khuôn | Số lần lặp | Đặc trưng |
|---|---|---|---|
| K1 | **List + SavedSearch + Filters + Table** | ~20 | `XListPage` + `XTable`, tab saved search, setting column, phân trang |
| K2 | **Manager / form chi tiết** | ~15 | `XManagerPage`, `useCustomForm`, query chi tiết + mutation create/update |
| K3 | **Publish / Transmit modal** | ~8 | `getTenantCertificate` + `getTenantSettingInvoice` + ký USB/remote |
| K4 | **Bulk action trên table** | 13 | `ids.map(async id => …)` |
| K5 | **Import modal** | 4 | dropzone + parse file + upload |

**Hệ quả cho cách chia việc:** đừng xếp thứ tự theo feature, xếp theo **khuôn**. Làm xong một khuôn ở màn hình pilot thì 19 màn hình còn lại của khuôn đó là áp lại công thức, không phải nghĩ lại. Rủi ro giảm theo cấp số nhân sau slice đầu tiên.

## 4. Chọn màn hình pilot

Số liệu từng feature (LOC · file · hook API · cờ refetch · useState · table · savedSearch · bulk):

| feature | LOC | hook | refetch | useState | table | savedS | bulk | ghi chú |
|---|---|---|---|---|---|---|---|---|
| `transmission-history` | 2.559 | 3 | 1 | 8 | 2 | 2 | 0 | quá đơn giản, không đại diện |
| **`cancelled-invoices`** | **2.213** | **12** | **4** | **15** | **3** | **4** | **2** | **nhỏ nhất mà có ĐỦ 5 khuôn** |
| `customer` | 2.790 | 20 | 4 | 7 | 1 | 6 | 0 | pilot 2 |
| `product` | 3.433 | 28 | 4 | 8 | 2 | 5 | 0 | pilot 3 |
| `invoice` | 21.527 | 79 | 12 | 94 | 5 | 8 | 2 | để cuối |
| `e-document` | 30.160 | 124 | 26 | 134 | 15 | 24 | 5 | để cuối |

**Pilot = `cancelled-invoices`.** Nhỏ nhất trong nhóm có đủ K1+K2+K3+K4, nghiệp vụ hẹp (hoá đơn đã huỷ — ít traffic, sai thì bán kính nhỏ), và có sẵn cả `component/CancelInvoiceModal` lẫn `hooks/` nên đại diện được cấu trúc chuẩn.

**Thứ tự đề xuất:**

1. **Sprint 0** — lõi ngang §1 (~1,5 ngày)
2. **`cancelled-invoices`** — pilot, vừa làm vừa viết playbook §5 cho chính xác
3. **`customer`** + **`product`** — chứng minh playbook lặp lại được, đo xem slice 2–3 có nhanh hơn slice 1 không
4. **Cặp gương**: `registration` → `e-document/registration`, `customer` → `e-document/taxpayer`, `template` → `e-document/template`, `invoice-mistake` → `e-document/tax-document-mistake`. Làm bản gốc trước, bản sao ngay sau — lúc đó công thức còn nóng
5. **`invoice`** và **`e-document/tax-document`** cuối cùng — lớn nhất, rủi ro cao nhất, làm khi playbook đã chín

## 5. Checklist một màn hình

Chạy đúng thứ tự này cho mỗi slice. Mỗi bước là một commit riêng để rollback được từng phần.

**Bước 0 — đo trước**
- [ ] Ghi số request khi vào màn hình (cold + warm) từ middleware đếm
- [ ] Ghi số lần render của `XTable` (React DevTools Profiler)
- [ ] Chụp lại luồng nghiệp vụ chính để so sau

**Bước 1 — tag cho domain riêng** (`pages/<feature>/api.ts`)
- [ ] Query danh sách → `providesTags` theo `{type, id}` + `{type, id: "LIST"}`
- [ ] Query chi tiết → `providesTags: [{ type, id }]`
- [ ] Mutation update → invalidate đúng `{type, id}`; create/delete → `{type, id: "LIST"}`
- [ ] Rà mutation trả `void` mà invalidate theo `result` (bug §1 của plan) — đổi sang điều kiện theo `error`
- [ ] Query nào không cần tag (preview/job/lookup) thì ghi comment nói rõ lý do

**Bước 2 — bỏ cờ refetch** *(chỉ sau khi bước 1 xanh)*
- [ ] Xoá mọi `refetchOnMountOrArgChange: true` trong feature
- [ ] Khai `keepUnusedDataFor` ở endpoint theo độ tươi thật của dữ liệu
- [ ] Xoá `refetch()` gọi tay sau mutation nếu tag đã phủ
- [ ] **Nghiệm thu:** đi 3 vòng `list → detail → back`, vòng 2–3 không sinh request mới

**Bước 3 — bulk (nếu có K4)**
- [ ] `Promise.all` + **một** lần `invalidateTags` ở cuối, bỏ invalidate khỏi mutation đơn lẻ
- [ ] Ghi ticket backend cho bulk endpoint thật

**Bước 4 — rerender**
- [ ] Selection state (`useIndexResourceState`) chuyển từ `XListPage` xuống `XTable`
- [ ] Mỗi modal tự giữ state mở/đóng trong component riêng
- [ ] Object literal truyền xuống table bọc `useMemo`
- [ ] `memo` cho `XTable`, tách `XRow` riêng nếu bảng > 50 dòng
- [ ] `selectFromResult` cho component chỉ cần một phần kết quả query

**Bước 5 — component**
- [ ] Đối chiếu component nội bộ dùng trong màn hình với [[10_Projects/design-system/audit-coverage-invoice]] §3.1 — cái nào DS đã có thì xoá
- [ ] Cái nào generic mà DS chưa có → ghi vào backlog DS, **không** tự viết thêm bản mới trong app

**Bước 6 — đo lại + chốt**
- [ ] So số request / số render với bước 0, ghi vào bảng theo dõi
- [ ] Chạy lại luồng nghiệp vụ chính
- [ ] Nếu slice này là màn hình đầu của một khuôn → cập nhật playbook này bằng cái học được

## 6. Definition of done cho một slice

Một màn hình coi là xong khi đủ cả 4:

1. **Không còn `refetchOnMountOrArgChange`** trong thư mục feature đó.
2. **Đi 3 vòng `list → detail → back` không sinh request lặp** — kiểm bằng middleware đếm, không kiểm bằng cảm nhận.
3. **Số request cold load giảm** so với bước 0, có số ghi lại.
4. **Luồng nghiệp vụ chính không đổi hành vi** — đặc biệt: dữ liệu sau khi tạo/sửa/xoá phải cập nhật đúng mà không cần reload (đây chính là thứ 117 cờ refetch đang che).

## 7. Rủi ro của chính cách chia này

Nói trước để không bị bất ngờ:

- **Sprint 0 vẫn là thay đổi rộng.** Chia dọc không xoá được rủi ro này, chỉ dồn nó vào một chỗ có kiểm soát. Đổi lại: một lần review kỹ thay vì 20 lần vá vặt.
- **Slice đầu sẽ chậm bất thường** — vừa làm vừa dựng playbook. Đừng lấy tốc độ slice 1 để ước lượng 23 slice còn lại; lấy slice 2–3.
- **Hai hệ tồn tại song song trong lúc chuyển tiếp** (màn hình đã refactor cạnh màn hình chưa). Chấp nhận được vì ranh giới là thư mục feature, nhưng cần rule: **màn hình chưa refactor thì không thêm `refetchOnMountOrArgChange` mới** — chặn bằng ESLint rule là chắc nhất.
- **Cặp gương dễ bị lệch.** Làm `registration` mà quên `e-document/registration` thì hai bản sao trôi khác nhau, lần sau khó gộp hơn. Nên làm liền cặp, không xen slice khác vào giữa.
- **Backend chưa sẵn.** Bulk endpoint, `X-Total-Count`, `/api/bootstrap` là việc của BE — mở ticket từ Sprint 0 để chúng chạy song song, đừng để slice cuối mới phát hiện thiếu.
