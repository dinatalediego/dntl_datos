import { FormEvent, useEffect, useMemo, useState } from 'react'

import { apiGet } from './lib/api'
import { telemetrySnapshot, track } from './lib/telemetry'
import { demoArtists, demoMacro, demoMarkets, demoSummary } from './data/demo'

type View = 'home' | 'music' | 'markets' | 'macro'
type DataMode = 'live' | 'demo'

type Summary = {
  data_mode: DataMode
  market_rows: number
  macro_rows: number
  artist_rows: number
  catalog_rows: number
  sources: string[]
}

type MarketItem = {
  ticker: string
  date: string | null
  close: number | null
  daily_return: number | null
  volatility_30d_ann: number | null
  drawdown: number | null
}

type ArtistItem = {
  artist_name: string
  match_status: string | null
  genre: string | null
  occupation: string | null
  country: string | null
  begin_area: string | null
  musicbrainz_score: number | null
}

type MacroItem = Record<string, string | number | null>

type AskResponse = {
  question: string
  answer: string
  route: string
  sources: string[]
  data_mode: DataMode
}

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>
}

const nav: Array<{ id: View; label: string; symbol: string }> = [
  { id: 'home', label: 'Inicio', symbol: '◉' },
  { id: 'music', label: 'Música', symbol: '♪' },
  { id: 'markets', label: 'Mercados', symbol: '↗' },
  { id: 'macro', label: 'Economía', symbol: '◎' },
]

function compact(value: number): string {
  return new Intl.NumberFormat('es-PE', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
}

function number(value: number | null, digits = 2): string {
  if (value === null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('es-PE', { maximumFractionDigits: digits }).format(value)
}

function percent(value: number | null): string {
  if (value === null || Number.isNaN(value)) return '—'
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`
}

function App() {
  const [view, setView] = useState<View>('home')
  const [summary, setSummary] = useState<Summary>(demoSummary as Summary)
  const [markets, setMarkets] = useState<MarketItem[]>(demoMarkets.items)
  const [artists, setArtists] = useState<ArtistItem[]>(demoArtists.items)
  const [macro, setMacro] = useState<MacroItem[]>([])
  const [country, setCountry] = useState('PER')
  const [artistQuery, setArtistQuery] = useState('')
  const [question, setQuestion] = useState('')
  const [askResult, setAskResult] = useState<AskResponse | null>(null)
  const [asking, setAsking] = useState(false)
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null)

  useEffect(() => {
    apiGet<Summary>('/api/summary', demoSummary as Summary).then(setSummary)
    apiGet<{ data_mode: DataMode; items: MarketItem[] }>('/api/markets', demoMarkets as { data_mode: DataMode; items: MarketItem[] }).then(
      (result) => setMarkets(result.items),
    )
    apiGet<{ data_mode: DataMode; items: ArtistItem[] }>('/api/artists?limit=30', demoArtists as { data_mode: DataMode; items: ArtistItem[] }).then(
      (result) => setArtists(result.items),
    )
  }, [])

  useEffect(() => {
    const fallback = { ...demoMacro, country, items: [] as MacroItem[] }
    apiGet<{ data_mode: DataMode; country: string; items: MacroItem[] }>(`/api/macro?country=${country}&years=12`, fallback).then(
      (result) => setMacro(result.items),
    )
  }, [country])

  useEffect(() => {
    const onInstall = (rawEvent: Event) => {
      rawEvent.preventDefault()
      const event = rawEvent as BeforeInstallPromptEvent
      setInstallPrompt(event)
      track('install_prompt_shown')
    }
    window.addEventListener('beforeinstallprompt', onInstall)
    return () => window.removeEventListener('beforeinstallprompt', onInstall)
  }, [])

  useEffect(() => {
    track('view_open', view)
  }, [view])

  const latestMacro = macro.length ? macro[macro.length - 1] : null
  const telemetry = useMemo(() => telemetrySnapshot(), [view, askResult, installPrompt])

  const go = (next: View) => {
    setView(next)
    if (next !== 'home') track('domain_open', next)
  }

  const searchArtists = async (event: FormEvent) => {
    event.preventDefault()
    const result = await apiGet<{ data_mode: DataMode; items: ArtistItem[] }>(
      `/api/artists?q=${encodeURIComponent(artistQuery)}&limit=40`,
      demoArtists as { data_mode: DataMode; items: ArtistItem[] },
    )
    setArtists(result.items)
  }

  const ask = async (event: FormEvent) => {
    event.preventDefault()
    const clean = question.trim()
    if (clean.length < 2) return
    setAsking(true)
    track('question_asked')
    const fallback: AskResponse = {
      question: clean,
      answer: 'Estoy en modo demo. Puedo explorar música peruana, mercados y economía; conecta la API para responder con los marts actuales.',
      route: 'home',
      sources: summary.sources,
      data_mode: 'demo',
    }
    const result = await apiGet<AskResponse>(`/api/ask?q=${encodeURIComponent(clean)}`, fallback)
    setAskResult(result)
    setAsking(false)
  }

  const install = async () => {
    if (!installPrompt) return
    track('install_requested')
    await installPrompt.prompt()
    await installPrompt.userChoice
    setInstallPrompt(null)
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Navegación principal">
        <button className="brand" onClick={() => go('home')} aria-label="DNTL Datos Inicio">
          <span className="brand-mark">D</span>
          <span>
            <strong>DNTL Datos</strong>
            <small>Explorer</small>
          </span>
        </button>
        <nav className="side-nav">
          {nav.map((item) => (
            <button key={item.id} className={view === item.id ? 'nav-item active' : 'nav-item'} onClick={() => go(item.id)}>
              <span>{item.symbol}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span className={`mode-dot ${summary.data_mode}`} />
          {summary.data_mode === 'live' ? 'Datos en vivo' : 'Modo demo'}
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">PUBLIC DATA COMMONS</p>
            <h1>{view === 'home' ? 'Explora señales, no archivos.' : nav.find((item) => item.id === view)?.label}</h1>
          </div>
          <div className="top-actions">
            <span className={`mode-pill ${summary.data_mode}`}>{summary.data_mode === 'live' ? 'LIVE' : 'DEMO'}</span>
            {installPrompt && (
              <button className="install-button" onClick={install}>
                Instalar app
              </button>
            )}
          </div>
        </header>

        {view === 'home' && (
          <section className="view-stack">
            <div className="hero-card">
              <div>
                <p className="eyebrow">DNTL DATOS EXPLORER · v0.2</p>
                <h2>Un solo lugar para mirar música peruana, mercados y economía.</h2>
                <p className="muted">
                  La interfaz usa tus marts cuando están disponibles. Si no, entra en demo sin inventar precios ni indicadores puntuales.
                </p>
              </div>
              <div className="hero-orbit" aria-hidden="true"><span>DNTL</span></div>
            </div>

            <div className="domain-grid">
              <button className="domain-card music-card" onClick={() => go('music')}>
                <div className="card-symbol">♪</div>
                <span className="card-kicker">MÚSICA PERUANA</span>
                <strong>{compact(summary.artist_rows)} artistas</strong>
                <p>Identidad, género, ocupación y reconciliación entre fuentes.</p>
                <span className="card-link">Explorar catálogo →</span>
              </button>
              <button className="domain-card" onClick={() => go('markets')}>
                <div className="card-symbol">↗</div>
                <span className="card-kicker">MERCADOS</span>
                <strong>{compact(summary.market_rows)} observaciones</strong>
                <p>Retornos, medias móviles, volatilidad y drawdown.</p>
                <span className="card-link">Abrir radar →</span>
              </button>
              <button className="domain-card" onClick={() => go('macro')}>
                <div className="card-symbol">◎</div>
                <span className="card-kicker">ECONOMÍA</span>
                <strong>{compact(summary.macro_rows)} filas país-año</strong>
                <p>Perú y LatAm con World Bank y series BCRP.</p>
                <span className="card-link">Ver panel →</span>
              </button>
            </div>

            <div className="split-grid">
              <section className="panel">
                <div className="panel-head"><h3>Datacenters</h3><span>{summary.catalog_rows} registrados</span></div>
                <div className="source-list">
                  {summary.sources.map((source) => <span key={source}>{source}</span>)}
                </div>
              </section>
              <section className="panel validation-panel">
                <div className="panel-head"><h3>Validar uso real</h3><span>solo este dispositivo</span></div>
                <div className="mini-metrics">
                  <div><strong>{telemetry.app_open || 1}</strong><span>aperturas</span></div>
                  <div><strong>{telemetry.question_asked || 0}</strong><span>preguntas</span></div>
                  <div><strong>{telemetry.install_requested || 0}</strong><span>intentos de instalar</span></div>
                </div>
              </section>
            </div>
          </section>
        )}

        {view === 'music' && (
          <section className="view-stack">
            <div className="section-intro">
              <div><p className="eyebrow">PERU MUSIC INTELLIGENCE</p><h2>¿Quién está en el mapa?</h2></div>
              <span className="big-number">{compact(summary.artist_rows)}</span>
            </div>
            <form className="search-bar" onSubmit={searchArtists}>
              <input value={artistQuery} onChange={(e) => setArtistQuery(e.target.value)} placeholder="Busca artista, género u ocupación…" />
              <button>Buscar</button>
            </form>
            <div className="artist-grid">
              {artists.map((artist, index) => (
                <article className="artist-card" key={`${artist.artist_name}-${index}`}>
                  <div className="artist-avatar">{artist.artist_name.slice(0, 1).toUpperCase()}</div>
                  <div><h3>{artist.artist_name}</h3><p>{artist.genre || artist.occupation || 'Catálogo musical peruano'}</p></div>
                  <span className="match-chip">{artist.match_status || 'catalog'}</span>
                </article>
              ))}
            </div>
          </section>
        )}

        {view === 'markets' && (
          <section className="view-stack">
            <div className="section-intro">
              <div><p className="eyebrow">MARKET RADAR</p><h2>Señales antes que titulares.</h2></div>
              <span className="big-number">{compact(summary.market_rows)}</span>
            </div>
            <div className="market-table" role="table" aria-label="Resumen de mercados">
              <div className="market-row market-header" role="row"><span>Activo</span><span>Último</span><span>Retorno</span><span>Vol. 30d</span><span>Drawdown</span></div>
              {markets.map((item) => (
                <div className="market-row" role="row" key={item.ticker}>
                  <strong>{item.ticker}</strong>
                  <span>{number(item.close)}</span>
                  <span className={item.daily_return !== null && item.daily_return < 0 ? 'negative' : 'positive'}>{percent(item.daily_return)}</span>
                  <span>{percent(item.volatility_30d_ann)}</span>
                  <span className="negative">{percent(item.drawdown)}</span>
                </div>
              ))}
            </div>
            {summary.data_mode === 'demo' && <p className="demo-note">Modo demo: mostramos cobertura e instrumentos, pero no inventamos cotizaciones.</p>}
          </section>
        )}

        {view === 'macro' && (
          <section className="view-stack">
            <div className="section-intro">
              <div><p className="eyebrow">MACRO LATAM</p><h2>Contexto para entender el movimiento.</h2></div>
              <select value={country} onChange={(e) => setCountry(e.target.value)} aria-label="País">
                <option value="PER">Perú</option><option value="CHL">Chile</option><option value="COL">Colombia</option><option value="MEX">México</option><option value="USA">EE. UU.</option>
              </select>
            </div>
            {latestMacro ? (
              <div className="macro-grid">
                {Object.entries(latestMacro).filter(([key]) => !['country_code', 'country'].includes(key)).map(([key, value]) => (
                  <article className="metric-card" key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{typeof value === 'number' ? number(value, 2) : value || '—'}</strong></article>
                ))}
              </div>
            ) : (
              <div className="empty-state"><strong>Panel listo para conectarse.</strong><p>Cuando el mart esté accesible para la API, aquí aparecerán los últimos años del país seleccionado.</p></div>
            )}
          </section>
        )}

        <section className="ask-dock" aria-label="Pregunta a DNTL Datos">
          {askResult && (
            <div className="answer-card">
              <div><span className="answer-mark">D</span></div>
              <div><p>{askResult.answer}</p><small>Fuentes: {askResult.sources.join(' · ')}</small></div>
              <button onClick={() => setAskResult(null)} aria-label="Cerrar respuesta">×</button>
            </div>
          )}
          <form onSubmit={ask}>
            <span className="ask-icon">⌁</span>
            <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Pregunta a DNTL Datos…" />
            <button disabled={asking}>{asking ? '…' : 'Preguntar'}</button>
          </form>
        </section>
      </main>

      <nav className="bottom-nav" aria-label="Navegación móvil">
        {nav.map((item) => (
          <button key={item.id} className={view === item.id ? 'active' : ''} onClick={() => go(item.id)}><span>{item.symbol}</span><small>{item.label}</small></button>
        ))}
      </nav>
    </div>
  )
}

export default App
