# HANDOFF — DayZ-MCP

<!-- LIVE-STATE:START -->
# DayZ-MCP — Estado vivo · snapshot 2026-09-15 (tras la Ola 2 in-game)

**Última verificación real:** 2026-09-15 03:47.
- **Árbol vivo `P:\DayZ_MCP_dev`:** `main` en `d4516cb` (#55). Sin cambios de código desde la tercera promoción.
- **Daemon:** generación `b612ae38…`. Un cliente lo relanzó a las 02:42, con el argv canónico, después de que se apagara por inactividad. `daemon_modules.stale=[]`. Caja vacía al cerrar.
- **PBO desplegado:** `7DE421C5…` (254098 B), empaquetado sin binarizar desde `addon/` en `d4516cb`. Sus 13 entradas son idénticas a `9a44ef9` (#44 y #54). Copia del anterior: `DayZ_MCP.pbo.bak_pre_ola2_20260915` (`F77AAC3E`).

bugs: tracker = buzón `pipeline_inbox` · **30** abiertas (censo 2026-09-15 03:50: 22 + 3 de otras sesiones + 7 nuevas − 2 resueltas, `deb9` y `07a1`) · toque 2026-09-15
ciclos_en_este_objetivo: 1 (triaje del buzón + promoción + Ola 1 + segunda promoción + 160e y delegables + tercera promoción + Ola 2)

## Estado actual

- **Ola 2 in-game hecha,** en cuatro runs, uno por coche (D-73):
  - **G7 de `deb9`, verde:** las subidas van separadas 3,85 s y no hay segunda subida dentro de la ventana de 0,3 s. Ficha resuelta.
  - **`07a1`, verde:** el get-in elige el coche más cercano a `pos`. Ficha resuelta.
  - **G3, verde en vivo con `CivilianSedan`:** 20 Hz, dueño y net id estables, readback 0,0 y contacto de carrocería. Faltan los criterios offline, como el bundle byte-idéntico.
  - **BUG-040, verde. BUG-113:** los cuatro lanzamientos fueron bien. **time/weather:** cambio visible y restaurado.
  - **`f47b`, reproducido y agravado:** `restore_gameplay` devuelve `ok` con el render congelado (`b0d9`).
  - **Canario de BUG-096, inconcluso:** solo hay una cuenta de Steam (`ba11`, reconfirma `e4cf`).
  - **`3bb4`:** `key_press(1)` sin menú abierto no abre nada; cerrar un menú sigue sin probar.
  - **`b1ff` I1:** sin receta vanilla. **`f298`:** sin confirmación del dueño. **BUG-083:** sin repro. **BUG-069:** aparcado.
- **Trampas medidas al conducir el MCP:**
  - `vehicle_release` antes de `vehicle_trace(stop)` tira la traza (`7ad1`). Primero `stop`, en otra llamada.
  - Tras `vehicle_get_in_client` no hay forma de bajar del coche, y `player_teleport` con el jugador sentado desincroniza cliente y servidor (`81f3`). Un coche por run.
  - El lease caduca en pausas de más de 120 s (`d85b`, parecida a `8d68`). Hay que usar `session_heartbeat`.
  - `capture_screenshot` falla con el `PSModulePath` heredado (`ba70`). Capturar con `env -u PSModulePath`.
  - `pack-addon.ps1` muere si algún `config.cpp` bajo `P:\` no parsea (`bcd8`). Empaquetar con `-packonly` desde `addon/`.

## Tickets

GitHub `willy92wins/dayz-mcp` (**público**: nada de rutas locales ni contenido del buzón en commits). El tracker real es el buzón (`pipeline_inbox` / `pipeline_feedback` / `pipeline_resolve`) en `%LOCALAPPDATA%\DayZ_MCP\inbox\feedback.jsonl`, con ids `fb-AAAAMMDD-HHMMSS-xxxx` citados por sufijo.

- **Resueltas en la Ola 2:** `deb9` y `07a1`. Puntero local de evidencia, sin versionar: `reviews/ola2-2026-09-15/EVIDENCE.md`.
- **Nuevas en la Ola 2:**
  - `bcd8`: `pack-addon.ps1` y binarize;
  - `ba70`: captura y `PSModulePath`;
  - `b0d9`: el falso verde de `f47b`;
  - `81f3`: teletransporte con el jugador sentado;
  - `7ad1`: `release` tira la traza;
  - `d85b`: lease en pausas;
  - `ba11`: canario.
- **Abiertas con resto:**
  - `f47b` y `f298`;
  - `3bb4`;
  - `c261`: falta observar la recuperación desde un rechazo untrusted;
  - `e4be`, `88ef` y `305a`;
  - `7ef2`, `dff2` y `6d18`.

## Próxima acción

1. **Sin juego:**
   - `pack-addon.ps1` con `-packonly` para addons sin assets binarizables (`bcd8`);
   - `mcp_capture` sin `PSModulePath` (`ba70`);
   - autodump en el `Abort` de la traza (`7ad1`);
   - `player_teleport` sin desincronizar (`81f3`);
   - `e4be`, `88ef` y `305a`, y los P2 3-5 de la review de `deb9`.
2. **`f47b`:** encontrar la causa del congelado y un detector que no dependa de la captura. El dueño lo confirma a la vista.
3. **Con el dueño delante:** `f298` (el ratón al entrar).
4. **Decisiones de dueño pendientes:** modelo de cola `2223`, parada ordenada `8604`, `8bc6`, PARO/PARK (`3fc1`/`dce1`/`1025`, `2edd`-1, `dae1`-1/2) y BUG-069.

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

## Punteros (detalle)

- Decisiones D-69 a D-73: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\decisions\decision-log.md`
- Evidencia de la Ola 1 y de la segunda promoción: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-14-ola1\`
- Evidencia de la 160e, las delegables y la tercera promoción: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-14-delegables\`
- Evidencia de la Ola 2 (trazas, canario, logs de `f47b`, scripts y manifiesto de capturas): `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-15-ola2\`
- Sesiones: `C:\Users\guill\ObsidianVault\AI\30_Sessions\2026-09-14-dayzmcp-tercera-promocion.md` y `C:\Users\guill\ObsidianVault\AI\30_Sessions\2026-09-15-dayzmcp-ola2.md`
- Runbook de promoción a vivo: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-14-delegables\promote3\RUNBOOK.md`
- Histórico pre-v1.2: [`HANDOFF-ARCHIVE.md`](HANDOFF-ARCHIVE.md)
- `NEXT-SESSION-PROMPT.txt` es de **22-ago** y está **obsoleto**. No usarlo.

**Gate de arranque:** `Retomo DayZ-MCP desde: Ola 2 in-game HECHA (deb9/07a1 verificados, G3 verde, f47b reproducido; PBO 7DE421C5) · 30 fichas abiertas · próxima acción: fixes sin juego (bcd8, ba70, 7ad1, 81f3) y f47b`
<!-- LIVE-STATE:END -->

---

## Árboles: `main` público vs leftovers locales

| Árbol | Qué es | Estado 2026-09-12 |
|---|---|---|
| `P:\DayZ_MCP` | Addon compilable (`$PBOPREFIX$=DayZ_MCP`). **Sin `.git`.** | Bytes del bridge alineados con **`main`**. |
| `P:\DayZ_MCP_dev` | Repo de producto (Python MCP, plans, reviews, este HANDOFF). `addon/` es la copia git del bridge. | Git `https://github.com/willy92wins/dayz-mcp.git`. HEAD local = `main` (tracking `origin/main`, ff desde inbox `6de5d98` = PR #17). **Inbox no mergeada.** `HANDOFF.md` entra en este commit. Untracked leftovers (backups, dumps de reviews, `NEXT-SESSION-PROMPT.txt`) se conservan y no se publican. |
| `P:\Mods\@DayZ_MCP\Addons\DayZ_MCP.pbo` | PBO desplegado | SHA-256 `F82CFA8C4E557FFF0041661EC106DB6CF0ACA96C664515518DCC8459511E92AE` |
| `C:\Users\guill\Repos\dayz-mcp` | Otro clone | Rancio. No usarlo como checkout. Rama local `fichas/hands-watchdog` (**13c, no está en main**). |

Empaquetar desde `DayZ_MCP` o desde `DayZ_MCP_dev\addon` en este checkout pilla el bridge de `main`.

La rama `work/inbox-20260830-modules` @ `6de5d98` sigue en local/remoto, 22 commits detrás; no usarla como checkout. El vault sigue con los D1-1/D1-4 del 10-sep; no son un plan activo.

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
