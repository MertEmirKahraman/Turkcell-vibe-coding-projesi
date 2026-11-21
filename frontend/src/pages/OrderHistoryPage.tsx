import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiRequestError, getApiData } from '../api/client'
import type { Order } from '../types/domain'

export function OrderHistoryPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getApiData<Order[]>('/orders/history', controller.signal)
      .then(setOrders)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            requestError instanceof ApiRequestError
              ? requestError.message
              : 'Sipariş geçmişi yüklenemedi.',
          )
        }
      })
    return () => controller.abort()
  }, [])

  return (
    <section className="content-page">
      <p className="eyebrow">Hesabım</p>
      <h1>Sipariş geçmişim</h1>
      {error && <p className="notice notice-error">{error}</p>}
      {!error && orders.length === 0 && (
        <p className="empty-state">Henüz siparişin yok.</p>
      )}
      <div className="order-list">
        {orders.map((order) => (
          <article className="order-card" key={order.id}>
            <div>
              <p className="order-meta">Sipariş #{order.id} · {order.shop_name}</p>
              <strong>{order.items.map((item) => item.product_name).join(', ')}</strong>
              <p className="muted">{new Date(order.created_at).toLocaleString('tr-TR')}</p>
            </div>
            <div className="order-actions">
              <span className="status-pill">{order.status}</span>
              {order.qr_code && (
                <Link className="text-link" to={`/orders/${order.id}/qr`}>QR kodu</Link>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
