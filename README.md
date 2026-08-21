# dntl_datos

Hub reproducible de ingesta **batch** de fuentes públicas para construir datacenters temáticos de mercados, macroeconomía y música.

## Qué incluye

| Dominio | Fuente | Dataset | Estado |
|---|---|---|---|
| Mercados | Yahoo Finance vía `yfinance` | precios OHLCV, índices, FX, cripto | activo |
| Macro global | World Bank Indicators API | PBI, inflación, desempleo, FX | activo |
| Macro Perú | BCRP Series API | series económicas configurables | activo |
| Música Perú | MusicBrainz | artistas vinculados a Perú | activo |
| Música Perú | Wikidata SPARQL | músicos peruanos + ocupación/género | activo |
| Charts | Billboard vía `billboard.py` | chart, ranking, artista, semanas | opcional |

> `yfinance` y el adaptador de Billboard se consideran fuentes de investigación/no oficiales. Para pipelines críticos se priorizan APIs oficiales o datasets con licencias explícitas.

## Arquitectura

```text
Fuentes públicas
      |
      v
connectors/*
      |
      v
RAW / Bronze
  data/raw/<source>/<dataset>/run_date=YYYY-MM-DD/
      |
      v
SILVER
  tipado + nombres consistentes + claves normalizadas
      |
      v
MARTS
  market_daily_features
  macro_country_year
  peru_artist_master
  billboard_artist_snapshot (opcional)
      |
      v
Power BI / Python / econometría / ML / agentes

CATALOG
  config/catalog.yaml          <- contrato declarativo
  data/catalog/...             <- inventario materializado de cada corrida
```

Cada dataset materializado genera `data.parquet` y `manifest.json` con capa, fuente, dataset, fecha, filas y columnas.

## Marts analíticos

### `market_daily_features`

Grano: `ticker x date`.

Incluye OHLCV más:

- `daily_return`
- `ma_20`
- `ma_60`
- `volatility_30d_ann`
- `drawdown`
- `year`
- `month`

### `macro_country_year`

Grano: `country x year`. Convierte los indicadores del World Bank a un panel ancho listo para Power BI, econometría y ML.

### `peru_artist_master`

Grano: artista canónico. Cruza MusicBrainz y Wikidata usando una `artist_key` normalizada y conserva el estado del match:

- `matched`
- `musicbrainz_only`
- `wikidata_only`

Incluye IDs externos, género, ocupación, fecha de nacimiento, localización y metadata de MusicBrainz.

### `billboard_artist_snapshot`

Se crea solo si se habilita Billboard. Añade `chart_points` y marca coincidencias con el catálogo peruano.

## Instalación

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -e .
```

Desarrollo/tests:

```bash
pip install -e ".[dev]"
pytest -q
```

Billboard opcional:

```bash
pip install -e ".[billboard]"
```

## Ejecutar

Pipeline completo:

```bash
dntl-datos --config config/sources.yaml --stage all
```

Por etapas:

```bash
dntl-datos --stage raw
dntl-datos --stage silver
dntl-datos --stage marts
dntl-datos --stage catalog
```

`all` ejecuta:

```text
raw -> silver -> marts -> catalog
```

## Configuración y catálogo

- `config/sources.yaml`: qué fuentes, tickers, países, indicadores y charts se extraen.
- `config/catalog.yaml`: dominio, descripción, grano, claves, cadencia, nivel de uso y consumidores esperados de cada dataset.

Ejemplos incluidos:

- `SPY`, `QQQ`, `EEM`, S&P 500, Nasdaq, BTC/USD y USD/PEN.
- Perú, Chile, Colombia, México y EE. UU. vía World Bank.
- tipo de cambio del BCRP.
- artistas peruanos vía MusicBrainz y Wikidata.
- Hot 100, Billboard 200 y Latin Songs como adaptadores opcionales.

## Automatización

`.github/workflows/public_batch.yml` ejecuta el pipeline completo manualmente o en calendario y publica como artifact:

```text
data/raw
data/silver
data/marts
data/catalog
```

`.github/workflows/ci.yml` instala el proyecto y ejecuta `pytest` en pushes y pull requests.

## Próximas extensiones naturales

El diseño permite sumar conectores sin cambiar las capas superiores. Buenos siguientes datacenters:

- Wikipedia Pageviews / Google Trends para atención pública.
- Spotify/YouTube mediante APIs autorizadas para señales musicales digitales.
- INEI, MEF y datos abiertos del Estado peruano para economía Perú.
- SEC/FRED u otras APIs oficiales para mercados y macro internacional.
- un `peru_music_commercial_panel` longitudinal: artista x canción x semana x plataforma.

## Fuentes

- Yahoo Finance / yfinance: https://ranaroussi.github.io/yfinance/
- World Bank Indicators API: https://api.worldbank.org/
- BCRP Estadísticas: https://estadisticas.bcrp.gob.pe/
- MusicBrainz Web Service: https://musicbrainz.org/doc/MusicBrainz_API
- Wikidata Query Service: https://query.wikidata.org/
- Billboard: conector opcional mediante `billboard.py`; no se considera una API oficial estable.
