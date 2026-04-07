# Frontend (Next.js)

UI for DisasterGuard disaster assessment workflows:

- upload pre/post satellite imagery
- run backend damage inference
- visualize results on map + hotspot view
- inspect analytics and generated reports

## Development

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`.

Assessment data is session-only by default (no persistence).  
To opt in to persistence:

```bash
NEXT_PUBLIC_PERSIST_ASSESSMENTS=true npm run dev
```

Upload/load guard defaults:
- `NEXT_PUBLIC_MAX_UPLOAD_FILES=40`
- `NEXT_PUBLIC_MAX_FILE_SIZE_MB=25`
- `NEXT_PUBLIC_MAX_TOTAL_UPLOAD_MB=300`
- `NEXT_PUBLIC_MAX_ACTIVE_ANALYSES=2`

## Backend integration

`next.config.ts` rewrites API calls to backend:

- `/api/health` -> `http://localhost:8000/health`
- `/api/*` -> `http://localhost:8000/api/*`

So backend should run on port `8000`.

## Quality checks

```bash
npm run lint --silent
npm run build
```

## Main app surfaces

- `src/app/upload/page.tsx` — imagery upload + inference trigger
- `src/app/analysis/page.tsx` — result details + map
- `src/app/hotspots/page.tsx` — hotspot heatmap
- `src/app/analytics/page.tsx` — aggregate charts
- `src/app/reports/page.tsx` — report list/details
- `src/context/AssessmentContext.tsx` — assessment state + persistence
