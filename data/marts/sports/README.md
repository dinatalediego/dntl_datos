# FC Barcelona · tiros al arco (LaLiga)

Snapshot analítico con corte 2026-09-15. El objetivo es conservar tanto el agregado L3/L5/L10/L15 como una capa partido × jugador que permita reconstruir los indicadores sin depender de cálculos manuales.

## Semántica de ventanas

Las ventanas L3, L5, L10 y L15 se definen sobre los últimos N partidos del FC Barcelona en LaLiga.

Hay dos promedios diferentes:

- avg_sot_per_team_match_last_N: SOT acumulado / N partidos del Barcelona.
- avg_sot_per_appearance_last_N: SOT acumulado / apariciones reales del jugador.

El primero responde “cuánto aporta por partido del equipo”. El segundo responde “cuánto produce cuando juega”.

## Capas

### Agregado L3/L5/L10/L15

fc_barcelona_laliga_player_sot_windows_2026-09-15.csv conserva:
- acumulado de SOT;
- avg_sot_last_3 / 5 / 10 / 15;
- el alias histórico sot_per_team_match_last_N para compatibilidad.

### Partido × jugador

data/silver/sports/fc_barcelona_laliga_player_match_sot_2026-09-15.csv tiene grano:
date × player appearance.

Campos principales:
- rival y local/visitante;
- minutos;
- posición;
- tiros;
- tiros al arco;
- appeared;
- started nullable;
- URL y frescura de la fuente.

La titularidad NO se infiere a partir de minutos. Si la fuente no expone una señal explícita por partido, started queda vacío.

### Perfil analítico L5

fc_barcelona_laliga_player_sot_profiles_l5_2026-09-15.csv materializa:
- acumulado;
- promedio por partido del equipo;
- promedio por aparición;
- mediana;
- desviación estándar poblacional;
- % de apariciones con 1+, 2+ y 3+ SOT;
- minutos;
- SOT/90;
- media local y visitante;
- tendencia lineal de SOT por aparición;
- rival y sede más recientes;
- cobertura de titularidad.

## Cobertura y QA

El seed partido × jugador cubre todos los jugadores que aportaron al menos un SOT en los cinco partidos de liga 2026/27 observados. La suma por fecha reconcilia el 100% del volumen de SOT del equipo:

| Fecha | Rival | SOT Barça |
|---|---|---:|
| 2026-08-23 | Elche | 7 |
| 2026-08-27 | Athletic Club | 10 |
| 2026-08-31 | Rayo Vallecano | 9 |
| 2026-09-06 | Valencia | 10 |
| 2026-09-13 | Levante | 6 |

Total L5 = 42 SOT.

Importante: esto todavía no es un appearance grid completo de todos los jugadores con 0 SOT. Por eso:
- la reconciliación de volumen SOT L5 sí es completa;
- los indicadores de hit-rate/minutos se publican sólo donde hay filas de aparición verificadas;
- Pedri y Marc Bernal conservan source_freshness=through_2026-09-06 porque sus páginas observadas no estaban actualizadas al 13-Sep;
- el backfill partido × jugador de L10/L15 todavía debe ampliarse antes de tratar medianas, desviaciones e hit-rates L10/L15 como completos.

## Cálculos

dntl_datos.sports.barcelona_sot.build_window_summary genera, para cada N:
- sot_last_N
- avg_sot_per_team_match_last_N
- avg_sot_per_appearance_last_N
- median_sot_per_appearance_last_N
- std_sot_per_appearance_last_N
- hit_1plus_pct_last_N
- hit_2plus_pct_last_N
- hit_3plus_pct_last_N
- minutes_last_N
- sot_per_90_last_N
- avg_sot_home_per_appearance_last_N
- avg_sot_away_per_appearance_last_N
- trend_sot_per_appearance_last_N
- starts_known_last_N / starts_last_N
- latest_opponent_last_N / latest_venue_last_N

Los hit-rates usan apariciones como denominador; un partido que el jugador no disputó no cuenta como fallo.

## Fuentes

Fuente de investigación: Statz, que documenta datos de partido provenientes de Sportmonks, más el snapshot agregado original de StatMuse.

Referencias:
- https://statz.ai/team/fc-barcelona/shots-on-target
- https://statz.ai/player/lamine-yamal/37656179
- https://statz.ai/player/raphinha/160258
- https://statz.ai/player/fermin-lopez/37596363
- https://statz.ai/player/karim-adeyemi/15040126
- https://statz.ai/player/anthony-gordon/9611543
- https://statz.ai/player/dani-olmo/74060
- https://statz.ai/player/xavi-espart/37719662
- https://statz.ai/player/pedri/37288001
- https://statz.ai/player/marc-bernal/37710798

Uso: research_only. Mantener siempre as_of_date, URL de fuente y controles de reconciliación.
