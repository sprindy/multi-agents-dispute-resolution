# Travel History UI

A React + Tailwind CSS recreation of a ride-hailing "Activity" screen. Each trip card displays the route, date, price and three action buttons: **Rate & tip**, **Rebook** and **Advocate**.

## Features

- Mobile-first, responsive layout (centered phone frame on desktop)
- Clean trip list with status-aware styling (e.g. cancelled trips)
- Bottom tab bar matching the screenshot
- Interactive action buttons with toast feedback

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown in your terminal (usually http://localhost:5173).

## Build

```bash
npm run build
```

Static files are output to `dist/` and can be served by any static host.
