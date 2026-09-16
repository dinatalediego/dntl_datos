# FC Barcelona · Shot-on-target intelligence (LaLiga)

Snapshot reproducible con corte **2026-09-15**. La base ya no depende sólo de agregados: conserva el nivel **partido × jugador** para los últimos 15 partidos ligueros del FC Barcelona.

## Estado de cobertura

- 15 partidos de equipo.
- 241 apariciones reales.
- 31 jugadores distintos.
- 465 filas en el grid denso = 15 partidos × 31 jugadores.
- 11 titulares validados en cada partido.
- 95 SOT de jugadores = 95 SOT del equipo.
- 233 tiros del equipo en L15.
- L3 = 25 SOT, L5 = 42, L10 = 66, L15 = 95.

La fuente de control es StatMuse. Para no confundir "jugó y tuvo 0 SOT" con "no jugó", se conservan dos tablas:

### 1. Apariciones reales
`data/silver/sports/fc_barcelona_laliga_player_match_sot_2026-09-15.csv`

Una fila sólo si el jugador apareció. Grano:
`competition × club × date × player appearance`.

### 2. Grid denso
`data/silver/sports/fc_barcelona_laliga_player_match_grid_l15_2026-09-15.csv`

Una fila por cada combinación de los 15 partidos y los 31 jugadores observados. Cuando no aparece:
- `appeared=0`
- `started=0`
- `minutes=0`
- `shots_on_target=0`
- `appearance_status=did_not_appear`

Esto permite usar tanto el denominador **partidos del equipo** como el denominador **apariciones**.

## Marts

### Ventanas
`fc_barcelona_laliga_player_sot_windows_2026-09-15.csv`

Por jugador:
- acumulado L3/L5/L10/L15;
- promedio SOT por partido del Barça;
- apariciones;
- promedio SOT por aparición.

### Perfil analítico completo
`fc_barcelona_laliga_player_sot_profiles_2026-09-15.csv`

Para L3, L5, L10 y L15 materializa:
- SOT acumulado;
- promedio por partido del equipo;
- promedio por aparición;
- mediana y desviación con ambos denominadores;
- % 1+, 2+ y 3+ SOT por partido del equipo;
- % 1+, 2+ y 3+ SOT por aparición;
- minutos y SOT/90;
- apariciones y titularidades;
- media local/visitante;
- tendencia lineal por partido y por aparición;
- rival y sede de la última aparición.

El alias histórico `hit_Xplus_pct_last_N` conserva el denominador por aparición.

## QA

`validate_complete_appearance_grid` bloquea el snapshot si:
- existe duplicado date × player;
- falta alguna fecha de los 15 partidos;
- una aparición tiene `appeared != 1`;
- un partido no tiene exactamente 11 titulares;
- los minutos están fuera de 1..120;
- la suma de SOT de jugadores no reconcilia con el SOT del equipo.

`build_dense_player_match_grid` genera el grid DNP explícito.
`build_window_summary` produce todas las métricas L3/L5/L10/L15 desde el nivel granular.

## Fuente y limitación importante

Fuente principal: StatMuse, consultado con corte 2026-09-15/16.
Referencia de control:
https://www.statmuse.com/fc/ask/barcelona-shots-on-target-in-the-last-15-games?l=laliga

Los SOT y minutos/titularidad se construyen desde los match logs, lineups y player stats. La columna `shots` individual queda vacía en este backfill cuando no existe un valor player-level verificado de manera homogénea; **no se imputa**. El total de tiros del equipo sí se conserva en la tabla de partidos y reconcilia 233 para L15.

Uso: `research_only`.
