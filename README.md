# PyConvert — AI-Powered JavaScript → TypeScript Converter

A self-hosted **FastAPI** studio that ingests a JavaScript project folder, renders its
directory tree, converts every `.js` / `.jsx` source file to typed TypeScript using the
**Google Gemini API** (bring-your-own-key), and exports a ready-to-build TypeScript
project as a `.zip` or straight to disk.

Runs entirely on your machine — there is no account, no telemetry, and no hosted
backend. Source files and your Gemini key only ever travel between your browser,
the local server, and Google's API.

<p align="left">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License: Apache-2.0"></a>
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue.svg" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Gemini-BYOK-886fb5.svg" alt="Gemini BYOK">
  <img src="https://img.shields.io/badge/tests-6%20passing-brightgreen.svg" alt="6 tests passing">
</p>

---

## Features

**Project ingestion**
- Load a folder via the browser picker or drag-and-drop, or scan a local path directly from disk.
- Non-source noise is skipped automatically: `node_modules`, `.git`, `dist`, `build`, `.next`, `.nuxt`,
  `__pycache__`, `.venv`, lockfiles, and `.DS_Store`.
- Collapsible file tree with per-file status (`pending` → `converting` → `converted` / `error`) and
  file-type badges.

**Conversion**
- Extension mapping: `.js → .ts`, `.jsx → .tsx`, `.mjs → .mts`, `.cjs → .cts`.
- React components are detected heuristically (imports, JSX literals, `className`, hooks) so plain
  `.js` files containing JSX still get `.tsx` output, while a pure Node module won't false-positive.
- Conversion prompts are selected per context — `standard`, `strict`, `react`, or `node_backend`
  (the last one also rewrites CommonJS `require`/`module.exports` to ESM).
- Convert a single file, or batch the whole project concurrently behind a semaphore (default 3,
  hard-capped at 5) so your rate limit survives.
- De-duplicated streaming output: model "thought" parts are dropped, only real code is kept.

**Review & edit**
- Split view: original JavaScript beside the generated TypeScript.
- Line-by-line diff mode (LCS-based) showing exactly which types, interfaces, and generics were added.
- Editable output pane, so you can fix a signature before shipping.
- Prism syntax highlighting with line numbers and copy buttons.

**Config & export**
- Detects React / Vite / Next.js / Express-Koa-Fastify / plain JS from `package.json` and emits a
  matching `tsconfig.json` — e.g. `jsx: "react-jsx"` and `noEmit: true` for frontend projects.
- Injects `typescript` and the right `@types/*` packages into `package.json` devDependencies.
- Downloads a `.zip` that preserves your directory layout; or writes to a target directory on disk.
- Built-in samples to try it on immediately: **⚡ Express API** (routes, controllers, JWT middleware,
  models) and **⚛️ React UI** (components, custom hooks, props, state).

---

## Quick start

Tested on **Python 3.13.14**; the committed bytecode in the repo is `cpython-312`, so treat 3.12+ as
the safe baseline. Nothing pins a version in [`requirements.txt`](requirements.txt).

```bash
git clone https://github.com/harsh-gupta280102/Build-With-Vexite-PyConvert.git
cd Build-With-Vexite-PyConvert

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py
```

The API starts on `http://127.0.0.1:8000` and your browser opens automatically.

On Windows you can double-click `run.bat` instead, which just runs `python main.py`.

### CLI options

| Flag | Default | Purpose |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8000` | Bind port |
| `--no-browser` | off | Don't auto-open the browser |
| `--reload` | off | Uvicorn autoreload for development |

```bash
python main.py --port 9000 --no-browser
```

---

## Usage

1. **Set your key** — click **Set API Key** (top right), paste a key from
   [Google AI Studio](https://aistudio.google.com/app/apikey), press
   **Test Key Connection**, then **Save & Apply Key**.
2. **Load a project** — **Upload Folder**, drag-and-drop, **Scan Path** for a local directory such as
   `C:/Projects/my-app`, or hit **⚡ Express API (JS)** / **⚛️ React UI (JSX)** for the built-in samples.
3. **Convert** — select a file in the tree, then **Convert File**; or press
   **Convert Entire Project (JS → TS)** for a concurrent batch with live progress.
4. **Review** — toggle **Diff Mode** to see added types highlighted, and **Edit** to tweak output by hand.
5. **Export** — **Download .ZIP** for an archive with `tsconfig.json` and the updated `package.json`,
   or use disk export to write into a target folder.

### Model selection

Models are defined in [`app/config.py`](app/config.py), served by `GET /api/models`, and selectable in
the UI. Current options:

| Model ID | Positioning |
| --- | --- |
| `gemini-3.6-flash` | Recommended, fastest — also the fallback target |
| `gemini-3.5-flash-lite` | Ultra-fast, cost-effective, high throughput |
| `gemini-3.6-pro` | Deep reasoning for complex codebases and heavy generics |

`gemini-2.0-flash` and `gemini-1.5-flash` are also listed, but they are **legacy aliases auto-mapped
onto `gemini-3.6-flash`** rather than distinct models. If a requested model comes back unavailable,
the service parses the error for Google's suggested replacement, tries the known set in preference
order, and finally calls `ListModels` to find any model supporting `generateContent` — so a stale
model ID degrades instead of failing. These IDs come from `app/config.py`, not from Google's docs;
if one is unavailable on your key or plan, treat the mapping above as a hint and check
[AI Studio](https://aistudio.google.com/app/apikey) for what you can actually call.

---

## HTTP API

The UI is a thin client over these endpoints; interactive docs live at
[`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs).

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/models` | Available models and the default |
| `POST` | `/api/validate-key` | Test a Gemini key with a 10-token probe |
| `POST` | `/api/scan-path` | Scan a local directory → tree, stats, analysis, `tsconfig` |
| `GET` | `/api/samples` | List built-in sample projects |
| `POST` | `/api/load-sample/{sample_id}` | Load `express_api` or `react_components` |
| `POST` | `/api/convert-file` | Convert one file |
| `POST` | `/api/batch-convert` | Convert many files concurrently, semaphore-bounded |
| `POST` | `/api/analyze-project` | Framework analysis, `tsconfig`, updated `package.json` |
| `POST` | `/api/export-zip` | Project converted output as a `.zip` download |
| `POST` | `/api/export-disk` | Write converted output to a directory |
| `GET` | `/` | Serve the single-page UI |

---

## Project structure

```
.
├── main.py                      # Entry point: uvicorn + argparse + browser launch
├── requirements.txt
├── run.bat                      # Windows one-click launcher
├── test_backend.py              # unittest suite for the core services
├── test_gemini_schema.py        # Ad-hoc probe for Gemini request/response shape
├── app/
│   ├── config.py                # Port/host defaults, model list, prompt templates
│   ├── server.py                # FastAPI app, CORS, request models, routes
│   └── services/
│       ├── gemini_service.py    # Gemini client, model fallback, code-block extraction
│       ├── project_scanner.py   # Recursive disk scan, ignore rules, tree + metrics
│       ├── analyzer.py          # Framework detection, tsconfig + package.json generation
│       ├── exporter.py          # In-memory zip builder, disk exporter
│       └── sample_projects.py   # Bundled Express and React fixtures
└── static/
    ├── index.html               # Single-page studio UI
    ├── css/style.css            # Dark glassmorphic design system
    └── js/
        ├── api.js               # REST client
        ├── app.js               # State, batch orchestration, key storage
        ├── diff.js              # LCS-based visual diff renderer
        ├── editor.js            # Split pane + Prism highlighting
        └── tree.js              # Collapsible tree with search filter
```

---

## Testing

Run from the repository root:

```bash
python -m unittest test_backend -v
```

Six tests, all passing, via either runner — `python -m unittest test_backend -v` or
`python -m pytest test_backend.py` (both report 6).
They cover the model config, sample fixtures, framework analysis and `tsconfig` output, JSX
detection (including the `.js`-contains-JSX and pure-Node negative cases), zip export preserving
static assets, and stripping prose from model replies:

```
test_config_models .............................. ok
test_sample_projects ............................ ok
test_project_analyzer ........................... ok
test_jsx_code_detection ......................... ok
test_project_exporter_preserves_static_files .... ok
test_gemini_code_extraction ..................... ok
```

`test_backend.py` is pure `unittest` and needs no network or API key — it exercises local services only.

`test_gemini_schema.py` is a separate script, not part of that suite. It fires a single hardcoded
`maxOutputTokens: 0` request at Google with a dummy key and prints the decoded response to validate
the `systemInstruction` / `functionResponse` wire format. Leave it out of CI: it is a manual probe,
not an assertion, and `pytest` collects it as a module rather than a test case.

---

## Security & privacy

The model is bring-your-own-key, and the key is kept in browser `localStorage` under
`pyconvert_gemini_api_key` — the server never persists it to disk or to any storage of its own.

Worth understanding before you use it, though, because the local server is not a sandbox boundary:

- **Requests are server-side.** The browser posts your key and your source code to this FastAPI
  backend, which forwards them to `generativelanguage.googleapis.com`. Your code leaves your
  machine to Google, under your key and your data-processing terms.
- **CORS is open to every origin.** `app/server.py` sets `allow_origins=["*"]` alongside
  `allow_credentials=True`. Any page open in your browser can therefore call a loopback server on
  port 8000: read directories with `POST /api/scan-path`, and write files anywhere your user can
  write with `POST /api/export-disk`. Bind to `127.0.0.1` (the default) rather than `0.0.0.0`, don't
  expose it over a tunnel, and tighten `allow_origins` to the app's own origin before deploying.
- **The key travels as a query parameter** (`?key=...`), which can surface in proxy and server logs.
- **No authentication** on any endpoint. Treat this as a single-user local development tool.

---

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| Conversion fails with `404`/`400`, or Google reports a model as "no longer available" / "not found for API version" | The requested model ID isn't servable by your key. `_resolve_working_model` re-routes it automatically; if it still fails, pick `gemini-3.6-flash` explicitly and re-test the key. |
| Google reports "`API key not valid`" (HTTP `400`/`403`) | Wrong, disabled, or non-Google key. Re-check it at AI Studio and run **Test Key Connection**. |
| `429` quota exceeded on batch runs | Lower `concurrency` (e.g. 1–2) and retry; the semaphore caps at 5 regardless. |
| Browser didn't open | Normal on headless setups — visit `http://127.0.0.1:8000` manually, or start with `--no-browser`. |
| Port already in use | `python main.py --port 9000` |
| Empty or garbled TypeScript | Check **Diff Mode** for a truncated reply; large files hit `maxOutputTokens: 8192`, so split them or use a `-pro` model. |
| Missing files in the zip | Confirm the path isn't under `node_modules`, `dist`, `build`, or another ignored directory. |
| No syntax highlighting / unstyled code | Prism 1.29.0 is loaded from `cdnjs.cloudflare.com`, so the page needs outbound internet even though the backend is local. |

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).