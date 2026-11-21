import { useEffect, useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import { Link, useParams } from 'react-router-dom'

import { ApiRequestError, getApiData } from '../api/client'
import type { Order } from '../types/domain'

export function QrPage() {
  const { orderId } = useParams()
  const [order, setOrder] = useState<Order | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getApiData<Order>(`/orders/${orderId}`, controller.signal)
      .then(setOrder)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            requestError instanceof ApiRequestError
              ? requestError.message
              : 'Sipariş bilgisi yüklenemedi.',
          )
        }
      })
    return () => controller.abort()
  }, [orderId])

  if (error) return <p className="notice notice-error">{error}</p>
  if (!order) return <p className="empty-state">Sipariş yükleniyor…</p>
  if (!order.qr_code) {
    return <p className="notice notice-error">Bu siparişin QR kodu gösterilemiyor.</p>
  }

  const qrValue = JSON.stringify(order.qr_code)
  return (
    <section className="narrow-page qr-page">
      <p className="eyebrow">Sipariş #{order.id}</p>
      <h1>Teslim alma QR kodun</h1>
      <p className="page-intro">
        Siparişin hazır olduğunda bu kodu dükkân görevlisine göster.
      </p>
      <div className="qr-card">
        <QRCodeSVG value={qrValue} size={224} level="M" />
        <strong>{order.shop_name}</strong>
        <span>Durum: {order.status}</span>
      </div>
      <details className="qr-details">
        <summary>İmzalı QR verisini göster</summary>
        <pre>{JSON.stringify(order.qr_code, null, 2)}</pre>
      </details>
      <Link className="button button-secondary" to="/history">Siparişlerime dön</Link>
    </section>
  )
}
