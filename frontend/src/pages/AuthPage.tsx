import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ApiRequestError, postApiData } from '../api/client'
import { useAuth } from '../auth/useAuth'
import type { AuthResult } from '../types/domain'

interface AuthPageProps {
  mode: 'login' | 'register'
}

interface OtpSentResponse {
  message: string
  otp_simulation: string
}

export function AuthPage({ mode }: AuthPageProps) {
  const [phone, setPhone] = useState('')
  const [fullName, setFullName] = useState('')
  const [otp, setOtp] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [simulatedOtp, setSimulatedOtp] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const isRegister = mode === 'register'

  async function sendOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const path = isRegister ? '/auth/register' : '/auth/login'
      const body = isRegister
        ? { phone_number: phone, full_name: fullName }
        : { phone_number: phone }
      const response = await postApiData<OtpSentResponse>(path, body)
      setSimulatedOtp(response.otp_simulation)
      setOtpSent(true)
    } catch (requestError) {
      setError(
        requestError instanceof ApiRequestError
          ? requestError.message
          : 'İstek gönderilemedi. Backend bağlantısını kontrol edin.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function verifyOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const result = await postApiData<AuthResult>('/auth/verify-otp', {
        phone_number: phone,
        otp_code: otp,
      })
      signIn(result.access_token, result.refresh_token, result.user.role)
      navigate('/')
    } catch (requestError) {
      setError(
        requestError instanceof ApiRequestError
          ? requestError.message
          : 'Kod doğrulanamadı.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="narrow-page">
      <p className="eyebrow">{isRegister ? 'Yeni hesap' : 'Tekrar hoş geldin'}</p>
      <h1>{isRegister ? 'Kayıt ol' : 'Giriş yap'}</h1>
      <p className="page-intro">
        GSM numaranı gir; doğrulama kodu SMS simülasyonu olarak gösterilecek.
      </p>

      {!otpSent ? (
        <form className="form-card" onSubmit={sendOtp}>
          {isRegister && (
            <label className="field">
              Ad soyad
              <input
                autoComplete="name"
                maxLength={100}
                onChange={(event) => setFullName(event.target.value)}
                required
                value={fullName}
              />
            </label>
          )}
          <label className="field">
            GSM numarası
            <input
              autoComplete="tel"
              inputMode="tel"
              onChange={(event) => setPhone(event.target.value)}
              placeholder="05551234567"
              required
              value={phone}
            />
          </label>
          {error && <p className="notice notice-error">{error}</p>}
          <button className="button" disabled={busy} type="submit">
            {busy ? 'Gönderiliyor…' : 'Doğrulama kodu gönder'}
          </button>
        </form>
      ) : (
        <form className="form-card" onSubmit={verifyOtp}>
          <p className="notice notice-info">
            Simülasyon kodu: <strong>{simulatedOtp}</strong>
          </p>
          <label className="field">
            SMS doğrulama kodu
            <input
              autoComplete="one-time-code"
              inputMode="numeric"
              maxLength={4}
              onChange={(event) => setOtp(event.target.value)}
              pattern="[0-9]{4}"
              required
              value={otp}
            />
          </label>
          {error && <p className="notice notice-error">{error}</p>}
          <button className="button" disabled={busy} type="submit">
            {busy ? 'Doğrulanıyor…' : 'Doğrula ve devam et'}
          </button>
          <button
            className="text-button"
            onClick={() => setOtpSent(false)}
            type="button"
          >
            GSM numarasını değiştir
          </button>
        </form>
      )}

      <p className="switch-auth">
        {isRegister ? 'Zaten hesabın var mı?' : 'Henüz hesabın yok mu?'}{' '}
        <Link to={isRegister ? '/login' : '/register'}>
          {isRegister ? 'Giriş yap' : 'Kayıt ol'}
        </Link>
      </p>
    </section>
  )
}
