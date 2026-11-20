import { HealthPanel } from '../features/health/HealthPanel'

export function HomePage() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <span className="brand-mark" aria-hidden="true">
          KC
        </span>
        <div>
          <p className="brand-name">KahveCell</p>
          <p className="brand-caption">Dijital kahve aboneliği</p>
        </div>
      </header>

      <section className="home-content">
        <p className="eyebrow">Proje başlangıcı · Faz 2</p>
        <h1>Uygulama altyapısı hazır.</h1>
        <p className="intro-copy">
          Backend ve frontend ayrı çalışır. Bu kontrol, aralarındaki API
          bağlantısını doğrular.
        </p>
        <HealthPanel />
      </section>
    </main>
  )
}