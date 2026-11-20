import { useEffect, useState } from 'react'

import { ApiRequestError, getApiData } from '../../api/client'
import { StatusBadge, type ServiceStatus } from '../../components/StatusBadge'

interface HealthResponse {
  status: string
}

export function HealthPanel() {
  const [status, setStatus] = useState<ServiceStatus>('checking')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    getApiData<HealthResponse>('/health', controller.signal)
      .then(() => setStatus('connected'))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return

        setStatus('unavailable')
        setErrorMessage(
          error instanceof ApiRequestError
            ? error.message
            : 'Backend API ile bağlantı kurulamadı.',
        )
      })

    return () => controller.abort()
  }, [])

  return (
    <section className="health-panel" aria-live="polite">
      <div>
        <p className="health-label">Backend API</p>
        <p className="health-detail">GET /api/v1/health</p>
        {errorMessage && <p className="health-error">{errorMessage}</p>}
      </div>
      <StatusBadge status={status} />
    </section>
  )
}