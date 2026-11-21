import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ApiRequestError, getApiData } from '../api/client'
import type { ShopDetail } from '../types/domain'

const price = new Intl.NumberFormat('tr-TR', {
  style: 'currency',
  currency: 'TRY',
})

export function ShopDetailPage() {
  const { shopId } = useParams()
  const [shop, setShop] = useState<ShopDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getApiData<ShopDetail>(`/shops/${shopId}`, controller.signal)
      .then(setShop)
      .catch((requestError: unknown) => {
        if (controller.signal.aborted) return
        setError(
          requestError instanceof ApiRequestError
            ? requestError.message
            : 'Dükkân bilgisi yüklenemedi.',
        )
      })
    return () => controller.abort()
  }, [shopId])

  if (error) return <p className="notice notice-error">{error}</p>
  if (!shop) return <p className="empty-state">Dükkân yükleniyor…</p>

  return (
    <section className="content-page">
      <Link className="back-link" to="/">← Dükkânlara dön</Link>
      <p className="eyebrow">{shop.address}</p>
      <h1>{shop.name}</h1>
      <p className="page-intro">Menüden bir kahve seçerek siparişini oluştur.</p>

      <div className="product-list">
        {shop.menu.map((product) => (
          <article className="product-card" key={product.id}>
            <div>
              <h2>{product.name}</h2>
              <p>{product.description}</p>
            </div>
            <div className="product-action">
              <strong>{price.format(product.price)}</strong>
              <Link
                className="button button-small"
                to={`/orders/new/${shop.id}/${product.id}`}
              >
                Seç
              </Link>
            </div>
          </article>
        ))}
        {shop.menu.length === 0 && (
          <p className="empty-state">Bu dükkânın menüsü henüz boş.</p>
        )}
      </div>
    </section>
  )
}
