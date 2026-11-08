# ARCHIUM 5.3.2 — iPhone button and navigation investigation

## Target source and staging
- Repository: `666Danya/archium-beta`
- **Required source version:** ARCHIUM **5.3.2 — IPHONE BUTTON FIX**
- Staging branch: `codex/archium-5.3.2-mobile-audit`
- Source package names: `ARCHIUM_5_3_2_IPHONE_BUTTON_FIX_WEB.zip` (preferred; ~371 files including images), `ARCHIUM_5_3_2_IPHONE_BUTTON_FIX_FULL.html` (single-file backup).
- **BLOCKER:** As of writing, the full 5.3.2 package has not yet been copied into this branch. The branch initially contains only this task file and earlier repository content. **Do not treat `main` as 5.3.2.** Wait for the package upload, or ask for the missing files. Do not “repair” only the older `main` release.

## User-visible bug
On iPhone, the button `Понятно, перейти в ARCHIUM` (dismiss legal notice) apparently does not respond in the user's actual opening workflow. Earlier patch 5.3.2 did not resolve the user's experience. Browser automation had succeeded, so investigate environment-specific failures rather than claiming it was solved. Another likely factor is opening a local .html using iOS Files / ChatGPT preview instead of a normal HTTPS browser tab.

## Tasks
1. Read and map full application startup/notice logic and all event handlers, including `click`, touch/pointer handlers, overlays, z-index and pointer-events.
2. Reproduce in browser with WebKit as closely as possible and Chrome mobile widths 320, 375, 390, 430; test HTTPS and `file://` constraints separately; log JS errors and console warnings.
3. Ensure legal notice can always close when JS is active and that navigation initializes reliably; include a clear user-facing warning if opened in a non-executing preview.
4. Test first-run onboarding and returning-user paths; choose guide, main menu, search, faction dossier navigation, theme switching, PDA profile, achievements and visit counter (without artificially incrementing public visits).
5. Check iOS-specific performance (large HTML / blocking scripts / image loading / excessive synchronous setup); fix real causes, preserve offline single-file build if possible.
6. Add repeatable regression tests. Document how to reproduce and what remains unverified on actual Safari/Yandex iOS.

## Preserve
- 3D vertical PDA style, existing art, original trilogy lore, eight guides, faction themes, dossier content, local profile and reputation, legal notice each visit, and current content.
- Keep `Проект Горизонт` as separate original game.
- No paid back end, third-party keys committed, public deployment, merging to `main`, or GitHub Pages changes without owner approval.

## Completion
Provide separate branch and reviewable draft PR, report cause(s), changed files and tests passed, unresolved device-specific caveats. Do not report success solely because desktop automation clicked the button.
