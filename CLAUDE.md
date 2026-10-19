# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# RoadWise

An app that tells you the best day to leave on a long South African road trip. You pick a route
(e.g. Pretoria → Polokwane) and a departure window (e.g. 10–20 Dec), and it predicts traffic for
every day in that window, compared with an average day on that route.

Owner: Werner. End goal is an Android app. V1/V2 are a single-file HTML prototype.

## Files

- `roadwise.html` – the current prototype (V3). Single self-contained HTML page, no build step.
  Open it in a browser. Also published as a claude.ai artifact:
  https://claude.ai/artifact/XEVE4ZoAiUv2CL7q8vTyV9
- `roadwise_test.py` – stdlib-only Python script that asks the TomTom Routing API for predicted
  travel times at 08:00 on 12 test trips and writes `roadwise_test_results.csv`.
  Run: `py roadwise_test.py` (reads the key from `key.txt` or prompts for it).
- `key.txt` – (create yourself) the TomTom API key, one line. Never commit it; it is in `.gitignore`.

No build, lint or test suite. To check a change, open `roadwise.html` in a browser. After editing it,
republish to the same artifact URL above so the link stays the same. The page's own footer note still
says "Version 2", so update it when the model changes.

## How `roadwise.html` is built

One `<script>` block, top to bottom:
- **Data tables**: `SRC` (citations, keyed by id), `ROUTES` keyed `"Gauteng city|Destination"`, each a
  tuple `[km, clear-road min, road, swing, swing note, swing source id]` (looked up in either order by
  `routeFor`), `HOLIDAYS` (ISO date → name), `SCHOOL` (close/open pairs), `WEEK_RAW` (normal week).
- **Direction**: `"out"` if the origin is in `GAUTENG`, otherwise `"in"`. All profiles are per direction.
- **Dates** are UTC millisecond timestamps (`parse`, `iso`, `DAY`). Always use `getUTC*` to avoid timezone bugs.
- **`forecast(t, dir, route)`** returns `{t, rel, f}`. `rel` is % of an average day (100 = average) and
  `f` is the list of factors shown in the breakdown. Each factor has `tag` `"rec"`/`"est"` and an
  optional `src` that points into `SRC`. Swapping in a data-backed model means replacing this function
  while keeping that return shape, because `render()` and the UI depend on it.
- **Derived display**: `level(rel)` gives the colour band, and `delayMin`/`delayText` turn `rel` into
  extra minutes (also hand-tuned).
- **`render()`** reads the controls, builds up to 31 days, and draws the window chart and the
  normal-week chart (both through `drawChart`), plus the day list and the breakdown.
- Styling uses CSS custom properties on `:root` with light/dark variants. Keep new colours as tokens.

`roadwise_test.py` hard-codes `PLACES` (coordinates) and `TESTS` (trip, date, note). To change the
experiment, edit those lists. It records TomTom's `travelTimeInSeconds`, `noTrafficTravelTimeInSeconds`
and `historicTrafficTravelTimeInSeconds` for each trip.

## Product decisions so far

- Core use case: holiday road trips (December, Easter). Find the day with the least traffic.
- User picks a date window (two dates), not a fixed week. Max 31 days shown.
- Bar chart at the top: one bar per day, dashed reference line = an average day on this route
  in this direction. Tap a bar to see that day's breakdown.
- Every day is shown as % above/below an average day ("Average" = 100%).
- Show the route's normal week too (e.g. Fridays out of Pretoria on the N1 north are busy because
  people leave the city for the weekend), not just holidays.
- Departure-time-of-day suggestions are a later feature.
- Live traffic is a later feature; for planning weeks ahead, historical patterns do the work.

## Hard requirement from Werner

**The predictions must be backed by real data, not hand-tuned multipliers.** The current model
in `roadwise.html` is still hand-tuned and must be replaced.

## Current model (to be replaced)

In `forecast()` inside `roadwise.html`:
- Normal week profile per direction (out of Gauteng / into Gauteng), Sun..Sat, normalised to mean
  100. **Estimate – no source.**
- Multiplicative factors: festive season (5 Dec–15 Jan), school-closing getaway wave, school-
  reopening return wave, eve of public holiday, long-weekend start/end, payday (25th, 15 Dec),
  last weekend before Christmas, 23 Dec, New Year return (2–3 Jan).
- Christmas Day (30%), Boxing Day (55%), New Year's Day (45%) override the pattern entirely.
- Route "swing" scales how far a day deviates from average (N12/N14 0.5, N1 north 0.9,
  N1 south 1.1, N3 1.25).
- Each factor is tagged "Records" (dates line up with published SANRAL/N3TC peak-day forecasts)
  or "Estimate". Records only confirm *which* days are busy, not *how much*.
- School dates are approximate (2026 Term 4 assumed to end 9 Dec, schools reopen 13 Jan 2027).

## Data research so far

- No public day-of-week traffic counts found for these routes.
- SANRAL CTO yearbook station reports (e.g. 2019 N12 Delmas) give annual ADT, truck %, speeds,
  and the busiest *hours* of the year with dates – but no day-of-week or daily series.
  The hourly data behind them exists at SANRAL's permanent count stations; would need a request.
- SANRAL / N3TC publish festive & Easter peak-day forecasts, but qualitatively
  ("busy", "very busy"), not counts. N3 peaks quoted at ~1,500–3,500 vehicles/hour.
- SANRAL listed the N12, N14 and several other routes as free-flowing all festive season.
- TomTom Routing API: future `departAt` uses TomTom's historical traffic. Free tier
  20,000 requests/month. Google Routes API has similar (trafficModel BEST_GUESS / PESSIMISTIC /
  OPTIMISTIC, requires TRAFFIC_AWARE_OPTIMAL; marked experimental).
- Open question being tested: does TomTom's future prediction capture holiday spikes
  (18 Dec, 3 Jan) or only a typical weekday? Compare against normal Friday/Sunday in
  `roadwise_test_results.csv`.
- api.tomtom.com was blocked from the claude.ai sandbox, which is why the test runs locally.

Sources:
- SANRAL expected peak festive travel times 2015/16: https://pressoffice.mg.co.za/SANRAL/content/RgeVDqPYEV8vKJN3
- SANRAL N1 Great North 2016/17: https://pressoffice.mg.co.za/SANRAL/content/dgp45Ma6PejqX9l8
- SANRAL long weekends (Easter 2016): https://www.polity.org.za/article/sanral-traffic-over-long-weekends-2016-03-18
- N3 best times Dec 2019 (IOL): https://iol.co.za/news/south-africa/kwazulu-natal/2019-12-12-travelling-to-kzn-on-the-n3-this-december-heres-the-best-times-to-do-so/
- Mooi Plaza 2 Jan 2022: https://m.motoring.co.za/news/1-879-cars-an-hour-passing-through-mooi-river-toll-plaza-as-holiday-makers-head-home-defdf6a2-f2e6-4c15-b242-db63b034bc07
- SANRAL 2019 CTO station data (N12): https://www.etenders.gov.za/home/Download/?blobName=0cb63eaf-0da2-4746-b5f7-4ccbf38016ab.pdf&downloadedFileName=2019+CTO+data_C4-Appendix+3.pdf
- TomTom Routing API: https://docs.tomtom.com/routing-api/  · pricing: https://docs.tomtom.com/pricing
- Google Routes traffic model: https://developers.google.com/maps/documentation/routes/traffic-model

## Next steps

1. Run `roadwise_test.py`, read `roadwise_test_results.csv`. Do Dec/Jan dates come back slower
   than normal Fridays/Sundays?
   - If yes: build the forecast from TomTom predicted travel time vs. the route's average
     predicted time (sample each day, maybe several departure hours). Cache results.
   - If no: TomTom knows typical weeks only. Use it for the normal-week profile, and get holiday
     effects from elsewhere (own recordings, SANRAL counts).
2. Start a logger that records TomTom *live* travel times on the routes every hour from now
   through January – our own record of this festive season to validate against.
3. Ask SANRAL for hourly count data from permanent stations on the N1 (north and south),
   N3, N12 and N14, ideally several years, to build real day-of-week and holiday profiles.
4. Later: Android app. The prototype page cannot call external APIs from a claude.ai artifact
   (CSP), so data fetching needs a small backend or must live in the app.

## Routes in the prototype

Pretoria/Johannesburg ↔ Polokwane (N1 North), Kimberley (N14/N12, N12), Bloemfontein,
Beaufort West, Cape Town (N1), Durban (N3). Distances and clear-road times are approximate.
