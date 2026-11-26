# Pluvisky

The engine behind a Telegram bot that warns you about rain along your commute, using official forecasts and nowcast alerts from BMKG, Indonesia's national meteorological agency.

**Status:** v1 is in development. The database schema and queries are complete and tested; the Python service and the Telegram bot are not built yet.

## Features (v1)

- **Saved trips:** store named routes (e.g. "Commute to office") and start one with a single tap. Each trip session is monitored for 2 hours.
- **Scheduled reminders:** at a set time, the bot sends a forecast summary for the route together with your saved-trip buttons.
- **Route nowcast alerts:** BMKG early warnings whose area lies within 2 km of an active trip's route are pushed to Telegram.
- **Home alerts:** when no trip is active, alerts near your home are still sent, except during quiet hours (default 22:00–05:30 WIB).
- **No duplicates:** an alert that affects both your home and your route is sent only once.

## How it works

```
BMKG forecast (per village, hourly) ─────► forecast ──────┐
                                                          ├──► summary / matching ──► notification ──► Telegram
BMKG nowcast (RSS + CAP, every 2 min) ──► nowcast_alert ──┘          ▲
                                                                     │
                                          saved_trip + trip_session (your routes & sessions)
```

1. Each route is stored as a `LineString`. The villages it passes through are derived automatically by sampling a point every 3 km and matching it against village boundaries.
2. Forecasts are fetched by village code (BMKG `adm4`) for every village on a saved route, plus the home village.
3. The polygons of each nowcast alert are merged with `ST_Union`, and PostGIS computes their distance to active routes and to home.
4. Every match within 10 km is logged in `nowcast_match`. Only matches within 2 km are sent; the rest are kept to tune the buffer later.

## Tech stack

- PostgreSQL 17 with PostGIS 3
- Python 3.12, managed with [uv](https://docs.astral.sh/uv/)
- Telegram Bot API

## Data sources and disclaimer

- Weather data is provided by **BMKG** (Badan Meteorologi, Klimatologi, dan Geofisika) through its public weather forecast API and its Common Alerting Protocol (CAP) early-warning feed.
- This project is **not affiliated with or endorsed by BMKG**. For official information, use the Info BMKG app.
- **No alert does not mean safe conditions.** BMKG nowcasts are issued only for potentially severe weather.

## Contributing

Do not push changes directly to `main`. Every change, including small fixes, goes through an issue and a merge request:

1. **Open an issue** describing the bug or the proposed change before writing code.
2. **Create a branch** from `main` for that issue, e.g. `fix/12-duplicate-alerts` or `feat/15-quiet-hours`.
3. **Open a merge request** into `main` and reference the issue (e.g. `Closes #12`) so it is closed on merge.
4. **Merge only after review.** Wait for the merge request to be reviewed and approved before merging.
