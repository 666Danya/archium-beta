# ARCHIUM 5.7 — staging

This branch contains the new 5.7 HTML shell in `staging-5.7/index.html`, but the **complete site is not yet uploaded**. The 5.7 HTML refers to CSS, JavaScript and 368 WebP files from the prepared distribution ZIP; do not deploy this shell by itself.

To complete transfer, upload `ARCHIUM_5_7_SITE_PREVIEW.zip` (public distribution, ~12 MB) in the [`incoming` folder](../incoming/). The `archium57-import.yml` GitHub Actions workflow will extract the archive into the staging branch. The existing `main` and GitHub Pages site remain unchanged. Do not upload the full local-only admin project.
