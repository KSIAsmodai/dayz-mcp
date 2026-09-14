# HANDOFF — DayZ-MCP

<!-- LIVE-STATE:START -->
# DayZ-MCP — Estado vivo · snapshot 2026-09-14

**Última verificación real:** 2026-09-14.
- **Promoción:** `main` `1bad174` pasó al árbol vivo `P:\DayZ_MCP_dev` y el daemon se reinició (generación `eca81d26…`, `daemon_modules.stale=[]`, caja vacía).
- **Ola 1:** mergeada en `main` como PRs #44–#48; **aún no está en el árbol vivo**.
- **PBO desplegado:** `F77AAC3E…`, idéntico a `main` @ `1bad174` en sus 13 entradas. #44 cambia Enforce (`MCP_CarScript.c`, `MCPClientBridge.c`) **sin empaquetar**.

bugs: tracker = buzón `pipeline_inbox` · **25** abiertas (censo 2026-09-14: 22 tras cerrar A2, más las nuevas `4554`, `160e` y `6553`) · toque 2026-09-14
ciclos_en_este_objetivo: 1 (triaje del buzón + promoción + Ola 1)

## Estado actual

- **Tip `main` = `ad2fafb` (merge de #48).** El árbol vivo sigue en `1bad174`: lo mergeado en #44–#48 **no sirve** hasta una segunda promoción. Esa promoción requiere caja vacía, `git merge --ff-only` en `P:`, reinicio del daemon y avisar a las sesiones abiertas para que reabran su cliente.
- **Buzón triado** el 2026-09-14 (`reviews/triage-20260914-agy/RESUMEN.md`, sin versionar). 34 cerradas en triaje y las 3 A2 (`2c43`, `b1ff`, `14de`) tras la promoción.
- **Ola 1**, por lanes Grok 4.6/Cursor en worktrees, con gates-ledger y review Codex `gpt-5.6-sol`:
  - **#44** `deb9` + `07a1`: settle de ShiftUp y get-in al coche más cercano. Enforce offline; queda G7 in-game.
  - **#45** `6d18` + `c12b`: `session_locked` en captura y nota de 20 fps sin foco.
  - **#46** `050e` + `145c`: fecha del registro en el rechazo untrusted (lista blanca de sello UTC); aviso `caller_tool_registry_stale` en `dayz_test_run`.
  - **#47** `7ef2` + `dff2`: generación del daemon cableada al lifecycle; filtro de token para generaciones en el wire; `session_release` documentado.
  - **#48** `4554`: el doctor vuelve a parsear `--supervised`/`--exec-audit-path` y a comprobar el daemon.
- **Doctor tras la promoción:** FAIL por dos causas previas a ella (D-70). Una la arregla #48; la otra es la ficha `160e`.

## Tickets

GitHub `willy92wins/dayz-mcp` (**público**: nada de rutas locales ni contenido del buzón en commits). El tracker real es el buzón (`pipeline_inbox` / `pipeline_feedback` / `pipeline_resolve`) en `%LOCALAPPDATA%\DayZ_MCP\inbox\feedback.jsonl`, con ids `fb-AAAAMMDD-HHMMSS-xxxx` citados por sufijo.

- **Cerrar tras la segunda promoción:** `050e`, `145c`, `c12b`, `4554`.
- **Cerrar tras G7 in-game:** `deb9`, `07a1`.
- **Nueva sin resolver:** `6553`, test inestable del writer de audit. El hilo con budget compite con `rmtree` y puede poner rojo un G3 sin regresión real; hay que hacerlo hermético.
- **Abiertas con resto:**
  - `7ef2`: rastro de runs huérfanos en `session_status`.
  - `dff2`: runbook y causa real de la muerte.
  - `6d18`: decisión sobre captura por motor (MakeScreenshot roto, T165276).

## Próxima acción

1. **Dueño:** decidir la segunda promoción (Ola 1 a vivo) y ejecutarla con la caja vacía. Después, `pipeline_resolve` de las cuatro fichas de arriba, y `doctor` para verificar que ya no sale CONFIG_UNREADABLE.
2. **Dueño, ficha `160e`:** archivar los 10 slots `runs.json.bak-preprune*` (precedente `_preprune-archive\20260816\`) y fijar retención para `lifecycle-recovery-faults\backups` (8766 copias, 1,1 GB).
3. **Ola 2 in-game con el dueño:**
   - build del PBO con #44 y G7 de `deb9`/`07a1`, más sus 5 P2 de review;
   - WF §6: G3 GREEN, freecam→get-in / BUG-040, `b1ff` I1, time/weather, BUG-069/083/113/096;
   - B3 #6: `c261`, `3bb4`, `5dbe`, `1f21`;
   - `f298` y `f47b`.
4. **Decisiones de dueño pendientes:** modelo de cola `2223`, parada ordenada `8604`, `8bc6`, PARO/PARK (`3fc1`/`dce1`/`1025`, `2edd`-1, `dae1`-1/2).

## Invariantes CERRADAS — NO retocar / NO reabrir sin ángulo nuevo

- **v1.2 publicado** (2026-09-12 · `9f0343e` · sesión B3 `AI/30_Sessions/2026-09-12-dayzmcp-noche-b3-v11.md`)
- **Tramo jugable de tres bloques CERRADO** in-game: `0de3`+`5872`+`#4b`+`#6`+`9195`+`738a`+`CAMBIO` · PRs **#19–#25**
- **`84c4`** barrier mergeado (PR #25 → `6b6dd9e`)
- **`d50e` LEAVE_UNTRACKED** + resolved · evidencia `reviews/mcp-d50e-juicio-20260912/`
- **`world_time_set`:** `multiplier_applied=null` + `multiplier_unconfirmed` es el contrato final (D-69, #35).
- **Códigos de stop fijados por tests:** fila presente no activa → `run_not_active`; id desconocido → `run_not_found`. `run_retired` retirado (D-70).
- **Wire:** un texto persistido o de identidad solo sale en payloads públicos tras pasar una lista blanca de forma (sello UTC en `control_client`, token de generación en `process_lifecycle`). Un parser no es un filtro (D-70).

## Punteros (detalle)

- Decisiones D-69 y D-70: `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\decisions\decision-log.md`
- Evidencia de la Ola 1 (ledgers, reverify, reviews, briefs): `C:\Users\guill\ObsidianVault\AI\10_Projects\DayZ_MCP\reviews\2026-09-14-ola1\`
- Sesión: `C:\Users\guill\ObsidianVault\AI\30_Sessions\2026-09-14-dayzmcp-triaje-promocion-ola1.md`
- Histórico pre-v1.2: [`HANDOFF-ARCHIVE.md`](HANDOFF-ARCHIVE.md)
- `NEXT-SESSION-PROMPT.txt` es de **22-ago** y está **obsoleto**. No usarlo.

**Gate de arranque:** `Retomo DayZ-MCP desde: Ola 1 mergeada (#44–#48) pero NO promovida · árbol vivo 1bad174 · 25 fichas abiertas · próxima acción: decisión de segunda promoción del dueño, luego resolve 050e/145c/c12b/4554 y Ola 2 in-game`
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
