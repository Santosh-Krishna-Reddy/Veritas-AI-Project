# GridGreen web page

A thin display layer over the FastAPI service. It computes no numbers: every value comes from
`api/service.py`, which reads the trained model, `data/processed/` and `results/`.

Needs: [uv](https://docs.astral.sh/uv/) and Node.js 20 or newer.

From the repo root, once, to build the Python environment, the model and the results:

```bash
uv venv --python 3.12 && uv pip install -r requirements.txt
make data train eval rank failures
```

Then two terminals, both from the repo root:

```bash
make api                                  # terminal 1: FastAPI on http://localhost:8000
cd web && npm install && npm run dev      # terminal 2: page on http://localhost:3000
```

Open http://localhost:3000. If the API runs somewhere else, set `NEXT_PUBLIC_API_URL`
(default `http://localhost:8000`). Load presets live in `lib/presets.ts`. Screenshots are in
`docs/ui/`.
