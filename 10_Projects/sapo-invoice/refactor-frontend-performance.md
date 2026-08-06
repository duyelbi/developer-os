---
created: 2026-07-31
status: Proposed
scope: "sapo-invoice-admin-frontend — refactor toàn repo: giảm thời gian call API, khử duplicate call, khử rerender thừa; đánh giá SSR"
---

# Refactor `sapo-invoice-admin-frontend` — API latency, duplicate call, rerender

> Repo: `/Users/sapo/invoice/sapo-invoice-admin-frontend`. Số liệu đo 2026-07-31.
> Phần design-system tách riêng: [[10_Projects/design-system/audit-coverage-invoice]]
> Liên quan: [[10_Projects/sapo-invoice/ai/rules-frontend]], [[10_Projects/sapo-invoice/migrate-ui-components-sang-design-system]]

## 0. Hiện trạng đo được

| Chỉ số | Giá trị |
|---|---|
| File `.ts`/`.tsx` / LOC | 954 / 183.438 |
| File > 1000 dòng | 23 (lớn nhất `RegistrationManagerPage.tsx` 3.968) |
| `createApi` / file `injectEndpoints` | 2 / 31 |
| `builder.query` / `builder.mutation` | 172 / 151 |
| Query **không** có `providesTags` | 28 |
| Mutation **không** có `invalidatesTags` | 15 |
| Mutation có invalidate nhưng **không bao giờ chạy** | **4** (xem §1.A) |
| `refetchOnMountOrArgChange: true` | **117** (không nơi nào dùng số giây) |
| `keepUnusedDataFor` / `selectFromResult` / `refetchOnFocus` | **0 / 0 / 0** |
| `providesTags` / trong đó có granularity `{type, id}` | 144 / **3** |
| File gọi `refetch()` tay ngay sau mutation | **8** |
| `memo(...)` toàn repo | **15** / 954 file |
| `useSelector` | 8 (tốt — server state nằm ở RTK Query) |
| Chunk JS lớn nhất | `index.js` **922 KB** · `DashboardPage` 595 KB · `html2pdf` 668 KB |
| `src/assets/images` | **12 MB** (`L001.svg` 3,0 MB · `V004.svg` 2,0 MB · `V002.svg` 1,4 MB) |

---

## 1. Chẩn đoán theo nguyên nhân gốc

Ba nhóm triệu chứng (API chậm / duplicate / rerender) quy về **hai** nguyên nhân gốc độc lập nhau. Việc tách đúng hai cái này quyết định thứ tự refactor.

### A. Nguyên nhân gốc #1 — tầng invalidation không đáng tin

Không phải "thiếu cache". Cache có, nhưng **không ai tin nó**, nên bị vô hiệu hoá bằng tay ở 117 chỗ. Chuỗi nhân quả:

```
tag thô (144 providesTags, chỉ 3 có {type,id})
   + 4 mutation invalidate chết
   + 28 query không có tag
        ↓  invalidation không đáng tin
   dev gọi refetch() tay sau mutation (8 file)
   + refetchOnMountOrArgChange: true (117 chỗ)
        ↓
   duplicate call  +  bug tag thật bị che, không ai phát hiện
```

**A1 · 4 mutation có `invalidatesTags` nhưng không bao giờ chạy.** Mutation trả `void` nhưng invalidate lại điều kiện theo `result`, mà `result` luôn `undefined`:

| Mutation | File |
|---|---|
| `resetErrorInvoiceAutoConfig` | `src/api.ts:709` |
| `updateIdentityNumber` | `src/api.ts:780` |
| `deleteInvoiceCollectorConfiguration` | `src/pages/invoice-collector/api.ts` |
| `deleteTaxInvoiceConfiguration` | `src/pages/invoice-collector/api.ts` |

Đây là **bug correctness**, không phải bug hiệu năng: đổi mã số thuế xong, `getTenant` không refetch, UI hiển thị mã cũ cho tới khi reload.

**A2 · Một tag `"savedSearch"` phủ ~40 loại dữ liệu khác nhau.** `SavedSearchType` có 40 giá trị (`invoices`, `products`, `setting_column_invoice`, `setting_column_report_invoice_detail`, …). Cả `getSavedSearches` lẫn `getSavedSearch` đều `providesTags: ["savedSearch"]`; cả 3 mutation create/update/delete đều `invalidatesTags: ["savedSearch"]` vô điều kiện.

Hệ quả trên trang danh sách hoá đơn — người dùng **ẩn một cột**:

```
updateSavedSearch(type="setting_column_invoice")
  → invalidate tag "savedSearch"
  → refetch getSavedSearches("invoices")               ← không liên quan
  → refetch getSavedSearches("setting_column_invoice")
  → refetch getSavedSearch(id) nếu đang mở một bộ lọc  ← không liên quan
  → + refreshGetSettingColumn() gọi tay ngay sau đó    ← LẶP LẠI cái thứ 2
```

4 request cho một thao tác đổi hiển thị cột, trong đó 3 là thừa.

**A3 · Manual refetch chồng lên tag invalidation — 8 file.** Cùng một pattern `await updateSavedSearch(...).unwrap()` rồi `refreshGetSettingColumn()`:
`InvoiceTable.tsx:596` · `CustomerTable.tsx:171` · `TaxpayerTable.tsx:303` · `TaxDocumentTable.tsx:218` · `InvoiceCollectorTable.tsx:323` · `InvoiceDetailTable.tsx:103` · `InvoiceSummaryTable.tsx:104` · `ContentLineItem.tsx:591`

**A4 · Endpoint trùng URL.** `/api/users/profile` khai 2 lần — `getCurrentUser` (`src/api.ts:373`) và `getProfile` (`src/pages/account/api.ts:16`). Hai cache key ⇒ 2 request cho cùng payload, và `auth.account` chỉ được nuôi bởi cái thứ nhất. Tương tự `/api/transmissions` (`src/api.ts:486` + `transmission-history/api.ts:23`).

**A5 · Vòng lặp mutation N+1 — 13 file.** `ids.map(id => deleteX(id).unwrap())`: xoá 50 dòng = 50 request + 50 lần invalidate tag.

### B. Nguyên nhân gốc #2 — thứ tự khởi động chặn nhau

Độc lập hoàn toàn với (A). Đường đi một lần load `/admin/invoices` nguội:

```
1. HTML (nginx)
2. index.js 922 KB          ← parse xong mới chạy
3. AppLoader                ← await refresh_token, BLOCKING
4. AdminLayout              ← 3 query song song: tenant, tenant_settings, users/profile
     return tenant && currentUser ? <AdminFrame><Outlet/></AdminFrame> : <PageLoading/>
                                                    ↑ CHẶN
5. chunk InvoiceListPage    ← React.lazy chỉ fetch KHI được render → đợi bước 4
6. query của page           ← đợi bước 5 parse xong
```

Bước 4→5 là điểm chết: chunk JS của trang đích **không tải song song** với 3 request bootstrap. Đây là độ trễ thuần do thứ tự, không phải do backend chậm.

### C. Triệu chứng phái sinh — rerender

Không phải nguyên nhân gốc, mà là hệ quả của **state đặt sai tầng**: page 500–4.000 dòng giữ state modal/selection, mọi `setState` nhỏ rerender cả bảng 1.454 dòng. `filterParams={{...}}` inline ở `InvoiceListPage.tsx:403` khiến memo (nếu có) vô hiệu. 15 `memo` trên 954 file, 0 `selectFromResult`.

---

## 2. Thứ tự refactor

> **Chiến lược thực thi đã chọn: slice dọc theo từng màn hình.** Cách chia việc, checklist lặp lại và thứ tự màn hình nằm ở [[10_Projects/sapo-invoice/refactor-playbook-theo-man-hinh]]. Mục §2 dưới đây giữ nguyên phần *nội dung kỹ thuật* của từng hạng mục (nguyên nhân → giải pháp → kết quả → ví dụ); playbook quyết định *thứ tự và phạm vi* áp dụng chúng.

Hai nguyên nhân gốc độc lập ⇒ **hai track chạy song song được**. Bên trong mỗi track thì thứ tự là bắt buộc.

> **Điểm quan trọng nhất:** không được xoá 117 `refetchOnMountOrArgChange` trước khi sửa tag. Chúng đang là lớp che cho invalidation hỏng — gỡ trước sẽ biến bug ẩn thành bug hiện (stale data trước mặt người dùng).

| | Track A — đường tải trang | Track B — tầng data |
|---|---|---|
| Nguyên nhân | §1.B | §1.A |
| Rủi ro | Thấp (không đụng logic nghiệp vụ) | Trung bình (đụng correctness) |
| Thứ tự nội bộ | A1 → A2 độc lập nhau | **B1 → B2 → B3 bắt buộc theo thứ tự** |
| Bắt đầu | Ngay | Ngay |

### Bước 0 — Baseline (bắt buộc, trước cả hai track)

Không có số trước thì không chứng minh được số sau. Ba thứ, đều dev-only:

1. Middleware đếm request theo route, log endpoint bị gọi > 1 lần trong 2 s.
2. `rollup-plugin-visualizer` để chốt số bundle.
3. Bảng baseline 5 route chính: số request · TTI · số lần render bảng (React DevTools Profiler).

---

### TRACK B — tầng data (làm đúng thứ tự)

#### B1 · Sửa tầng invalidation ← **việc phải làm đầu tiên**

**Nguyên nhân.** §1.A1–A3. Tag thô + 4 invalidate chết ⇒ dev mất niềm tin ⇒ workaround bằng tay.

**Giải pháp.** Ba việc, làm cùng lô:

*(a) Sửa 4 invalidate chết* — bỏ điều kiện theo `result` với mutation `void`, chuyển sang điều kiện theo `error`:

```ts
// TRƯỚC — src/api.ts:780, result luôn undefined ⇒ không bao giờ invalidate
updateIdentityNumber: builder.mutation<void, { new_tax_code: string }>({
  invalidatesTags: (result) => (result ? ["tenant"] : []),
})

// SAU
updateIdentityNumber: builder.mutation<void, { new_tax_code: string }>({
  invalidatesTags: (_result, error) => (error ? [] : ["tenant"]),
})
```

*(b) Tách tag `savedSearch` theo `type`* — mỗi loại saved search là một tag riêng:

```ts
// TRƯỚC — 1 tag phủ 40 loại
getSavedSearches: builder.query<SavedSearch[], SavedSearchType>({
  providesTags: ["savedSearch"],
})
createSavedSearch: builder.mutation<SavedSearch, SavedSearchRequest>({
  invalidatesTags: ["savedSearch"],
})

// SAU — tag mang theo type
getSavedSearches: builder.query<SavedSearch[], SavedSearchType>({
  providesTags: (_r, _e, type) => [{ type: "savedSearch" as const, id: type }],
})
createSavedSearch: builder.mutation<SavedSearch, SavedSearchRequest>({
  invalidatesTags: (_r, e, { type }) =>
    e ? [] : [{ type: "savedSearch" as const, id: type }],
})
```

*(c) Xoá 8 chỗ `refetch()` gọi tay* sau khi (b) đã đúng — chúng thành thừa.

**Kết quả.** Thao tác ẩn một cột: **4 request → 1**. Đổi mã số thuế: UI cập nhật đúng thay vì phải reload. Quan trọng hơn — sau bước này invalidation mới đủ tin cậy để làm B2.

**Sau đó mở rộng cùng công thức cho 6 domain nặng nhất** (invoice, template, registration, customer, product, invoice_mistake):

```ts
const listTag = <T extends string>(type: T, items?: { id: number }[]) =>
  items
    ? [...items.map(({ id }) => ({ type, id })), { type, id: "LIST" as const }]
    : [{ type, id: "LIST" as const }];

getInvoicesWithCount: { providesTags: (r) => listTag("invoice", r?.invoices) }
getInvoice:           { providesTags: (_r, _e, id) => [{ type: "invoice", id }] }
updateInvoice:        { invalidatesTags: (_r, e, { id }) => (e ? [] : [{ type: "invoice", id }]) }
createInvoice:        { invalidatesTags: (_r, e) => (e ? [] : [{ type: "invoice", id: "LIST" }]) }
```

⇒ Sửa 1 hoá đơn chỉ refetch đúng hoá đơn đó, không kéo theo list + count + config.

**Công sức.** (a)(b)(c) ~1 ngày. Mở rộng 6 domain ~2–3 ngày.

---

#### B2 · Xoá 117 `refetchOnMountOrArgChange: true` ← **chỉ sau khi B1 xong**

**Nguyên nhân.** Là hệ quả của B1, không phải bệnh độc lập. Nó vô hiệu hoá cache: mọi lần mount lại (mở modal, đổi tab, back/forward, remount do parent rerender) đều bắn lại request kể cả dữ liệu vừa lấy 2 giây trước.

**Giải pháp.** Chuyển chính sách cache từ **call site** lên **endpoint**:

```ts
// TRƯỚC — src/pages/invoice/InvoiceListPage.tsx:141
useGetInvoicesWithCountQuery(args, {
  refetchOnMountOrArgChange: true,   // ← xoá
  skip: isLoadingFilters,
})

// SAU — call site sạch, chính sách khai ở endpoint
useGetInvoicesWithCountQuery(args, { skip: isLoadingFilters })
```

```ts
// khai một lần ở endpoint
getTenant:                 { keepUnusedDataFor: 3600 }   // gần như tĩnh
getDecimalConfigurations:  { keepUnusedDataFor: 3600 }
getTaxAuthorities:         { keepUnusedDataFor: 3600 }
getTenantSettings:         { keepUnusedDataFor: 600 }
getTenantCertificate:      { keepUnusedDataFor: 300 }
getSavedSearches:          { keepUnusedDataFor: 300 }
getInvoicesWithCount:      { keepUnusedDataFor: 60 }     // dựa vào tag, không refetch mù
```

Chỗ thật sự cần dữ liệu mới: dùng `refetchOnMountOrArgChange: 30` (**số giây**, không phải `true`), hoặc bật `refetchOnFocus` một lần ở `setupListeners` cho toàn app.

**Kết quả.** Đi `list → detail → back` không còn request lặp. Ước tính −40~60% số request/route (chốt bằng baseline bước 0).

**Nghiệm thu.** Mở DevTools Network, đi 3 vòng `list → detail → back`; vòng 2 và 3 không được sinh request mới ngoài những gì tag hợp lệ yêu cầu.

**Công sức.** ~1 ngày.

---

#### B3 · Gộp endpoint trùng + gom invalidate cho bulk

**Nguyên nhân.** §1.A4, §1.A5.

**Giải pháp.**

```ts
// (a) Xoá getProfile ở src/pages/account/api.ts, re-export hook chung
export { useGetCurrentUserQuery } from "app/api";   // 6 call site đổi import
```

```ts
// (b) Bulk: TRƯỚC — 50 request + 50 lần invalidate
const promises = ids.map(async (id) => { await deleteInvoice(id).unwrap(); });
await Promise.all(promises);

// SAU — vẫn 50 request (tới khi BE có bulk endpoint) nhưng 1 lần invalidate
await Promise.all(ids.map((id) => deleteInvoice(id).unwrap().catch(collectError)));
dispatch(adminApi.util.invalidateTags([{ type: "invoice", id: "LIST" }]));
// kèm: bỏ invalidatesTags khỏi deleteInvoice khi chạy trong vòng lặp
```

**Kết quả.** (a) bớt 1 request trên **mọi** trang có menu user. (b) bão refetch sau bulk delete: từ ~50 đợt xuống 1.

**Việc cho backend (mở ticket song song):** `DELETE /api/invoices/bulk`; `X-Total-Count` header thay endpoint `/count` (bỏ được 1 request/màn hình danh sách × ~15 module); `GET /api/bootstrap` gộp tenant + tenant_settings + users/profile (3 round-trip → 1 trên mọi lần load app).

**Công sức.** ~1 ngày FE.

---

### TRACK A — đường tải trang (chạy song song với Track B)

#### A1 · Phá waterfall AdminLayout → route chunk ← **thắng lớn nhất về TTI**

**Nguyên nhân.** §1.B. `AdminLayout` không render `<Outlet/>` cho tới khi `tenant` và `currentUser` về ⇒ `React.lazy` của trang đích chưa được render nên chưa bắt đầu tải chunk.

**Giải pháp.**

```tsx
// TRƯỚC — src/pages/admin/components/AdminLayout.tsx:97
return tenant && currentUser ? (
  <AdminFrame>{children ?? <Outlet />}</AdminFrame>
) : (
  <AppLayout>{loadingMarkup}{errorMarkup}</AppLayout>
);

// SAU — Outlet render ngay, chunk bắt đầu tải song song với 3 query bootstrap
return (
  <AdminFrame>
    {isLoading && <PageLoading loadingIndicator={false} />}
    {errorMarkup}
    <div hidden={isLoading}>{children ?? <Outlet />}</div>
  </AdminFrame>
);
```

Kèm theo — khởi động 3 query bootstrap sớm ngay trong loader, **không `await`**:

```ts
// src/App.tsx — AppLoader
store.dispatch(adminApi.endpoints.getTenant.initiate());
store.dispatch(adminApi.endpoints.getCurrentUser.initiate());
store.dispatch(adminApi.endpoints.getTenantSettings.initiate());
// hook trong AdminLayout sẽ dùng lại cache, không gọi lại
```

**Kết quả.** Bỏ một tầng serial khỏi **mọi** trang. Ước tính −400~900 ms cold load (chốt bằng baseline).

**Cần kiểm khi làm.** Các trang đang ngầm giả định `tenant`/`currentUser` đã có khi render — sau thay đổi này chúng có thể render sớm hơn. Rà các chỗ đọc `useCurrentUser()` (hook này `throw` khi chưa có user).

**Công sức.** ~0,5 ngày.

#### A2 · Bundle + asset

**Nguyên nhân.** `vite.config.ts` không có `manualChunks` ⇒ vendor gom hết vào `index.js` 922 KB. Ba lib nặng import tĩnh. 12 MB ảnh preview.

**Giải pháp.**

```ts
// vite.config.ts
build: {
  manifest: true,
  rollupOptions: { output: { manualChunks: {
    react: ["react", "react-dom", "react-router-dom"],
    redux: ["@reduxjs/toolkit", "react-redux", "redux-persist"],
    ui:    ["@sapo/ui-components", "@sapo/ui-icons", "@emotion/react", "@emotion/styled"],
    charts:["highcharts", "highcharts-react-official", "@sapo/ui-viz"],
  }}},
},
```

```ts
// TRƯỚC — src/pages/template/TemplateManagerPage.tsx:52
import * as cheerio from "cheerio";
// SAU — chỉ cần khi mở editor
const cheerio = await import("cheerio");

// tương tự html2pdf.js ở 3 file: InvoiceStatementManagePage,
// TaxDocumentStatementManagePage, TaxDocumentStatementView
```

Ảnh: `src/pages/template/constants.ts` đang import 9 SVG preview 0,3–3,0 MB. Chuyển sang WebP ~40–80 KB cho picker, giữ SVG gốc chỉ cho bản in nếu thật sự cần.

**Kết quả.** `index.js` 922 KB → ~350–450 KB. Trang Template và Statement nhẹ ~800 KB. Picker mẫu hoá đơn từ 12 MB → dưới 1 MB.

**Công sức.** ~0,5 ngày (chưa tính chuyển ảnh).

---

### TRACK C — rerender (chưa phải bây giờ)

**Lý do hoãn.** Sau Track A + B, baseline thay đổi hẳn — số lần rerender đo lại có thể ưu tiên khác. Và công sức/đơn vị ở đây cao nhất trong cả ba track. Hai việc khi tới lượt:

- **C1 · POC React Compiler** (~2 ngày). Với 183k LOC và 15 `memo`, memo hoá tay toàn repo là bất khả thi. `babel-plugin-react-compiler` + `react-compiler-runtime` tự memo hoá ở compile time. Rủi ro phải POC trước: tương thích thứ tự với `@emotion/babel-plugin`; tỉ lệ component bị bail-out do vi phạm Rules of Hooks. Bật cho **một** thư mục (`src/pages/invoice`) trước, đo bằng Profiler.
- **C2 · Hạ state xuống đúng tầng** (~1 ngày/trang, cho 6 trang nặng nhất): selection state từ page xuống table; mỗi modal tự giữ state mở/đóng; bọc `useMemo` cho object literal truyền xuống table; `memo` cho `InvoiceTable` + tách `InvoiceRow` riêng.

---

## 3. Tóm tắt thứ tự

| # | Việc | Track | Phụ thuộc | Công sức | Kết quả chính |
|---|---|---|---|---|---|
| 0 | Baseline đo | — | — | 1 ngày | Có số để so |
| 1 | Sửa invalidation (4 bug + tag `savedSearch` + bỏ refetch tay) | B | — | 1 ngày | 4→1 request/thao tác; sửa bug mã số thuế |
| 2 | Phá waterfall AdminLayout | A | — | 0,5 ngày | −400~900 ms mọi trang |
| 3 | `manualChunks` + dynamic import + ảnh | A | — | 0,5 ngày | `index.js` −50% |
| 4 | Mở rộng tag cho 6 domain nặng | B | 1 | 2–3 ngày | Hết refetch storm |
| 5 | Xoá 117 `refetchOnMountOrArgChange` | B | **4** | 1 ngày | −40~60% request/route |
| 6 | Gộp endpoint trùng + gom invalidate bulk | B | 1 | 1 ngày | −1 request/trang; bulk 50 đợt → 1 |
| 7 | Backend: bootstrap, `X-Total-Count`, bulk delete | B | — | song song | 3 round-trip → 1 |
| 8 | Rerender (POC React Compiler → 6 trang nặng) | C | 0–6 | 1 sprint | Đo lại rồi mới chốt |

**Ba việc đầu (#1–#3) tổng ~2 ngày và độc lập nhau** — làm được ngay, lấy phần lớn lợi ích thấy được.

---

## 4. Có làm server-side được không?

Ngắn gọn: **kỹ thuật thì được, nhưng repo này ở thời điểm này thì không nên**. Đây là admin sau đăng nhập — không SEO, không cần first-paint từ server cho khách vãng lai. Phần lớn lợi ích SSR hứa hẹn (bỏ waterfall, prefetch sớm) lấy được bằng #2 + #7 với chi phí ~2 ngày.

### Sẽ vỡ nếu bật SSR hôm nay

| Chỗ | Vấn đề |
|---|---|
| `src/main.tsx` | `configureStore()` gọi ở module scope ⇒ store **singleton toàn process**. SSR đa request sẽ rò dữ liệu tenant này sang tenant khác — đây là lỗi bảo mật, không chỉ lỗi kỹ thuật |
| `src/App.tsx:34` | `isNotAuthorizationPage` đọc `window.location.pathname` **ở module scope**, chạy ngay lúc import |
| `src/api.ts:117` | `refreshPromise` mutex ở module scope — trên server dùng chung mọi request |
| `src/api.ts:167` | `baseQueryWithReAuth` đọc `window.location` và gán `window.location.href` |
| `AppLoader` | `localStorage`, `document.head.appendChild`, `setCookie` |
| Auth | HttpOnly cookie + SSO redirect + token qua URL + iframe `@sapo/app-bridge` |
| Hạ tầng | S3/CDN + nginx tĩnh; SSR cần Node runtime, đổi CI/CD, healthcheck, autoscale, luồng DR |

### Ba mức

**Mức 1 — SPA + BFF (khuyến nghị, làm ngay).** `/api/bootstrap`; `Cache-Control`/`ETag` cho endpoint tra cứu tĩnh (`tax_authorities`, `provinces`, `decimal_configurations`); `<link rel="modulepreload">` sinh từ `manifest.json` Vite đã bật. ~3–4 ngày, lợi ích gần bằng SSR cho app sau login.

**Mức 2 — React Router 7 framework mode (đường tiến hoá đúng).** Kế thừa trực tiếp `react-router-dom` 6 data router đang dùng, nâng cấp incremental. Cho `route.lazy` + `loader` chạy song song ở tầng framework (đúng cái #2 cần), và **bật `ssr: true` sau này mà không đổi kiến trúc** khi đã dọn xong bảng trên. ~1–2 sprint. Khuyến nghị làm sau Track B.

**Mức 3 — Next.js / RSC.** Chỉ hợp lý cho các trang public đã tách sẵn trong `src/routes/publicRoutes.tsx` và `App.tsx:34-43` (`checkout`, `register`, `confirm/statement`, `payment-success`) — nhóm duy nhất có lợi ích thật từ SSR và gần như không dùng chung state với phần admin. Port 183k LOC còn lại là dự án nhiều tháng, không phải refactor.

---

## 5. Việc cần chốt với người khác

- **Backend**: `/api/bootstrap` · `X-Total-Count` header · bulk `DELETE`/`PUT` · `Cache-Control`/`ETag` cho dữ liệu tra cứu.
- **Leader/BA**: thứ tự 6 trang nặng ưu tiên ở C2 — nên chọn theo lưu lượng thật, không theo cảm tính.
- **Design system**: xem [[10_Projects/design-system/audit-coverage-invoice]].
