# KahveCell Frontend

React 19, TypeScript and Vite application with React Router, Leaflet maps and a
small API client for the FastAPI backend.

## Run locally

From the repository root in PowerShell:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open the URL printed by Vite, normally <http://localhost:5173>. The backend API
defaults to <http://127.0.0.1:8000/api/v1>; configure another URL with
`VITE_API_BASE_URL` in `frontend/.env`.

## Pages

- `/`: Ankara shop discovery, search and map
- `/login` and `/register`: GSM OTP flow
- `/shops/:shopId`: shop details and menu
- `/orders/new/:shopId/:productId`: customize and place an order
- `/orders/:orderId/qr`: signed pickup QR
- `/history`: customer order history
- `/subscription`: plans and mock payment
- `/shop-orders`: shop-owner order queue, status updates and QR redemption
