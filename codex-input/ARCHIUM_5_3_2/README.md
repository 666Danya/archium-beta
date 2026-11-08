# ARCHIUM 5.3.2 — Codex input snapshot

This branch preserves the **exact standalone ARCHIUM 5.3.2 HTML** as 11 source chunks, avoiding the GitHub connector's maximum request size. It is **not** a new production deployment.

## Restore the original 5.3.2 HTML

From the repository root:

```sh
python3 codex-input/ARCHIUM_5_3_2/reconstruct.py
```

Output: `codex-input/ARCHIUM_5_3_2/ARCHIUM_5_3_2_IPHONE_BUTTON_FIX_FULL.html`.

Expected SHA256: `425af8dc18e02a89d137920b24d76d98be2920526e2289677d9e74f0d9aa5cdb`. Do not edit the chunks; work with the reconstructed file and organize a maintainable site structure.

## Codex task

Investigate and repair the broken buttons on iPhone, especially the mandatory legal notice confirmation button. Verify real-world limitations of opening HTML via `file://` / iOS embedded preview versus a proper HTTPS web server.

Check:
- Mandatory disclaimer is shown at every site opening and can be dismissed.
- First visit offers **manual choice of 8 guides**, persist choice locally, change guide via settings. Never assign automatically by faction.
- Navigation, all dossiers, media, search and filters, eight PDA themes, rank/reputation/achievements and profile remain intact.
- Visit counter increments at most once per 30-minute session, has graceful error behavior, no fake real stats.
- Navigation and tap/click handlers work on touch/mobile browsers; no stuck overlays, pointer-events or z-index blocking.
- Mobile widths 320/375/390/430 px and desktop, including reduced motion; avoid horizontal overflow and huge first-render costs.
- Add reproducible browser test coverage, preferably Playwright + WebKit, and document test execution.

Important: the live `main` branch still contains an older site version. Do **not** publish or modify `main`, merge, add paid services, or deploy without explicit owner approval. Make a separate feature branch / draft PR for review.

Project legal context: ARCHIUM is an independent, unofficial S.T.A.L.K.E.R. fan site, not affiliated with GSC Game World. «Проект Горизонт» is a separate original game/universe.
