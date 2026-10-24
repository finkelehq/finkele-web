# finkele-web

The source of the Finkele website, **[www.finkele.com](https://www.finkele.com)**, a static site
served by GitHub Pages.

![Finkele Logo](public/assets/img/finkele-logo-square.png)

Finkele Ltd builds TERRA, a machine-learning model of flood inundation trained on physics-based
solver runs, and AXIOM, a protocol for checking machine-learning surrogates in engineering
simulation. The platform itself is a separate, private service; this repository holds only the
public website.

## Layout

```
public/
├── index.html      landing page
├── climate.html    embeds the climate dashboard (finkelehq/finkele-climate)
├── alert.html      legacy page, to be removed: its service was retired on 2026-10-24
├── floodmap.html   legacy page, to be removed: its service was deleted on 2026-10-23
├── assets/         CSS, JavaScript and images
└── CNAME           the custom domain, finkele.com
```

The retired flood alert dashboard's code is kept in `finkelehq/finkele-gauge-dashboard`, and
the name `finkele-alert` is reserved for a future alerting service.

## Local development

```bash
npm install
npm start          # serves public/ at http://localhost:8080
```

## Deployment

A push to `main` runs `.github/workflows/deploy.yml`, which publishes `public/` to the
`gh-pages` branch. GitHub Pages serves `gh-pages` at finkele.com, set in the repository's
Pages settings (source `gh-pages`, folder `/`, custom domain `finkele.com`, HTTPS enforced).

If `gh-pages` is ever deleted, GitHub switches Pages off and the site answers 404 even after the
workflow recreates the branch; turn Pages back on in the settings with the values above.

## Licence

Proprietary. Copyright (c) 2026 Finkele Ltd. All rights reserved; see [LICENSE](LICENSE).
The repository is public only so GitHub Pages can serve the site.
