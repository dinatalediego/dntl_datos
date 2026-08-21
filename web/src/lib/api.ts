export async function apiGet<T>(path: string, fallback: T): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 5000)

  try {
    const response = await fetch(path, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    })
    if (!response.ok) throw new Error(`API ${response.status}`)
    return (await response.json()) as T
  } catch {
    return fallback
  } finally {
    window.clearTimeout(timeout)
  }
}
