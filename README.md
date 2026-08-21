# dntl_datos

Hub reproducible de ingesta **batch** de fuentes públicas para construir datacenters temáticos de mercados, macroeconomía y música.

## Qué incluye v0.1

| Dominio | Fuente | Dataset | Estado |
|---|---|---|---|
| Mercados | Yahoo Finance vía `yfinance` | precios OHLCV, índices, FX, cripto | activo |
| Macro global | World Bank Indicators API | PBI, inflación, desempleo, FX | activo |
| Macro Perú | BCRP Series API | series económicas configurables | activo |
| Música Perú | MusicBrainz | artistas vinculados a Perú | activo |
| Música Perú | Wikidata SPARQL | músicos peruanos + ocupación/género | activo |
| Charts | Billboard vía `billboard.py` | chart, ranking, artista, semanas | opcional |

> `yfinance` es una librería no oficial y su documentación recuerda que los datos de Yahoo Finance están orientados a uso personal. Billboard también se mantiene aislado como fuente opcional/no oficial. Para pipelines críticos conviene priorizar APIs oficiales o datasets con licencia explícita.

## Arquitectura

```text
Public APIs / libraries
        |
        v
connectors/*
        |
        v
data/raw/<source>/<dataset>/run_date=YYYY-MM-DD/
        |-- data.parquet
        `-- manifest.json
        |
        +--> DuckDB / PostgreSQL / Power BI / notebooks / ML
```

Cada lote genera Parquet + `manifest.json` con fuente, dataset, fecha de corrida, filas y columnas.

## Instalación

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -e .
```

Para habilitar Billboard:

```bash
pip install -e ".[billboard]"
```

## Ejecutar todos los lotes

```bash
dntl-datos --config config/sources.yaml
```

También existe `.github/workflows/public_batch.yml` para ejecución manual o programada en GitHub Actions. Los Parquet se publican como artifacts de cada corrida y no se versionan como código.

## Configuración

Edita `config/sources.yaml` para añadir tickers, países, indicadores, series BCRP o charts.

Ejemplos incluidos:

- `SPY`, `QQQ`, `EEM`, S&P 500, Nasdaq, BTC/USD y USD/PEN.
- Perú, Chile, Colombia, México y EE. UU. vía World Bank.
- tipo de cambio del BCRP.
- artistas peruanos vía MusicBrainz y Wikidata.
- Hot 100, Billboard 200 y Latin Songs como adaptadores opcionales.

## Siguiente capa sugerida

La evolución natural es agregar `silver/` con contratos homogéneos (`entity_id`, `event_date`, `metric`, `value`, `source`) y luego datamarts como:

- `market_daily`
- `macro_country_period`
- `artist_master`
- `artist_chart_performance`
- `peru_music_commercial_panel`

Así `dntl_datos` puede convertirse en una colección de **datacenters pequeños y combinables**, no en una carpeta de CSV sueltos.

## Fuentes

- Yahoo Finance / yfinance: https://ranaroussi.github.io/yfinance/
- World Bank Indicators API: https://api.worldbank.org/
- BCRP Estadísticas: https://estadisticas.bcrp.gob.pe/
- MusicBrainz Web Service: https://musicbrainz.org/doc/MusicBrainz_API
- Wikidata Query Service: https://query.wikidata.org/
- Billboard: conector opcional mediante `billboard.py`; no se considera una API oficial estable.
