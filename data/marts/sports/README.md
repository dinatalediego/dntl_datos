# FC Barcelona · tiros al arco (LaLiga)

Snapshot analítico al **2026-09-15** para estudiar tiros al arco (SOT, shots on target) del FC Barcelona por jugador.

## Definición de las ventanas

Las ventanas L3, L5, L10 y L15 se calculan sobre los **últimos N partidos del FC Barcelona en LaLiga**, no sobre los últimos N partidos personales de cada jugador. Esto mantiene el mismo período de comparación para todos los jugadores.

`sot_per_team_match_last_N` usa N como denominador. Por ejemplo, 8 SOT de Lamine Yamal en L3 = 8 / 3 = 2.667 SOT por partido del equipo.

## Archivos

- `fc_barcelona_laliga_player_sot_windows_2026-09-15.csv`: SOT acumulados y por partido de equipo en L3/L5/L10/L15.
- `fc_barcelona_laliga_team_sot_matches_2026-09-15.csv`: log de los 15 partidos del equipo que definen la ventana máxima.

## Control de calidad

La suma de SOT de jugadores debe reconciliar con el total del equipo:

| Ventana | SOT equipo | Suma jugadores |
|---|---:|---:|
| L3 | 25 | 25 |
| L5 | 42 | 42 |
| L10 | 66 | 66 |
| L15 | 95 | 95 |

Si una futura actualización no reconcilia, el snapshot no debe publicarse como validado.

## Fuentes

Fuente de investigación: StatMuse FC, LaLiga.

Consultas de referencia:
- https://www.statmuse.com/fc/ask/barcelona-players-stats-shots-on-target-last-3-matches?l=laliga
- https://www.statmuse.com/fc/ask/barcelona-player-most-shots-on-target-last-5-games?l=laliga
- https://www.statmuse.com/fc/ask/which-barcelona-player-has-the-most-shots-on-target-last-10-games?l=laliga
- https://www.statmuse.com/fc/ask/barcelona-shots-on-target-in-the-last-15-games?l=laliga

El dataset es para análisis/research. La cobertura y metodología del proveedor pueden cambiar; por eso se conserva `as_of_date`, el log de partidos y la reconciliación de totales.

## Actualización futura

Normaliza observaciones a grano `date x player` con al menos:
`date, player, shots_on_target, appeared`.

Luego usa `dntl_datos.sports.barcelona_sot.build_window_summary` para regenerar las ventanas sin cambiar la semántica.
