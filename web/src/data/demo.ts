export const demoSummary = {
  data_mode: 'demo',
  market_rows: 9402,
  macro_rows: 330,
  artist_rows: 1424,
  catalog_rows: 14,
  sources: ['Yahoo Finance', 'World Bank', 'BCRP', 'MusicBrainz', 'Wikidata'],
} as const

export const demoMarkets = {
  data_mode: 'demo',
  items: ['SPY', 'QQQ', 'EEM', '^GSPC', '^IXIC', 'BTC-USD', 'PEN=X'].map((ticker) => ({
    ticker,
    date: null,
    close: null,
    daily_return: null,
    volatility_30d_ann: null,
    drawdown: null,
  })),
}

export const demoArtists = {
  data_mode: 'demo',
  items: ['Gian Marco', 'Eva Ayllón', 'Susana Baca', 'Daniela Darcourt', 'Grupo 5', 'Renata Flores'].map(
    (artist_name) => ({
      artist_name,
      match_status: 'demo',
      genre: null,
      occupation: null,
      country: 'PE',
      begin_area: null,
      musicbrainz_score: null,
    }),
  ),
}

export const demoMacro = {
  data_mode: 'demo',
  country: 'PER',
  items: [],
}
