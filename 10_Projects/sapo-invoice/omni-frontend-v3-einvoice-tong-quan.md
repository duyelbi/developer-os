---
created: 2026-08-11 08:30
status: Implemented
project: "[[10_Projects/sapo-invoice/README]]"
---

# `sapo-frontend-v3` — tổng quan + phần hóa đơn điện tử

SPA admin của **Sapo Omni** (không phải app riêng của hóa đơn). Toàn bộ nghiệp vụ bán hàng nằm ở đây: sản phẩm, đơn hàng, khách hàng, kho, khuyến mãi, CRM, tài chính… Phần liên quan dự án hóa đơn chỉ là **2 page**: `EInvoice` và `InvoiceQR`.

- Path: `/Users/sapo/invoice/sapo-frontend-v3/`
- Remote: `git.dktsoft.com:2008/sapo-presentation/sapo-frontend-v3.git`
- Branch mặc định `master`; branch chạy CI: `master`, `staging`, `dev2`, `optimize-ci`
- Branch convention: `dev-money/feature/...`, `dev-money/hotfix/...`, `dev-express/hotfix/...`

## Stack — lưu ý là stack cũ

| Thành phần | Giá trị |
|---|---|
| Node | **14.17.0**, ghim bằng Volta (`package.json` → `volta`) |
| React | **16.12** (không phải 18) |
| Bundler | Webpack 5 (không phải Vite như `sapo-invoice-admin-frontend`) |
| UI | Material-UI **4.9** + styled-components + `@sapo-presentation/sapo-ui-components` |
| State | Redux Toolkit + RTK Query, Redux Persist (chỉ persist slice `theme`), có cả Zustand |
| Form | React Hook Form + Yup (mới), Formik (code cũ) |
| Router | React Router DOM 5, mọi page `React.lazy()` |
| i18n | i18next, 30+ namespace, `public/locales/{hash}/{lang}/…`, vi (fallback) + th |
| Test | **Không có test framework** |

Khác hẳn stack của [[10_Projects/sapo-invoice/refactor-frontend-performance|sapo-invoice-admin-frontend]] (React mới + Vite + pnpm) — đừng bê thẳng pattern giữa hai repo.

## Lệnh

```bash
npm start              # dev, port 4200 — cần map host 127.0.0.1 core2-dev2.mysapogo.com
npm run start-staging  # dev trỏ backend staging
npm run build:dev2 | build:staging | build:master
npm run type-check     # tsc --noEmit
npm run lint:fix
```

Không có `.env.example` — copy từ `.env.local` / `.env.dev2` / `.env.staging` / `.env.production` có sẵn trong repo.

## Cách frontend nối tới backend

Base URL **không lấy từ env** mà dựng từ chính URL đang mở:

```ts
// src/services/config.ts
`${window.location.protocol}//${window.location.hostname}:${window.location.port}/admin`
```

Header cố định `X-Sapo-Client` / `X-Sapo-ServiceId` = `sapo-frontend-v3`. Timeout 30s (API analytics 120s). Array param serialize bằng `qs` với `arrayFormat: "comma"` → `?ids=1,2,3`.

Dev server proxy (`webpack/proxy.js`) trỏ theo IP nội bộ, chia 3 target:

| Pattern | Target |
|---|---|
| `**.json`, `/admin/notifications/ws` | `SAPO_API` (dev `192.168.12.72:8765`, staging `10.10.1.202:9765`, prod `10.10.2.87:8765`) |
| `/admin/pos_v2/**` | `SAPO_POS_V2` (:8189) |
| `/v2/**`, `/admin/orders/returns/**`, auth/oauth/session | `SAPO_FE_X` (:8185) |

→ Mọi call hóa đơn đi qua `**.json` vào `SAPO_API`, gateway route tới `sapo-einvoice-service`.

## Page `EInvoice` (`src/page/EInvoice/`)

Route `/admin/einvoices`, lazy load, bọc `AuthGuardRoute`.

```text
einvoice.module.tsx
list/        EInvoices.tsx — danh sách + filter
edit/        FormEinvoice.tsx, ValidateFormEinvoice.ts, MapMEinvoiceModelToSave.ts, store.ts
publish/     EInvoicePublish.tsx
components/  EInvoiceBulkPublish, EInvoiceQuickFilter, EInvoiceOtherFilter,
             EInvoiceImport, EInvoiceExport, Mail,
             DialogDeleteEInvoices, DialogBulkDeleteEInvoices,
             DialogAutoInvoiceResults, DialogEInvoiceDecreeNotice, WarningBanner
```

`DialogAutoInvoiceResults` là UI của [[10_Projects/sapo-invoice/epic-65-auto-invoice-order-name|Epic #65]].

## API surface — `src/services/EinvoiceService/EInvoiceService.ts`

Toàn bộ endpoint hóa đơn gom trong 1 file (~470 dòng), đuôi `.json`:

| Nhóm | Endpoint tiêu biểu |
|---|---|
| CRUD | `GET /einvoices/{id}.json`, `GET /einvoices/order/{order_id}.json`, `POST /einvoices/create_draft.json?order_id=`, `PUT /einvoices/{id}.json`, `DELETE /einvoices/{id}.json` |
| Phát hành | `POST /einvoices/{id}/publish_draft.json`, `/publish_signed.json`, `POST /einvoices/bulk_publish.json`, `/bulk_signed.json`, `GET /einvoices/jobs/{id}.json`, `/publishing_jobs/latest.json` |
| Import/Export | `POST /einvoices/import.json`, `/import/product_mapping.json`, `GET /einvoices/export.json`, `/product_mappings.json` |
| Auto invoice | `GET|PUT /einvoices/auto_invoice/configs.json`, `GET|PUT /invoice_providers/sapo_invoice/accounts/{id}/auto_config.json` |
| Provider chung | `GET /einvoices/publish_providers.json`, `/invoice_providers/templates.json`, `/invoice_providers/custom_fields.json` |
| SapoInvoice (SI) | `/invoice_providers/sapo_invoice/{accounts,tenants,certificates,invoice_balance,user,t2b,customers,settings}.json` |
| MeInvoice | `/invoice_providers/meinvoice/{templates,account,clients}.json` |
| SInvoice | `/invoice_providers/sinvoice/accounts.json`, `/{id}/preview.json`, `/create_exchange_invoice_file.json` |
| VnInvoice | `/invoice_providers/vninvoice/{account,login,print/{id}}.json` |

Base path service khớp `controller/` bên [[10_Projects/sapo-invoice/omni-einvoice-service-tong-quan|sapo-einvoice-service]] 1-1.

## Luồng QR — chạy xuyên 2 repo, **không cần đăng nhập**

Người mua quét QR trên hóa đơn/phiếu → mở trang công khai để tự nhập thông tin xuất hóa đơn.

- FE route công khai: `/sapo_invoice/qr/:token` và `/invoice_qr/:id` — khai trong `PUBLIC_ROUTES` (`src/app.routing.tsx:51`), `App.tsx` render ngoài `AuthGuardRoute`
- FE service: `src/services/InvoiceQRService/InvoiceQRService.ts`
  - `GET /einvoices/sapo_invoice/qr/{token}.json`
  - `POST /einvoices/sapo_invoice/qr/{token}/submit.json`
  - `GET https://invoice.sapo.vn/api/tax_to_business` (gọi thẳng SI, tra MST → tên doanh nghiệp)
- BE: `controller/qr/PublicQrInvoiceController.java`, `@RequestMapping("/einvoices/sapo_invoice/qr")` + `PublicQrExceptionHandler`
- Spec: `sapo-einvoice-service/docs/features/scan-qr-enter-invoice-info/` (prd, srs, api, messages, task-list)

Đây là bề mặt **public** duy nhất của hóa đơn — sửa gì ở đây phải cân nhắc bảo mật (token, rate limit, lộ thông tin hóa đơn).

## Build & deploy

Webpack 5 + `dotenv-webpack` (env prefix `REACT_APP_`), minify bằng esbuild (target es2015), `ForkTsCheckerWebpackPlugin` **chỉ chạy khi build prod**, không chạy ở dev → lỗi type có thể lọt tới lúc build CI. Output `build/www/`.

CI GitLab: `lint` (`npm run lint:quiet`) → `build` (`npm run build:$CI_COMMIT_REF_SLUG`, Node 14 alpine, `npm ci`) → `cdn` (đẩy static lên S3, **trừ `index.html`**) → `package` (Docker nginx:1.17-alpine, SPA fallback) → `deploy`.

→ Tên branch **phải** khớp tên script build (`build:master`/`build:staging`/`build:dev2`), đặt tên branch khác là job build fail.

## Tích hợp khác trong repo

Sentry, Mixpanel (9 key V1–V9), Customer.io; sàn Shopee/Lazada/Tiki/Sendo/Bizweb/WooCommerce; vận chuyển SapoExpress/AHA Move/Ninja Van/TikiNow/VNPOST; thanh toán OnePay + Sapo Payment; notification qua STOMP over WebSocket.

## Liên kết

- Service tương ứng: [[10_Projects/sapo-invoice/omni-einvoice-service-tong-quan]]
- Điều tra sự cố prod: [[10_Projects/sapo-invoice/omni-einvoice-dieu-tra-su-co-prod]]
