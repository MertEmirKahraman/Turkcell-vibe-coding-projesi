import { useEffect, useState, type FormEvent } from 'react'

import {
  ApiRequestError,
  getApiData,
  patchApiData,
  postApiData,
} from '../api/client'
import type { ActiveSubscription, SubscriptionPlan } from '../types/domain'

interface PaymentResult {
  status: 'SUCCEEDED' | 'FAILED'
  transaction_id: string
  subscription_plan: string
  amount: number
}

const price = new Intl.NumberFormat('tr-TR', {
  style: 'currency',
  currency: 'TRY',
})

export function SubscriptionPage() {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([])
  const [active, setActive] = useState<ActiveSubscription | null>(null)
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan['plan_type']>('STARTER')
  const [cardNumber, setCardNumber] = useState('4242-4242-4242-4242')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([
      getApiData<SubscriptionPlan[]>('/subscriptions/plans', controller.signal),
      getApiData<ActiveSubscription>('/subscriptions/me', controller.signal),
    ])
      .then(([availablePlans, subscription]) => {
        setPlans(availablePlans)
        setActive(subscription)
        if (subscription.subscription) {
          setSelectedPlan(subscription.subscription.plan_type)
        }
      })
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            requestError instanceof ApiRequestError
              ? requestError.message
              : 'Abonelik bilgileri yüklenemedi.',
          )
        }
      })
    return () => controller.abort()
  }, [])

  async function purchase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      const body = {
        subscription_plan: selectedPlan,
        card_number: cardNumber,
      }
      const payment = active?.active
        ? (
            await patchApiData<{ payment: PaymentResult }>(
              '/subscriptions/me',
              body,
            )
          ).payment
        : await postApiData<PaymentResult>('/payments/process', body)
      if (payment.status === 'SUCCEEDED') {
        setMessage(`${payment.subscription_plan} aboneliğin aktif. İşlem: ${payment.transaction_id}`)
        const subscription = await getApiData<ActiveSubscription>('/subscriptions/me')
        setActive(subscription)
      } else {
        setError('Ödeme başarısız oldu. Test kartını kontrol edip tekrar deneyin.')
      }
    } catch (requestError) {
      setError(
        requestError instanceof ApiRequestError
          ? requestError.message
          : 'Ödeme tamamlanamadı.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="content-page">
      <p className="eyebrow">Üyelik</p>
      <h1>Kahve aboneliğin</h1>
      {active?.active && active.subscription && (
        <p className="notice notice-info">
          Aktif paket: <strong>{active.subscription.plan_name}</strong>
          {' · '}Kalan hak: {active.subscription.remaining_credits ?? 'Sınırsız'}
        </p>
      )}
      {message && <p className="notice notice-success">{message}</p>}
      {error && <p className="notice notice-error">{error}</p>}

      <div className="plan-grid">
        {plans.map((plan) => (
          <button
            aria-pressed={selectedPlan === plan.plan_type}
            className={`plan-card${selectedPlan === plan.plan_type ? ' plan-card-selected' : ''}`}
            key={plan.plan_type}
            onClick={() => setSelectedPlan(plan.plan_type)}
            type="button"
          >
            <span className="plan-name">{plan.name}</span>
            <strong>{price.format(plan.monthly_price)}<small> / ay</small></strong>
            <span>{plan.monthly_credits ?? 'Sınırsız'} kahve</span>
            {plan.guest_credits > 0 && <span>{plan.guest_credits} misafir hakkı</span>}
            {plan.priority && <span>Öncelikli hazırlık</span>}
          </button>
        ))}
      </div>

      <form className="form-card payment-form" onSubmit={purchase}>
        <label className="field">
          Simülasyon kart numarası
          <input
            autoComplete="off"
            inputMode="numeric"
            onChange={(event) => setCardNumber(event.target.value)}
            required
            value={cardNumber}
          />
        </label>
        <p className="muted">
          Başarılı: 4242-4242-4242-4242 · Başarısız: 4000-0000-0000-0002
        </p>
        <button className="button" disabled={busy || plans.length === 0} type="submit">
          {busy ? 'İşleniyor…' : 'Seçili paketi satın al'}
        </button>
      </form>
    </section>
  )
}
