# LIA Leads Finder

Automatiserat verktyg för YH-studenter att hitta LIA-praktikplatser (Lärande i Arbete). Skrapar jobbannonser och bolagsregister, rankar företag efter tech-match och kontaktbarhet, och genererar personliga ansökningsbrev med AI.

## Kom igång

```bash
# Installera beroenden
uv sync

# Installera Playwright-webbläsare (krävs för scraping av Indeed)
uv run playwright install chromium

# Starta
uv run python src/app.py
# → http://localhost:8000
```

## Konfiguration

Kopiera `.env.example` till `.env` och fyll i önskade värden:

```bash
cp .env.example .env
```

| Variabel | Beskrivning | Standard |
|----------|-------------|---------|
| `LLM_PROVIDER` | `claude-cli` \| `openrouter` \| `anthropic` | `claude-cli` |
| `OPENROUTER_API_KEY` | API-nyckel för OpenRouter | — |
| `OPENROUTER_MODEL` | Modell att använda via OpenRouter | `minimax/minimax-01` |
| `ANTHROPIC_API_KEY` | API-nyckel för Anthropic SDK | — |
| `ANTHROPIC_MODEL` | Modell att använda via Anthropic | `claude-sonnet-4-6` |
| `SITE_URL` | Publik URL (används i OpenRouter-anrop) | `http://localhost:8000` |
| `FORETAGSAPI_KEY` | [foretagsapi.se](https://foretagsapi.se) — valfri, guest-läge fungerar utan | — |
| `BOLAGSAPI_KEY` | [bolagsapi.se](https://bolagsapi.se) — valfri, ger finansiell hälsopoäng | — |

## Pipeline

```
Profil → Discovery → Enrichment → Scoring → Resultat → Ansökningsbrev
```

**Discovery** hämtar kandidater från tre källor parallellt:

- ~~**Indeed.se** — jobbannonser via Playwright~~ (funkar inte ännu)
- **Arbetsförmedlingen** — platsannonser via publik sökning
- ~~**Allabolag.se** — direktsökning på IT-bolag per stad~~ (funkar inte ännu)

**Enrichment** berikar varje kandidat med data från foretagsapi.se och bolagsapi.se (org-nummer, registreringsdatum, antal anställda, kontaktinfo).

**Scoring** viktas efter:

| Dimension | Vikt |
|-----------|------|
| Tech-match | 35% |
| Senioritet | 20% |
| Kontaktbarhet | 20% |
| Aktivitet | 15% |
| Stabilitet | 10% |

Tier-trösklar: **STRONG** ≥70 · **GOOD** 50–69 · **WEAK** 30–49 · **SKIP** <30

## Krav

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) för pakethantering
