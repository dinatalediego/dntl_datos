const KEY = 'dntl-datos-telemetry-v1'

export type ExplorerEvent =
  | 'app_open'
  | 'view_open'
  | 'domain_open'
  | 'question_asked'
  | 'install_prompt_shown'
  | 'install_requested'

export type TelemetrySnapshot = Record<string, number>

export function track(event: ExplorerEvent, detail?: string): void {
  try {
    const current = JSON.parse(localStorage.getItem(KEY) || '{}') as TelemetrySnapshot
    const key = detail ? `${event}:${detail}` : event
    current[key] = (current[key] || 0) + 1
    localStorage.setItem(KEY, JSON.stringify(current))
  } catch {
    // Telemetry is intentionally best-effort and local-only for the demo.
  }
}

export function telemetrySnapshot(): TelemetrySnapshot {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '{}') as TelemetrySnapshot
  } catch {
    return {}
  }
}
