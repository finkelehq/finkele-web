# Finkele – Climate Intelligence Platform

**[www.finkele.com](https://www.finkele.com)**

![Finkele Logo](public/assets/img/finkele-logo-square.png)

## Overview

Finkele is a Climate Risk Intelligence Platform that combines ESG analytics, real-time flood monitoring, and climate dashboards to help organizations build resilience in a changing world.

The platform is composed of a static landing site on GitHub Pages and three independent micro-services on Google Cloud Run.

---

## Architecture

```
finkele.com  (GitHub Pages)
├── index.html          ← landing page
├── alert.html          ← iframe → finkele-alert
├── climate.html        ← iframe → finkele-climate
└── floodmap.html       ← iframe → finkele-floodmap
```

| Service | URL | Stack | Repo |
|---------|-----|-------|------|
| **finkele-alert** | https://finkele-alert-328632529722.europe-west9.run.app | FastAPI · Python | [finkelehq/finkele-alert](https://github.com/finkelehq/finkele-alert) |
| **finkele-climate** | https://finkele-climate-328632529722.europe-west9.run.app | Nginx · Static | [finkelehq/finkele-climate](https://github.com/finkelehq/finkele-climate) |
| **finkele-floodmap** | https://finkele-floodmap-328632529722.europe-west9.run.app | Nginx · Folium | [finkelehq/finkele-floodmap](https://github.com/finkelehq/finkele-floodmap) |

All Cloud Run services are deployed to **europe-west9** in the **finkele-flood** GCP project via GitHub Actions CI/CD.

---

## Services

### 🚨 Flood Alert (`finkele-alert`)
Live flood warnings, river gauge levels, and rainfall forecasts across England & Scotland. Polls the Environment Agency and SEPA APIs every 5 minutes via Cloud Scheduler.

- **Stack:** FastAPI, uvicorn, SQLite, httpx
- **Data sources:** EA Flood Warnings, EA Gauges, SEPA Gauges, Open-Meteo Rainfall
- **Scheduling:** Cloud Scheduler → `GET /cron/poll` every 5 min
- **Config:** CPU throttling enabled, scale-to-zero (`min-instances=0`)

### 🌡️ Climate Dashboard (`finkele-climate`)
Interactive climate risk intelligence dashboard with global metrics, trend charts, heat maps, and AI-driven predictions.

- **Stack:** Nginx, Chart.js, D3.js
- **Content:** Static HTML/CSS/JS dashboard

### 🗺️ Flood Risk Map (`finkele-floodmap`)
Interactive multi-region flood depth map with return periods from 10 to 500 years. Features collapsible region layers, multiple basemap options, and risk score overlays.

- **Stack:** Nginx, Folium/Leaflet
- **Content:** Pre-generated interactive map with GeoTIFF-derived flood overlays

---

## Local Development

```bash
# Serve the landing site locally
npm install
npm start          # → http://localhost:8080
```

---

## Deployment

### Landing site (GitHub Pages)
Pushes to `main` trigger the GitHub Actions workflow which deploys the `public/` directory to the `gh-pages` branch.

### Cloud Run services
Each service repo has its own `.github/workflows/deploy.yml`:
1. Authenticate to GCP with `google-github-actions/auth@v2`
2. Build container with Cloud Build
3. Deploy to Cloud Run

---

## Features

- 🌡️ **Real-time Climate Monitoring** – Live data from EA, SEPA, and Open-Meteo
- 🚨 **Flood Alert System** – ~3,400 gauge stations, 5-min refresh
- 🗺️ **Interactive Flood Maps** – Multi-region depth analysis (10–500 yr return periods)
- 📊 **ESG Analytics Dashboard** – Environmental risk metrics and trend analysis
- 🌍 **UK-wide Coverage** – England & Scotland flood monitoring
- ⚡ **Cost-optimised** – Scale-to-zero, CPU throttling, Cloud Scheduler

---

## License

See [LICENSE](LICENSE) for details.