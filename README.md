# Paperpulse - Daily ArXiv Research Summariser

Paperpulse retrieves new papers from ArXiv every day, groups them into themes using the **OpenAI Agents SDK**, and publishes the result as a Jekyll blog post.

The search scope, summarisation persona, and blog branding are all controlled via `config.yaml` — no code changes needed.

## Features

- Configurable ArXiv search by category and/or keyword (see `config.yaml`)
- Two-stage summarisation pipeline: batch summaries → single merged post
- Automatic hyperlinks from the summary text back to the ArXiv paper pages
- Jekyll blog served via Docker; production deployment uses a built-in cron scheduler

## Requirements

- Docker (both dev and prod run entirely in containers)
- An OpenAI API key

For local development outside Docker, Python 3.x and the packages in `api/requirements.txt` are also needed.

## Configuration

All user-facing settings live in `config.yaml`:

| Section | What it controls |
|---|---|
| `blog` | Site title, tagline, and per-post front-matter title |
| `search.categories` | ArXiv category codes to include |
| `search.keywords` | Free-text keyword filters (matched against title and abstract) |
| `search.mode` | How categories and keywords are combined (`categories_and_keywords`, `categories_only`, `keywords_only`) |
| `summarization.persona` | Opening of the LLM system prompt — sets expertise framing |
| `summarization.style` | Tone and explanation style injected after the persona |

Secrets and environment-specific values stay in `.env` (never committed):

```
OPENAI_API_KEY=sk-...
PROJECT_ENV=dev          # dev | prod
PROJECT_DIR=/path/to/paperpulse
MIXPANEL_TOKEN=...       # optional analytics
```

The `OPENAI_MODEL` environment variable controls which model is used (default: `gpt-4o-mini`).

## Development vs Production

### Development (`docker-compose.yml`)

Intended for local iteration. The Jekyll blog is served with `--livereload` so changes to `blog/` are reflected immediately.

The API container is defined under the `run` profile so it only starts on demand:

```bash
# Start the blog (live-reload at localhost:4000)
docker compose up --build

# Run the summariser once
docker compose run --rm api
```

In `dev` mode (`PROJECT_ENV=dev`), retrieved papers are cached to a pickle file (`data/papers-<date>.pkl`). Re-running within the same day skips the ArXiv API call and uses the cache, which speeds up iteration.

The `.env` file is bind-mounted read-only into the container so `python-dotenv` can load it automatically.

### Production (`docker-compose.prod.yml`)

Intended for a server deployment (e.g. an LXC container behind Nginx Proxy Manager). Key differences from dev:

| Aspect | Dev | Prod |
|---|---|---|
| Jekyll image | Pre-built `jekyll/jekyll:4` | Custom image built from `Dockerfile.jekyll` |
| Jekyll command | `jekyll serve --livereload` | Built as a static site; served by Jekyll's production server |
| API invocation | Manual (`docker compose run`) | Automatic — `supercronic` runs the crontab on schedule |
| Cron schedule | — | Daily at 06:00 UTC (`api/crontab`) |
| `.env` mount | Yes (read-only) | No — env vars are passed directly in the compose file |
| Restart policy | — | `unless-stopped` on both services |
| Networking | Default bridge | Named `web` bridge network |

SSL termination and domain routing are handled externally by Nginx Proxy Manager; this stack only exposes port 4000 on the host.

```bash
# Start the production stack (detached)
docker compose -f docker-compose.prod.yml up -d --build
```

Set `OPENAI_API_KEY` and `OPENAI_MODEL` (optional) in the server environment or a secrets manager before starting.

## Project Structure

```
config.yaml              # All user-facing configuration
docker-compose.yml       # Dev stack
docker-compose.prod.yml  # Production stack
api/
  main.py                # Orchestrator — wires ArXiv → agent → blog post
  arxiv_client.py        # ArXiv API queries
  agent.py               # OpenAI Agents SDK: summariser + combiner agents
  file_handler.py        # Paper pickle cache (dev mode)
  webs.py                # Renders the Jekyll markdown post
  settings.py            # Env var loading, prompt builders, query builder
  utils.py               # PDF extraction and text utilities
  crontab                # Cron schedule for production (supercronic)
  requirements.txt
  tests/
    test_main.py         # Unit tests for core logic
blog/                    # Jekyll site — posts written here by the API
```

## Running Tests

```bash
pytest api/tests/test_main.py
```

## License

MIT License
