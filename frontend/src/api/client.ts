import type { ApiEnvelope } from '../types/api'

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'
).replace(/\/$/, '')

const accessTokenKey = 'kahvecell.accessToken'

export class ApiRequestError extends Error {
  readonly code: string

  constructor(message: string, code: string) {
    super(message)
    this.name = 'ApiRequestError'
    this.code = code
  }
}

export function saveAccessToken(token: string | null) {
  if (token) {
    localStorage.setItem(accessTokenKey, token)
  } else {
    localStorage.removeItem(accessTokenKey)
  }
}

export async function requestApi<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')

  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const token = localStorage.getItem(accessTokenKey)
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers })
  if (response.status === 204) {
    return undefined as T
  }

  const envelope = (await response.json()) as ApiEnvelope<T>
  if (!response.ok || !envelope.success || envelope.error !== null) {
    throw new ApiRequestError(
      envelope.error?.message ?? 'API isteği başarısız oldu.',
      envelope.error?.code ?? 'request_failed',
    )
  }
  if (envelope.data === null) {
    throw new ApiRequestError('API boş yanıt döndürdü.', 'empty_response')
  }
  return envelope.data
}

export function getApiData<T>(path: string, signal?: AbortSignal) {
  return requestApi<T>(path, { method: 'GET', signal })
}

export function postApiData<T>(path: string, body: unknown) {
  return requestApi<T>(path, { method: 'POST', body: JSON.stringify(body) })
}

export function patchApiData<T>(path: string, body: unknown) {
  return requestApi<T>(path, { method: 'PATCH', body: JSON.stringify(body) })
}
