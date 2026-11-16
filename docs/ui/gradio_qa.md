# GridGreen Gradio dashboard QA

Tested November 15, 2026 on macOS in Google Chrome with Python 3.12 and Gradio 6.32.0.

## Automated checks

- `make test`: **24 passed**. The 10 warnings are existing pandas deprecations in `ml/features.py` and `ml/data.py`.
- `python -m py_compile app.py`: passed.
- `git diff --check`: passed.
- `make app`: started successfully at `http://127.0.0.1:7862` (`7860` and `7861` were already occupied on the test machine).

## Forecast and interaction checks

| Check | Result |
|---|---|
| Historical labeling | Pass. Replay window is **Nov 14, 3 AM–Nov 15, 2 AM 2026 CT**; the interface does not call it live or tomorrow's forecast. |
| Cleanest hour | Pass. **11 AM Saturday**, 326.054 gCO₂/kWh (displayed as 326). |
| Three recommendations | Pass. UI order matches `numpy.argsort`: 11 AM (326.054), 12 PM (326.329), 10 AM (327.539). The strip contains exactly three individually labeled markers. |
| Load behavior | Pass. The default 7 kWh scenario displays 0.30 kg CO₂; selecting the illustrative 40 kWh EV preset updates it to 1.70 kg CO₂ without changing the forecast. |
| Metrics | Pass. Values are read from `results/metrics.json`: model/persistence MAE 13.77/16.94 and cleanest-three overlap 0.473/0.483. |
| Missing artifacts | Pass by code-path inspection and callback check. Missing model, data, or metrics produce an explicit setup panel and no substitute values. |

## Browser inspection

### 1440 × 900

- Dashboard content is 1,240 px wide with no horizontal overflow.
- Both model and persistence lines render in the Gradio/Vega chart.
- The full 24-cell intensity strip fits below the chart, with clean 01/02/03 markers.
- IBM Plex web fonts report `loaded`; system fallbacks remain in the stylesheet for offline use.

Screenshots:

- `.context/gridgreen-desktop-1440x900.png`
- `.context/gridgreen-desktop-chart-1440x900.png`

### 390 × 844

- Body width remains 390 px with no page-level horizontal overflow; dashboard content is 366 px wide.
- Header retains GRIDGREEN / PJM / HISTORICAL REPLAY.
- Hero stacks into one column. Chart tick density drops to six readable time labels.
- The carbon strip scrolls horizontally and tells the user that all 24 hours are available.

Screenshots:

- `.context/gridgreen-mobile-390x844.png`
- `.context/gridgreen-mobile-chart-390x844.png`

## Accessibility and console

- Native link, buttons, number input, reset control, range slider, and chart export control are reachable in logical Tab order.
- Focus-visible styling is present for preset controls. Recommendations and the strip expose text labels in addition to color.
- Measurement typography uses tabular numerals, and muted text was checked against the deep navy panels at both viewports.
- No JavaScript exceptions or console errors appeared. Gradio's native `LinePlot` emitted two non-blocking Vega warnings: its generated spec identifies Vega-Lite 5.17 while the bundled renderer is 6.4.2, and Vega drops `zero` on the categorical point scale.

## Known constraints

- IBM Plex loads from [Google Fonts](https://fonts.google.com/specimen/IBM+Plex+Sans) when network access is available; the UI falls back to Arial/SFMono-compatible system fonts offline.
- The two Vega warnings are internal to Gradio's native chart output and do not affect rendering or interaction.
