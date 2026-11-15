# GridGreen web page

A thin display layer over the FastAPI service. It computes no numbers: every value comes from
`api/service.py`, which reads the trained model, `data/processed/` and `results/`.

Run it with two terminals from the repo root (after `make data train eval rank failures`):

```bash
make api                                  # terminal 1: FastAPI on http://localhost:8000
cd web && npm install && npm run dev      # terminal 2: page on http://localhost:3000
```

If the API runs somewhere else, set `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
Load presets live in `lib/presets.ts`. Screenshots are in `docs/ui/`.
