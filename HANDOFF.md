# HANDOFF — DayZ-MCP

<!-- LIVE-STATE:START -->
# DayZ-MCP — Estado vivo · snapshot 2026-09-16 (tras la promoción 5)

**Última verificación real:** 2026-09-16 12:52.
- **Árbol vivo `P:\DayZ_MCP_dev`:** `main` en `1737dc5`, en sync con origin. Entra la Ola A entera: cierre ordenado del run, cola de la caja con `on_busy="queue"`, `action_use` con `target`, ESC cancelando `ui_dialog` y la retirada de `vehicle_drive` y `drive_probe_client`.
- **Daemon:** generación `c7ee586e…`, `daemon_modules.stale=[]`, doctor `DAEMON_STATUS_OK`. Ahora **parado** por su vigía de inactividad (`idle 3631s >= 3600s`); arranca en diferido con la próxima llamada, ya sobre este árbol.
- **PBO desplegado:** `1E79BF80…` (243617 B), empaquetado desde `1737dc5`. Sus 13 entradas dan `exact` contra ese commit y no lleva ninguna ajena. Copia del anterior: `DayZ_MCP.pbo.bak_pre_promote5_20260916` (`EB62B4E7…`, 254861 B).
- **Launcher nativo:** sin tocar desde #57 (PE `67D974AF…`, registro `1CBC9ED4…`). Ningún módulo embebido cambió en esta ola: el gate de módulos sellados lo comprobó en cada ficha.
- **Verificado en juego tras la promoción:** compila limpio en cliente y servidor (0 `Can't compile`, solo las 8 líneas `SCRIPT (E)` conocidas), el censo de capacidades da `match` y prueba que el PBO nuevo está cargado, `action_use` arranca `ActionDrink` con `target="hands"` y `target="self"`, y un run adoptado sobrevive a 160 s de pausa con heartbeats.
- **Sin verificar todavía, para el próximo ciclo:** ESC cancelando el diálogo con teclas físicas, `dayz_test_close` grácil, el ratón libre al aparecer la ventana (`f298`) y la cola con dos sesiones. Requieren reabrir un cliente MCP: el catálogo de una sesión abierta antes de la promoción no trae las tools ni los parámetros nuevos, y recargar el worker no lo refresca.

bugs: tracker = buzón `pipeline_inbox` · **29** abiertas (censo 2026-09-15 12:53: 30 + 4 nuevas − 5 resueltas) · toque 2026-09-15
ciclos_en_este_objetivo: 1 (triaje del buzón + promociones + Ola 1 + 160e y delegables + Ola 2 + verificación de #57)

## Estado actual

- **Ola A cerrada y promocionada.** Ocho PR fusionados entre el 15 y el 16 y llevados a vivo en la promoción 5: el
  cierre ordenado de un run (`dayz_test_close` y `close_run` en el daemon), la fase 1 de la cola de la caja
  (`on_busy="queue"`, `queue_offer` y `queue_position` en `session_status.box`), `action_use` con `target` world, hands
  o self, ESC cancelando un `ui_dialog` abierto, la retirada de `vehicle_drive` y `drive_probe_client`, el empaquetado
  desde un export limpio y el resto de la ola.
- **Lo que la ola endureció por auditoría, no por petición:** la limpieza de la cola tras cancelar una petición y la
  propiedad del claim de la caja. Ahora el claim recuerda su ticket, solo se informa `box_claimed` a ese ticket, una
  liberación sin id no toca el ticket de otra petición viva de la misma sesión, y una espera termina en cuanto el
  puerto pedido lo ocupa un proceso ajeno.
- **Resto conocido y aceptado:** una liberación que no llegó a conocer su ticket no puede nombrar lo que deshace, así
  que el daemon lo deduce de lo que tiene la sesión; y la entrada `on_busy="fail"` no consulta el claim por ticket. Los
  dos se cierran con un marcador por petición en el wire, que es cambio propio porque toca el fichero que lo parsea.
- **Trampas vigentes al conducir el MCP:** un coche por run; `stop` antes de `release`; heartbeat en pausas de más de
  120 s (`d85b`); resellar el launcher si cambia un módulo empaquetado; y **reabrir el cliente MCP después de una
  promoción**, porque su catálogo de tools no se refresca al recargar el worker.

## Tickets

GitHub `willy92wins/dayz-mcp` (**público**: nada de rutas locales ni contenido del buzón en commits). El tracker real es el buzón (`pipeline_inbox` / `pipeline_feedback` / `pipeline_resolve`) en `%LOCALAPPDATA%\DayZ_MCP\inbox\feedback.jsonl`, con ids `fb-AAAAMMDD-HHMMSS-xxxx` citados por sufijo.

- **Resueltas al verificar #57:** `bcd8`, `ba70`, `7ad1`, `81f3` y `de68`. Puntero local de evidencia, sin versionar: `reviews/post57-2026-09-15/EVIDENCE.md`.
- **Con código ya en vivo, pendientes de cerrar en el buzón tras el próximo ciclo in-game:** `3fc1`/`dce1` y el C1 de
  `d85b` (verificados el 16 tras la promoción), la mitad de empaquetado de `63c9`, y `3bb4`, `f298`, `8604`/`2edd` y
  `2223`, que esperan las comprobaciones que quedaron sin hacer. Se cierran en una sola pasada, no a medias.
- **Abiertas con resto:** `f47b` (HOLD), `b0d9`, `1004`, `1025` (la guarda contra módulos empaquetados sin resellar),
  `e4be`, `88ef`, `305a`, `ba11`, `7ef2`, `dff2` y `6d18`.

## Próxima acción

1. **Con el dueño delante, en un solo ciclo corto y con un cliente MCP reabierto:** ESC cancelando el diálogo con
   teclas físicas (`3bb4`), `dayz_test_close` grácil con su línea de terminación por rol (`8604`), el ratón libre al
   aparecer la ventana (`f298`) y `on_busy="queue"` con dos sesiones (`2223`). Después, cerrar el buzón de una pasada.
2. **Sin juego:**
   - el marcador por petición en el wire, que cierra el resto de la cola de la caja;
   - `1004`: corregir la descripción, o que `object_delete` rechace el coche con ocupante de cliente;
   - la guarda de `1025`;
   - `e4be`, `88ef` y `305a`, los P2 3-5 de la review de `deb9`, `d85b` y `ba11`.
3. **`f47b`:** encontrar la causa del congelado y un detector que no dependa de la captura. El dueño lo confirma a la vista.
4. **Decisiones de dueño pendientes:** `8bc6`, PARO/PARK (`dae1`-1/2) y BUG-069.

## Invariantes CERRADAS — NO retocar / NO reabrir sin ángulo nuevo

- **v1.2 publicado** (2026-09-12 · `9f0343e` · sesión B3 `AI/30_Sessions/2026-09-12-dayzmcp-noche-b3-v11.md`)
- **Tramo jugable de tres bloques CERRADO** in-game: `0de3`+`5872`+`#4b`+`#6`+`9195`+`738a`+`CAMBIO` · PRs **#19–#25**
- **`84c4`** barrier mergeado (PR #25 → `6b6dd9e`)
- **`d50e` LEAVE_UNTRACKED** + resolved · evidencia `reviews/mcp-d50e-juicio-20260912/`
- **`world_time_set`:** `multiplier_applied=null` + `multiplier_unconfirmed` es el contrato final (D-69, #35).
- **Códigos de stop fijados por tests:** fila presente no activa → `run_not_active`; id desconocido → `run_not_found`. `run_retired` retirado (D-70).
- **Wire:** un texto persistido o de identidad solo sale en payloads públicos tras pasar una lista blanca de forma (sello UTC en `control_client`, token de generación en `process_lifecycle`). Un parser no es un filtro (D-70).
- **Retención de copias de manifest (`160e`):** se conservan las 200 más nuevas y las que nombra el puntero o un fault. No se borra nada si el puntero o un fault son ilegibles o si una entrada no se puede clasificar. La ventana TOCTOU del unlink por ruta es un límite aceptado (D-72, `e4be`).
- **`deb9` y `07a1`:** verificados in-game con el PBO `7DE421C5` (D-73).
- **`bcd8`, `ba70`, `7ad1` y `81f3`:** verificados in-game con el PBO `EB62B4E7` (D-74).
- **El árbol vivo solo avanza en una promoción controlada**, y el PBO entra con su Python, no después. El 16 alguien lo
  adelantó fuera de promoción y dejó Python nuevo contra un PBO viejo; la promoción 5 lo realineó. Para trabajar, un
  worktree desechable.
- **`3fc1` verificado in-game con el PBO `1E79BF80`:** `action_use` arranca `ActionDrink` con `target="hands"` sobre el
  objeto en manos y con `target="self"`, y el eco del target coincide. El censo de capacidades del cliente es la prueba
  de qué PBO está cargado.

## Punteros (detalle)

- Decisiones D-69 a D-74: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\decisions\decision-log.md`
- Evidencia de la Ola 1 y de la segunda promoción: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-14-ola1\`
- Evidencia de la 160e, las delegables y la tercera promoción: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-14-delegables\`
- Evidencia de la Ola 2 (trazas, canario, logs de `f47b`, scripts y manifiesto de capturas): `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-15-ola2\`
- Evidencia de la verificación de #57 (traza, logs, procedencia de los dos empaquetados, launcher y sonda de `f298`): `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-15-post57\`
- Sesiones: `C:\Users\guill\ObsidianVault\AI\30_Sessions\2026-09-15-dayzmcp-ola2.md` y `C:\Users\guill\ObsidianVault\AI\30_Sessions\2026-09-15-dayzmcp-post57.md`
- Runbook de promoción a vivo: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-14-delegables\promote3\RUNBOOK.md`
- Evidencia del pleno (una carpeta por ficha, gates, auditorías, reviews y la promoción 5, con manifiesto sha256):
  `ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-15-pleno-tickets\`
- Punto de entrada para retomarlo: `ObsidianVault\AI\30_Sessions\2026-09-16-HANDOFF-pleno-receptor.md`
- Histórico pre-v1.2: [`HANDOFF-ARCHIVE.md`](HANDOFF-ARCHIVE.md)
- `NEXT-SESSION-PROMPT.txt` es de **22-ago** y está **obsoleto**. No usarlo.

**Gate de arranque:** `Retomo DayZ-MCP desde: Ola A promocionada (main 1737dc5, daemon c7ee586e, PBO 1E79BF80 desde ese commit) · próxima acción: reabrir el cliente MCP y un ciclo corto para ESC, dayz_test_close, f298 y la cola con dos sesiones; luego cerrar el buzón de una pasada`
<!-- LIVE-STATE:END -->

---

## Árboles: `main` público vs leftovers locales

| Árbol | Qué es | Estado 2026-09-12 |
|---|---|---|
| `P:\DayZ_MCP` | Addon compilable (`$PBOPREFIX$=DayZ_MCP`). **Sin `.git`.** | Bytes del bridge alineados con **`main`**. |
| `P:\DayZ_MCP_dev` | Repo de producto (Python MCP, plans, reviews, este HANDOFF). `addon/` es la copia git del bridge. | Git `https://github.com/willy92wins/dayz-mcp.git`. HEAD local = `main` (tracking `origin/main`, ff desde inbox `6de5d98` = PR #17). **Inbox no mergeada.** `HANDOFF.md` entra en este commit. Untracked leftovers (backups, dumps de reviews, `NEXT-SESSION-PROMPT.txt`) se conservan y no se publican. |
| `…\!Workshop\@DayZ_MCP\Addons\DayZ_MCP.pbo` | PBO desplegado | SHA-256 `1E79BF80EADE48C98BB318A96C7F4ECF73F8782EC3AD3DDD08045B7751F98C9B` (2026-09-16, desde `1737dc5`) |
| `C:\Users\guill\Repos\dayz-mcp` | Otro clone | Rancio. No usarlo como checkout. Rama local `fichas/hands-watchdog` (**13c, no está en main**). |

Empaquetar desde `DayZ_MCP` o desde `DayZ_MCP_dev\addon` en este checkout pilla el bridge de `main`.

Las ramas de trabajo ya fusionadas se retiraron el 2026-09-16: el remoto se queda solo con `main`, y en local sobreviven las que sujeta un worktree vivo y tres con commits sin fusionar. Ningún commit se pierde —todos siguen alcanzables desde `main` y desde sus PR—, y el registro con nombre y sha de cada una queda fuera del repo, junto a la evidencia de la ola. El vault sigue con los D1-1/D1-4 del 10-sep; no son un plan activo.

## Cola aparcada (PARK / PARO)

Ninguna de estas fichas está en implementación.

| Marca | Fichas | Por qué no se tocan |
|---|---|---|
| **PARK** | `0ab2`, `546d`, `a429`, lote sellado (`2edd-1`, `dae1-1`) | Día + params del dueño + audit R9 (`0ab2`); no son trabajo de noche. |
| **PARO** | `3fc1`, `1025` | Parados a propósito. **No reabrir sin ángulo nuevo.** |
| **LEAVE_UNTRACKED** | `d50e` (`fb-20260907-232253-d50e`) | Juicio Sol 12-sep. La auditoría original no se promociona. |
| **fuera de main** | `fichas/hands-watchdog` | Local, 13 commits, no mergear por inercia. |

El buzón quedó en **66** abiertas tras W2 (2026-09-12). Esa cifra **no** es un encargo para re-resolver 95. Desglose de las 66: 20 re-enrute (W4, aún ABIERTAS), PARK/PARO intactos, residuales W9/W10. El plan de olas W1–WF **sí** está en vuelo (W1 = esta rama). `GATES.md` raíz del cierre integral 30-ago sigue con ROOT-* en `[ ]`: ledger no actualizado a v1.2.

## Planes

**Plan MCP en vuelo: olas W1–WF despachadas.**

- **W1 (esta rama):** documentación, tablas de cadencias, banners STALE **en raíz** (cuatro `AUDITORIA_*.md` de agosto) y D1–D4.
- **W2:** C-resolve JSONL **hecho** 2026-09-12 (29 ids; 95→66). No repetir.
- **W3:** tests.
- **W4:** grill `050e`/`0d65` + re-enrute de 20 fichas ajenas (no es W2).
- **W5:** occupancy (needs grill).
- Mapa general: Context `docs/mcp-end-to-end-plan.md` (no está en este repo).
- `2026-09-10-tres-bloques-backlog.md` (v2.1): tramo jugable **cerrado**. El resto de su universo está aparcado o encauzado.
- Playbooks en repo: `place_safely`, `lease_spawn_prepare_trace`, `box_is_mine`, `run_really_started`.

El buzón no se sustituye por Issues GitHub. PR #26 es leftover `546d` (W1 no la toca). Linear no existe para este producto.

## Superficie (no recontar a ciegas)

README / architecture / `build_app`: **62 tools** (+ `exec_enforce` opt-in). `CLAUDE.md` local alineado a 62 (sigue untracked). `CHANGELOG` [Unreleased] vacío; la superficie vive en [1.2]. Group G en `product-spec.md` sigue ❓ — parked, no es un plan abierto.

## Gotchas que siguen vigentes

- `MakeScreenshot` roto (T165276) → window-grab.
- `SetHeader` solo Content-Type → API-key en query string.
- `*_now` bloquea el tick.
- `SetTimeMultiplier(0)` congela la sim.
