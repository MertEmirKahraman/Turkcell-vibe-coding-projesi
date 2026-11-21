import { useEffect, useState, type FormEvent } from 'react'

import { ApiRequestError, getApiData, patchApiData, postApiData } from '../api/client'
import { QrScanner } from '../components/QrScanner'
import type { Order } from '../types/domain'

const nextStatus: Record<string, string> = {
  PENDING: 'ACCEPTED',
  ACCEPTED: 'PREPARING',
  PREPARING: 'READY',
}

const statusNames: Record<string, string> = {
  PENDING: 'Onay bekliyor',
  ACCEPTED: 'Kabul edildi',
  PREPARING: 'Hazırlanıyor',
  READY: 'Teslime hazır',
  DELIVERED: 'Teslim edildi',
}

function showError(error: unknown) {
  return error instanceof ApiRequestError
    ? error.message
    : 'İşlem tamamlanamadı. Backend bağlantısını kontrol edin.'
}

export function ShopOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [busyOrderId, setBusyOrderId] = useState<number | null>(null)
  const [qrText, setQrText] = useState<Record<number, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    getApiData<Order[]>('/orders/shop', controller.signal)
      .then(setOrders)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) setError(showError(requestError))
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [refreshKey])

  async function advanceOrder(order: Order, status: string) {
    setBusyOrderId(order.id)
    setError(null)
    setMessage(null)
    try {
      const updated = await patchApiData<Order>(`/orders/${order.id}/status`, { status })
      setOrders((current) => current.map((item) => item.id === updated.id ? updated : item))
    } catch (requestError) {
      setError(showError(requestError))
    } finally {
      setBusyOrderId(null)
    }
  }

  async function redeemOrder(event: FormEvent<HTMLFormElement>, order: Order) {
    event.preventDefault()
    setBusyOrderId(order.id)
    setError(null)
    setMessage(null)
    let payload: unknown
    try {
      payload = JSON.parse(qrText[order.id] ?? '')
    } catch {
      setError('QR içeriği okunamadı. Kodu tekrar tarayın veya JSON’u yapıştırın.')
      setBusyOrderId(null)
      return
    }

    try {
      const updated = await postApiData<Order>(`/orders/${order.id}/redeem`, payload)
      setOrders((current) => current.map((item) => item.id === updated.id ? updated : item))
      setQrText((current) => ({ ...current, [order.id]: '' }))
      setMessage(`Sipariş #${order.id} QR imzası doğrulandı ve teslim edildi.`)
    } catch (requestError) {
      setError(showError(requestError))
    } finally {
      setBusyOrderId(null)
    }
  }

  return (
    <section className="content-page">
      <div className="section-title">
        <div>
          <p className="eyebrow">Dükkân yönetimi</p>
          <h1>Gelen siparişler</h1>
        </div>
        <button
          className="button button-secondary"
          onClick={() => {
            setLoading(true)
            setError(null)
            setRefreshKey((key) => key + 1)
          }}
          type="button"
        >
          Yenile
        </button>
      </div>

      {error && <p className="notice notice-error">{error}</p>}
      {message && <p className="notice notice-success">{message}</p>}
      {loading && <p className="empty-state">Siparişler yükleniyor…</p>}
      {!loading && !error && orders.length === 0 && (
        <p className="empty-state">Dükkânlarına henüz sipariş gelmedi.</p>
      )}

      <div className="order-list">
        {orders.map((order) => {
          const next = nextStatus[order.status]
          return (
            <article className="shop-order-card" key={order.id}>
              <div className="shop-order-heading">
                <div>
                  <p className="order-meta">{order.shop_name} · Sipariş #{order.id}</p>
                  <strong>{order.items.map((item) => item.product_name).join(', ')}</strong>
                  <p className="muted">
                    {order.items.map((item) => {
                      const options = item.customization
                      return `${options.size} · Şeker ${options.sugar_level} · ${options.milk_preference} süt · ${options.extra_shots} ek shot`
                    }).join(' / ')}
                  </p>
                </div>
                <span className="status-pill">{statusNames[order.status] ?? order.status}</span>
              </div>

              {next && (
                <button
                  className="button button-small"
                  disabled={busyOrderId === order.id}
                  onClick={() => advanceOrder(order, next)}
                  type="button"
                >
                  {busyOrderId === order.id ? 'Güncelleniyor…' : `${statusNames[next]} olarak işaretle`}
                </button>
              )}

              {order.status === 'READY' && (
                <form className="redeem-form" onSubmit={(event) => redeemOrder(event, order)}>
                  <p className="muted">
                    Müşterinin QR kodunu tara ya da imzalı JSON içeriğini yapıştır.
                  </p>
                  <QrScanner
                    onScan={(value) => {
                      setQrText((current) => ({ ...current, [order.id]: value }))
                      setError(null)
                    }}
                  />
                  <label className="field">
                    QR içeriği
                    <textarea
                      onChange={(event) =>
                        setQrText((current) => ({
                          ...current,
                          [order.id]: event.target.value,
                        }))
                      }
                      placeholder='{"order_id":"…","signature":"…"}'
                      rows={5}
                      value={qrText[order.id] ?? ''}
                    />
                  </label>
                  <button
                    className="button"
                    disabled={busyOrderId === order.id || !qrText[order.id]?.trim()}
                    type="submit"
                  >
                    {busyOrderId === order.id ? 'Doğrulanıyor…' : 'QR’ı doğrula ve teslim et'}
                  </button>
                </form>
              )}
            </article>
          )
        })}
      </div>
    </section>
  )
}
