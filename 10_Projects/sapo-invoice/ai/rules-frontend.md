---
created: 2026-07-29 16:00
scope: "Rules Cursor/Claude — Frontend React TypeScript (invoice-app, sapo-invoice-admin-frontend)"
---

# Frontend Rules — React TypeScript (Sapo Invoice)

Migrate từ `ai-workspace/rules/cursor-frontend.md`. Dùng làm `.cursorrules`/`CLAUDE.md` ở root repo frontend khi cần, hoặc tham chiếu trực tiếp từ đây.

## Tech Stack

- React 18.2 + TypeScript 5.3 (strict — **KHÔNG** dùng features TypeScript 5.4+)
- Redux Toolkit 2.x + **RTK Query** (server data + state)
- React Hook Form 7.x + Yup (forms)
- `@sapo/ui-components` (UI library — **KHÔNG** tạo lại components đã có)
- `@sapo/app-bridge-react` (iframe integration với Sapo Admin)
- Vite 5.x, pnpm 9.x, Node 20.x (Volta)

## RTK Query — CRITICAL RULE: ONE api.ts FILE

```typescript
// ĐÚNG — inject vào instance duy nhất
// src/api.ts
export const api = createApi({ ... })

// src/features/invoice/invoiceEndpoints.ts (hoặc trực tiếp trong api.ts)
export const invoiceEndpoints = api.injectEndpoints({
  endpoints: (builder) => ({
    getInvoices: builder.query<InvoiceListResponse, InvoiceFilterRequest>({
      query: (params) => ({ url: '/api/invoices', params }),
      providesTags: ['Invoice'],
    }),
    createInvoice: builder.mutation<InvoiceResponse, CreateInvoiceRequest>({
      query: (body) => ({ url: '/api/invoices', method: 'POST', body }),
      invalidatesTags: ['Invoice'],
    }),
  }),
})

// SAI — KHÔNG tạo createApi() thứ hai
const anotherApi = createApi({ ... }) // ← cache invalidation BROKEN
```

## UI Components — @sapo/ui-components

- **Check `@sapo/ui-components` TRƯỚC** khi tạo component mới
- Tham chiếu: `import { Button, Table, Modal, Form } from '@sapo/ui-components'`
- **KHÔNG** tự viết lại Button, Input, Table, Modal — đã có trong library
- Admin frontend còn có `@sapo/ui-viz` cho charts (Highcharts)

## State Management

| Loại data | Tool |
|---|---|
| Server data (API) | RTK Query trong `api.ts` |
| Cross-page global | Redux slice (`state/`) |
| UI-only (modal, toggle) | `useState` |

- KHÔNG dùng Redux thủ công cho API calls (RTK Query đảm nhận)
- KHÔNG prop drilling quá 2 levels

## Forms — useCustomForm Pattern

```typescript
// Dùng useCustomForm (KHÔNG dùng useForm trực tiếp)
const form = useCustomForm<CreateInvoiceFormData>({
  schema: createInvoiceSchema, // Yup schema
})

// Modal forms — reset sau submit
const form = useCustomForm<FormData>({
  schema,
  makeCleanAfterSubmit: true, // reset form sau submit thành công
})

// Multi-step forms: dùng ModalView union type
type ModalView =
  | { step: 'form' }
  | { step: 'confirm'; data: FormData }
  | { step: 'result'; invoiceId: number }
```

## Error Handling

```typescript
// Form validation errors từ API
transformErrors(error, form.setError)

// Toast notification (chọn một trong hai)
handleErrorApi(error)     // version 1
handleErrorApiV2(error)   // version 2 (ưu tiên dùng)

// Unexpected errors → Sentry
Sentry.captureException(error)

// KHÔNG swallow errors trong catch blocks
```

## TypeScript

- **`NO any`** — define interfaces cho mọi prop và API response
- `import type { Xxx }` cho type-only imports (không phải runtime)
- TypeScript 5.3 only — KHÔNG dùng features từ 5.4+
- `interface` cho objects; `type` cho unions/primitives
- `console.log` được phép (no-console off)

## Component Rules

- Functional components only — PascalCase files (`InvoiceListPage.tsx`)
- Hooks: camelCase với use prefix (`useInvoiceData.ts`)
- **Size limit: dưới 200 lines** → extract sang hook hoặc sub-component
- `React.FC<Props>` với explicit Props interface
- Event handlers: `handleXxx` naming (`handleSubmit`, `handleRowClick`)
- **KHÔNG** anonymous functions trong JSX event handlers

```typescript
// ĐÚNG
const handleSubmit = useCallback(() => { ... }, [])
<Button onClick={handleSubmit}>Submit</Button>

// SAI
<Button onClick={() => { ... }}>Submit</Button>
```

## File Structure (invoice-app frontend)

```
frontend/src/
├── api.ts           ← RTK Query (ONE file — KHÔNG split thành nhiều createApi)
├── routes.tsx       ← Routes (React.lazy cho lazy loading)
├── store/           ← Redux store setup
├── state/           ← Redux slices (cross-page global state only)
├── pages/           ← Page components (lazy-loaded qua routes.tsx)
│   └── iframe/      ← Sapo Admin iframe embedding
├── components/      ← Reusable UI components
├── types/           ← TypeScript definitions
├── hooks/           ← Custom hooks
└── utils/           ← format, datetime, toast, form utils
```

## File Structure (sapo-invoice-admin-frontend)

```
src/
├── routes/          ← Route definitions
├── pages/           ← Page components
├── components/      ← Reusable components (DashboardChart, Sheet2*, ErrorBoundary)
├── types/           ← TypeScript + e-document types
├── store/           ← Redux store
├── state/           ← Redux slices
├── hooks/           ← Custom hooks
├── contexts/        ← React contexts
└── utils/           ← Utilities
```

Admin frontend còn dùng thêm:
- `@preact/signals-react` cho reactive state
- `@dnd-kit/core` + `react-dnd` cho drag & drop
- `@sentry/react` cho error monitoring

## Performance

- Routes: lazy load với `React.lazy()` + `Suspense`
- `useMemo` cho expensive computations
- `useCallback` cho callbacks pass như props
- `React.memo` cho list items
- KHÔNG anonymous functions trong JSX (causes re-render)

## Linting & Build

- Lint: `pnpm lint` (ESLint với `@sapo/eslint-plugin`)
- Build: `pnpm build` (type-checked qua `tsc`)
- Dev: `pnpm dev`
- KHÔNG skip TypeScript errors — fix trước khi commit

## BLOCKING — Đọc trước khi sửa (admin-frontend)

Trước khi edit bất kỳ `.ts/.tsx` file trong `sapo-invoice-admin-frontend`:
**Đọc `.claude/commands/review-code.md`** (trong repo đó) — chứa project-specific conventions:
- New page → follow section 1 (api.ts, routes.tsx, types.ts)
- New endpoint → section 3 (injectEndpoints, tagTypes, transformAxiosErrorResponse)
- New form → section 5 (useCustomForm + Control.* + yup factory)
- Modal forms → makeCleanAfterSubmit; multi-step → ModalView union

---

_Nguồn: `ai-workspace/rules/cursor-frontend.md`. Cập nhật rule mới ở đây (developer-os) trước — `ai-workspace` không còn là nguồn chính cho phần rules._
