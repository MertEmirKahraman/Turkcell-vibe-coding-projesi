export type ServiceStatus = 'checking' | 'connected' | 'unavailable'

interface StatusBadgeProps {
  status: ServiceStatus
}

const labels: Record<ServiceStatus, string> = {
  checking: 'Kontrol ediliyor',
  connected: 'Bağlı',
  unavailable: 'Ulaşılamıyor',
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge--${status}`}>
      {labels[status]}
    </span>
  )
}