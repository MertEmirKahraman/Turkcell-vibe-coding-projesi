import { Link, NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'

export function AppLayout() {
  const { isAuthenticated, role, signOut } = useAuth()

  return (
    <div className="app-frame">
      <header className="site-header">
        <Link className="brand" to="/" aria-label="KahveCell ana sayfa">
          <span className="brand-icon" aria-hidden="true">K</span>
          <span>KahveCell</span>
        </Link>
        <nav className="main-nav" aria-label="Ana menü">
          <NavLink to="/">Dükkânlar</NavLink>
          <NavLink to="/subscription">Abonelik</NavLink>
          {isAuthenticated && <NavLink to="/history">Siparişlerim</NavLink>}
          {isAuthenticated && (role === 'SHOP_OWNER' || role === 'ADMIN') && (
            <NavLink to="/shop-orders">Dükkân siparişleri</NavLink>
          )}
        </nav>
        <div className="account-nav">
          {isAuthenticated ? (
            <button className="button-quiet" onClick={signOut} type="button">
              Çıkış yap
            </button>
          ) : (
            <>
              <NavLink to="/login">Giriş</NavLink>
              <Link className="button button-small" to="/register">Kayıt ol</Link>
            </>
          )}
        </div>
      </header>
      <main className="page-main">
        <Outlet />
      </main>
      <footer className="site-footer">
        <span>KahveCell</span>
        <span>Ankara’da kahve molan.</span>
      </footer>
    </div>
  )
}
