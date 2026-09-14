# HANDOFF — DayZ-MCP

<!-- LIVE-STATE:START -->
# DayZ-MCP — Estado vivo · snapshot 2026-09-14 (tras la tercera promoción)

**Última verificación real:** 2026-09-14 22:28.
- **Árbol vivo `P:\DayZ_MCP_dev`:** `main` en `9a44ef9`. Fast-forward a `346e3ad` (PRs #51–#53) a las 22:15 y a `9a44ef9` (#54, solo Enforce y tests, sin efecto en el daemon) hacia las 22:27.
- **Daemon:** reiniciado a las 22:15 con el argv canónico. Generación `00b35adf…`, `daemon_modules.stale=[]`, caja vacía.
- **Suite sobre el árbol de `346e3ad`:** `Ran 3715 tests`, 0 rojos. Es la del regate de la ronda 4 de la `160e`; `git diff --quiet 11e1ef8 346e3ad` confirma que el árbol es el mismo.
- **PBO desplegado:** `F77AAC3E…`, idéntico a `1bad174` en sus 13 entradas. #44 y #54 cambian Enforce y **están sin empaquetar**. El build espera a que la caja quede libre: a las 22:21 `@LFPowerGrid` lanzó el run `5c6139b9`, que figura RUNNING_IDLE sin dueño y mantiene bloqueado el PBO.

bugs: tracker = buzón `pipeline_inbox` · **21** abiertas (censo 2026-09-14 22:22: 22 + 3 nuevas, `305a`, `88ef` y `e4be`, − 4 resueltas, `160e`, `6553`, `0e4c` y `5dbe`) · toque 2026-09-14
ciclos_en_este_objetivo: 1 (triaje del buzón + promoción + Ola 1 + segunda promoción + 160e y delegables + tercera promoción)

## Estado actual

- **Tercera promoción en vivo desde las 22:15:**
  - **#51** `6553`: el test del writer de audit es hermético (solo tests).
  - **#52** `0e4c`: el doctor publica `DAEMON_STATUS_OK` (INFO) cuando comprueba el daemon sin hallazgos.
  - **#53** `160e`: retención de las copias de manifest. Se conservan las 200 más nuevas y las que nombran el puntero o un fault; la poda hace como mucho 128 intentos por checkpoint, bajo el lock del store. Añade el WARN `MANIFEST_BACKUP_RETENTION_STALLED`.
- **Doctor tras la tercera promoción** (`--daemon-policy normal`): `ok=true` y 0 FAIL.
  - `DAEMON_STATUS_OK` presente.
  - WARN `MANIFEST_BACKUP_RETENTION_STALLED`: 8684 copias. Seguirá mientras el backlog pase de 400, unos 68 checkpoints.
  - WARN `KNOWLEDGE_PACK_MISSING`.
- **Archivo previo a la poda:** `%LOCALAPPDATA%\DayZ_MCP\_preprune-archive\20260914\` guarda los 10 slots y un tar.xz con índice de las 8812 copias.
- **Clientes MCP abiertos antes de las 22:15:** su registro de tools está stale. `server_reload` lo refresca y conserva el lease (verificado, `5dbe`). Se avisó a las tres sesiones abiertas.
- **Ola 1 (#44–#49)** sigue en vivo desde la segunda promoción. #44 (`deb9` + `07a1`) está sin empaquetar, y **#54** (`9a44ef9`) le corrige los P2 1-2 de Enforce: el sello del settle empieza en -1.0, se reinicia en cada drive y un reloj que retrocede no lo bloquea. Review Codex: APROBAR, con dos P2 aceptados.

## Tickets

GitHub `willy92wins/dayz-mcp` (**público**: nada de rutas locales ni contenido del buzón en commits). El tracker real es el buzón (`pipeline_inbox` / `pipeline_feedback` / `pipeline_resolve`) en `%LOCALAPPDATA%\DayZ_MCP\inbox\feedback.jsonl`, con ids `fb-AAAAMMDD-HHMMSS-xxxx` citados por sufijo.

- **Resueltas tras la tercera promoción:**
  - `160e`, `6553` y `0e4c`. Puntero local de evidencia, sin versionar: `reviews/delegables-2026-09-14/EVIDENCE.md`.
  - `5dbe`: el reciclo con lease vivo, verificado en vivo.
- **`c261`:** con seguimiento añadido. El runbook de sesión ya nombra `server_reload`; falta observar la recuperación desde un rechazo untrusted real.
- **Cerrar tras G7 in-game:** `deb9`, `07a1`.
- **Nuevas sin resolver:**
  - `e4be`: borrar relativo a un handle (ctypes) para cerrar la ventana TOCTOU de la poda.
  - `88ef`: en Windows, un lector con un fichero de runtime abierto hace fallar el `os.replace` atómico del daemon (medido, winerror 5).
  - `305a`: un `manifest.bin` truncado por un crash hace fallar `create_manifest_backup` y bloquea el arranque.
- **Abiertas con resto:**
  - `7ef2`: rastro de runs huérfanos en `session_status`.
  - `dff2`: runbook y causa real de la muerte.
  - `6d18`: decisión sobre captura por motor (MakeScreenshot roto, T165276).

## Próxima acción

1. **Ola 2 in-game con el dueño.** Checklist en `reviews/2026-09-14-delegables/OLA2-CHECKLIST.md` del vault.
   - Esperar a que la caja quede libre. El run `5c6139b9` de `@LFPowerGrid` bloquea el PBO; se pidió a `lfpowergrid-dev-51` que avise cuando lo pare.
   - Sincronizar con `deploy-addon.ps1` y empaquetar con `pack-addon.ps1 -Clear`. La fuente por defecto, `P:\DayZ_MCP`, está desfasada. Después, `pbo_provenance.py`.
   - G7 de `deb9`/`07a1` con `CT_Sedan_P0` de `@LFCarTune`, que tiene caja manual.
   - Resto de la sesión: G3, BUG-040, `b1ff` I1, time/weather, `3bb4`, BUG-083, `f298`, `f47b` y el canario de BUG-096. BUG-069 queda aparcado como decisión.
2. **Sin juego:** `e4be`, `88ef` y `305a`, y los P2 3-5 de la review de `deb9` (tests Python).
3. **Decisiones de dueño pendientes:** modelo de cola `2223`, parada ordenada `8604`, `8bc6`, PARO/PARK (`3fc1`/`dce1`/`1025`, `2edd`-1, `dae1`-1/2).

## Invariantes CERRADAS — NO retocar / NO reabrir sin ángulo nuevo

- **v1.2 publicado** (2026-09-12 · `9f0343e` · sesión B3 `AI/30_Sessions/2026-09-12-dayzmcp-noche-b3-v11.md`)
- **Tramo jugable de tres bloques CERRADO** in-game: `0de3`+`5872`+`#4b`+`#6`+`9195`+`738a`+`CAMBIO` · PRs **#19–#25**
- **`84c4`** barrier mergeado (PR #25 → `6b6dd9e`)
- **`d50e` LEAVE_UNTRACKED** + resolved · evidencia `reviews/mcp-d50e-juicio-20260912/`
- **`world_time_set`:** `multiplier_applied=null` + `multiplier_unconfirmed` es el contrato final (D-69, #35).
- **Códigos de stop fijados por tests:** fila presente no activa → `run_not_active`; id desconocido → `run_not_found`. `run_retired` retirado (D-70).
- **Wire:** un texto persistido o de identidad solo sale en payloads públicos tras pasar una lista blanca de forma (sello UTC en `control_client`, token de generación en `process_lifecycle`). Un parser no es un filtro (D-70).
- **Retención de copias de manifest (`160e`):** se conservan las 200 más nuevas y las que nombra el puntero o un fault. No se borra nada si el puntero o un fault son ilegibles o si una entrada no se puede clasificar. La ventana TOCTOU del unlink por ruta es un límite aceptado (D-72, `e4be`).

## Punteros (detalle)

- Decisiones D-69 a D-72: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\decisions\decision-log.md`
- Evidencia de la Ola 1 y de la segunda promoción: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-14-ola1\`
- Evidencia de la 160e, las delegables y la tercera promoción (ledgers, reverify, reviews, archivo operativo, checklist de la Ola 2): `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-14-delegables\`
- Sesiones: `C:\Users\guill\ObsidianVault\AI\30_Sessions\2026-09-14-dayzmcp-segunda-promocion.md` y `C:\Users\guill\ObsidianVault\AI\30_Sessions\2026-09-14-dayzmcp-tercera-promocion.md`
- Runbook de promoción a vivo: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-14-delegables\promote3\RUNBOOK.md`
- Histórico pre-v1.2: [`HANDOFF-ARCHIVE.md`](HANDOFF-ARCHIVE.md)
- `NEXT-SESSION-PROMPT.txt` es de **22-ago** y está **obsoleto**. No usarlo.

**Gate de arranque:** `Retomo DayZ-MCP desde: tercera promoción EN VIVO (#51–#53, generación 00b35adf) · 21 fichas abiertas · próxima acción: caja libre → build del PBO con #44 y #54 → Ola 2 in-game`
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
