import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ApiRequestError, getApiData, postApiData } from '../api/client'
import type { Order, ShopDetail } from '../types/domain'

export function OrderCreatePage() {
  const { shopId, productId } = useParams()
  const navigate = useNavigate()
  const [shop, setShop] = useState<ShopDetail | null>(null)
  const [size, setSize] = useState('M')
  const [sugarLevel, setSugarLevel] = useState('0')
  const [milk, setMilk] = useState('WHOLE')
  const [extraShots, setExtraShots] = useState('0')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    getApiData<ShopDetail>(`/shops/${shopId}`, controller.signal)
      .then(setShop)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            requestError instanceof ApiRequestError
              ? requestError.message
              : 'Dükkân yüklenemedi.',
          )
        }
      })
    return () => controller.abort()
  }, [shopId])

  const product = shop?.menu.find((item) => item.id === Number(productId))

  async function submitOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const order = await postApiData<Order>('/orders', {
        shop_id: Number(shopId),
        product_id: Number(productId),
        size,
        sugar_level: Number(sugarLevel),
        milk_preference: milk,
        extra_shots: Number(extraShots),
      })
      navigate(`/orders/${order.id}/qr`)
    } catch (requestError) {
      setError(
        requestError instanceof ApiRequestError
          ? requestError.message
          : 'Sipariş oluşturulamadı.',
      )
    } finally {
      setBusy(false)
    }
  }

  if (!shop && !error) return <p className="empty-state">Dükkân yükleniyor…</p>
  if (!product) {
    return (
      <section className="content-page">
        <p className="notice notice-error">{error ?? 'Ürün bulunamadı.'}</p>
        <Link className="back-link" to={`/shops/${shopId}`}>Menüye dön</Link>
      </section>
    )
  }

  return (
    <section className="narrow-page">
      <Link className="back-link" to={`/shops/${shopId}`}>← Menüye dön</Link>
      <p className="eyebrow">{shop?.name}</p>
      <h1>{product.name}</h1>
      <p className="page-intro">Kahveni dilediğin gibi özelleştir.</p>
      <form className="form-card" onSubmit={submitOrder}>
        <label className="field">
          Boyut
          <select onChange={(event) => setSize(event.target.value)} value={size}>
            <option value="S">Small</option>
            <option value="M">Medium</option>
            <option value="L">Large</option>
          </select>
        </label>
        <label className="field">
          Şeker
          <select
            onChange={(event) => setSugarLevel(event.target.value)}
            value={sugarLevel}
          >
            {[0, 1, 2, 3, 4, 5].map((level) => (
              <option key={level} value={level}>{level}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Süt tercihi
          <select onChange={(event) => setMilk(event.target.value)} value={milk}>
            <option value="WHOLE">Tam yağlı</option>
            <option value="OAT">Yulaf</option>
            <option value="LACTOSE_FREE">Laktozsuz</option>
            <option value="NONE">Sütsüz</option>
          </select>
        </label>
        <label className="field">
          Ek shot
          <select
            onChange={(event) => setExtraShots(event.target.value)}
            value={extraShots}
          >
            {[0, 1, 2, 3].map((count) => (
              <option key={count} value={count}>{count}</option>
            ))}
          </select>
        </label>
        {error && <p className="notice notice-error">{error}</p>}
        <button className="button" disabled={busy} type="submit">
          {busy ? 'Sipariş veriliyor…' : 'Abonelik hakkımla sipariş ver'}
        </button>
      </form>
    </section>
  )
}
