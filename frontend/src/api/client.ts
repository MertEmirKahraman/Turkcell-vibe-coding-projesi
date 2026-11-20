import type { ApiEnvelope } from '../types/api'

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'
).replace(/\/$/, '')

export class ApiRequestError extends Error {
  readonly code: string

  constructor(
    message: string,
    code: string,
  ) {
    super(message)
    this.name = 'ApiRequestError'
    this.code = code
  }
}

export async function getApiData<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { signal })
  const result = (await response.json()) as ApiEnvelope<T>

  if (!response.ok || !result.success || result.error !== null) {
    throw new ApiRequestError(
      result.error?.message ?? 'API request failed',
      result.error?.code ?? 'request_failed',
    )
  }

  if (result.data === null) {
    throw new ApiRequestError('API returned no data', 'empty_response')
  }

  return result.data
}