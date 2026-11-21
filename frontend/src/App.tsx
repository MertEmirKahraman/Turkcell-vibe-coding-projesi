import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from './components/AppLayout'
import { RequireAuth } from './components/RequireAuth'
import { AuthPage } from './pages/AuthPage'
import { HomePage } from './pages/HomePage'
import { OrderCreatePage } from './pages/OrderCreatePage'
import { OrderHistoryPage } from './pages/OrderHistoryPage'
import { QrPage } from './pages/QrPage'
import { ShopDetailPage } from './pages/ShopDetailPage'
import { ShopOrdersPage } from './pages/ShopOrdersPage'
import { SubscriptionPage } from './pages/SubscriptionPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<HomePage />} />
          <Route path="login" element={<AuthPage mode="login" />} />
          <Route path="register" element={<AuthPage mode="register" />} />
          <Route path="shops/:shopId" element={<ShopDetailPage />} />
          <Route
            path="orders/new/:shopId/:productId"
            element={
              <RequireAuth>
                <OrderCreatePage />
              </RequireAuth>
            }
          />
          <Route
            path="orders/:orderId/qr"
            element={
              <RequireAuth>
                <QrPage />
              </RequireAuth>
            }
          />
          <Route
            path="history"
            element={
              <RequireAuth>
                <OrderHistoryPage />
              </RequireAuth>
            }
          />
          <Route
            path="shop-orders"
            element={
              <RequireAuth>
                <ShopOrdersPage />
              </RequireAuth>
            }
          />
          <Route
            path="subscription"
            element={
              <RequireAuth>
                <SubscriptionPage />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
