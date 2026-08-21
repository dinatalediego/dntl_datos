# dntl_datos

Hub reproducible de ingesta **batch** de fuentes públicas y hogar de **DNTL Datos Explorer**, una web app responsive/PWA para explorar mercados, macroeconomía y música peruana.

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
      |
      v
SILVER
      |
      v
MARTS
      |
      +--------------------+
      |                    |
      v                    v
FastAPI read-only       Power BI / ML
      |
      v
DNTL Datos Explorer
React + Vite + PWA
      |
      v
Web responsive -> instalar en Android -> validar uso -> Android nativo si aporta valor
```

Cada dataset materializado genera `data.parquet` y `manifest.json` con capa, fuente, dataset, fecha, filas y columnas.

## DNTL Datos Explorer v0.2

La primera experiencia incluye cuatro vistas mobile-first:

1. **Inicio**: estado de los datacenters, cobertura y señales de uso.
2. **Música Peruana**: búsqueda por artista, género u ocupación.
3. **Mercados**: último estado disponible por ticker con retorno, volatilidad y drawdown.
4. **Economía**: panel por país para Perú, Chile, Colombia, México y EE. UU.

La barra **“Pregunta a DNTL Datos”** usa por ahora routing determinístico sobre los marts. No depende todavía de un LLM y siempre muestra las fuentes utilizadas.

La aplicación tiene dos modos:

- `LIVE`: la API encontró los marts locales.
- `DEMO`: la interfaz usa únicamente cobertura validada y evita inventar cotizaciones o indicadores puntuales.

La validación inicial de producto se guarda en `localStorage` del propio navegador: aperturas, navegación, preguntas e intención de instalación. No se envía telemetría a terceros en esta versión.

### API

```text
GET /api/health
GET /api/summary
GET /api/markets
GET /api/macro?country=PER
GET /api/artists?q=...
GET /api/ask?q=...
```

### Ejecutar en Windows / VS Code

Preparación manual desde la raíz del repositorio:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cd web
npm install
cd ..
```

Luego puedes abrir API + web con:

```powershell
.\scripts\run_explorer.ps1
```

O ejecutarlas por separado:

```powershell
# Terminal 1
.\.venv\Scripts\Activate.ps1
dntl-datos-api

# Terminal 2
cd web
npm run dev
```

La web queda en `http://127.0.0.1:5173` y la API en `http://127.0.0.1:8000`.

Para probar el modo `LIVE`, ejecuta antes el pipeline completo:

```powershell
dntl-datos --config config/sources.yaml --stage all
```

### PWA / Android

La carpeta `web/public` contiene:

- `manifest.webmanifest`
- `sw.js`
- `icon.svg`

En producción sobre HTTPS, un navegador Android compatible puede ofrecer la instalación de **DNTL Datos** como aplicación standalone. La app nativa se posterga hasta tener evidencia de uso que justifique capacidades móviles adicionales.

## Marts analíticos

### `market_daily_features`

Grano: `ticker x date`.

Incluye OHLCV más `daily_return`, `ma_20`, `ma_60`, `volatility_30d_ann`, `drawdown`, `year` y `month`.

### `macro_country_year`

Grano: `country x year`. Convierte los indicadores del World Bank a un panel ancho listo para Power BI, econometría y ML.

### `peru_artist_master`

Grano: artista canónico. Cruza MusicBrainz y Wikidata usando una `artist_key` normalizada y conserva `matched`, `musicbrainz_only` o `wikidata_only`.

### `billboard_artist_snapshot`

Se crea solo si se habilita Billboard. Añade `chart_points` y marca coincidencias con el catálogo peruano.

## Instalación del motor de datos

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

## Pipeline batch

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

`all` ejecuta `raw -> silver -> marts -> catalog`.

## Configuración y catálogo

- `config/sources.yaml`: qué fuentes, tickers, países, indicadores y charts se extraen.
- `config/catalog.yaml`: dominio, descripción, grano, claves, cadencia, nivel de uso y consumidores esperados de cada dataset.

## Automatización

`.github/workflows/public_batch.yml` ejecuta el pipeline completo manualmente o en calendario y publica `data/raw`, `data/silver`, `data/marts` y `data/catalog` como artifact.

`.github/workflows/ci.yml` valida tanto el backend Python (`pytest`) como el build productivo del frontend React/Vite.

## Próximas extensiones naturales

- persistir marts en un storage accesible desde la web desplegada.
- publicar la PWA en HTTPS.
- Wikipedia Pageviews / Google Trends para atención pública.
- Spotify/YouTube mediante APIs autorizadas para señales musicales digitales.
- INEI, MEF y datos abiertos del Estado peruano.
- `peru_music_commercial_panel`: artista x canción x semana x plataforma.
- evaluar Android nativo únicamente después de observar uso real de la PWA.

## Fuentes

- Yahoo Finance / yfinance: https://ranaroussi.github.io/yfinance/
- World Bank Indicators API: https://api.worldbank.org/
- BCRP Estadísticas: https://estadisticas.bcrp.gob.pe/
- MusicBrainz Web Service: https://musicbrainz.org/doc/MusicBrainz_API
- Wikidata Query Service: https://query.wikidata.org/
- Billboard: conector opcional mediante `billboard.py`; no se considera una API oficial estable.
