import { useEffect, useState, type FormEvent } from 'react'
import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet'
import { Link } from 'react-router-dom'

import { ApiRequestError, getApiData } from '../api/client'
import { HealthPanel } from '../features/health/HealthPanel'
import type { Shop } from '../types/domain'

const ankaraCenter: [number, number] = [39.91987, 32.853241]

export function HomePage() {
  const [shops, setShops] = useState<Shop[]>([])
  const [searchText, setSearchText] = useState('')
  const [search, setSearch] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const controller = new AbortController()
    const params = new URLSearchParams({
      latitude: String(ankaraCenter[0]),
      longitude: String(ankaraCenter[1]),
    })
    if (search) params.set('search', search)

    getApiData<Shop[]>(`/shops?${params}`, controller.signal)
      .then((result) => {
        setShops(result)
        setError(null)
        setLoading(false)
      })
      .catch((requestError: unknown) => {
        if (controller.signal.aborted) return
        setError(
          requestError instanceof ApiRequestError
            ? requestError.message
            : 'Dükkânlar yüklenemedi.',
        )
        setLoading(false)
      })
    return () => controller.abort()
  }, [search, refreshKey])

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    const nextSearch = searchText.trim()
    if (nextSearch === search) {
      setRefreshKey((key) => key + 1)
    } else {
      setSearch(nextSearch)
    }
  }

  return (
    <div className="home-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Ankara</p>
          <h1>Yakınında bir kahve molası.</h1>
          <p className="page-intro">Dükkânları keşfet, menülere göz at ve sipariş ver.</p>
        </div>
        <HealthPanel />
      </div>

      <form className="search-bar" onSubmit={submitSearch}>
        <label className="visually-hidden" htmlFor="shop-search">
          Dükkân veya adres ara
        </label>
        <input
          id="shop-search"
          onChange={(event) => setSearchText(event.target.value)}
          placeholder="Dükkân veya semt ara"
          value={searchText}
        />
        <button className="button" type="submit">Ara</button>
      </form>

      {error && <p className="notice notice-error">{error}</p>}
      {loading && <p className="empty-state">Dükkânlar yükleniyor…</p>}
      {!loading && !error && shops.length === 0 && (
        <p className="empty-state">Aramana uygun dükkân bulunamadı.</p>
      )}

      {!loading && shops.length > 0 && (
        <div className="discovery-grid">
          <section className="shop-list" aria-label="Dükkân listesi">
            <div className="section-title">
              <h2>Dükkânlar</h2>
              <span>{shops.length} sonuç</span>
            </div>
            {shops.map((shop) => (
              <Link className="shop-card" key={shop.id} to={`/shops/${shop.id}`}>
                <span className="shop-card-icon" aria-hidden="true">☕</span>
                <span className="shop-card-copy">
                  <strong>{shop.name}</strong>
                  <span>{shop.address}</span>
                  <small>
                    {shop.distance_km != null
                      ? `${shop.distance_km.toFixed(1)} km uzakta`
                      : `${shop.product_count ?? 0} ürün`}
                  </small>
                </span>
                <span className="card-arrow" aria-hidden="true">→</span>
              </Link>
            ))}
          </section>

          <section className="map-panel" aria-label="Dükkân haritası">
            <MapContainer center={ankaraCenter} zoom={11} scrollWheelZoom>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {shops.map((shop) => (
                shop.latitude !== null && shop.longitude !== null && (
                  <CircleMarker
                    center={[shop.latitude, shop.longitude]}
                    key={shop.id}
                    pathOptions={{ color: '#ddb450', fillColor: '#1d4f9d', fillOpacity: 0.95 }}
                    radius={8}
                  >
                    <Popup>
                      <strong>{shop.name}</strong>
                      <br />
                      <Link to={`/shops/${shop.id}`}>Dükkânı gör</Link>
                    </Popup>
                  </CircleMarker>
                )
              ))}
            </MapContainer>
          </section>
        </div>
      )}
    </div>
  )
}