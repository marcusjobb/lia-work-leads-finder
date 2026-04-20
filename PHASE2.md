# Phase 2 — Cover Letter Agent

> Byggs efter att Phase 1 (leads finder) är klar.
> Integreras i samma FastAPI-app och GUI.

---

## Koncept

Från ett lead-kort i results-vyn klickar studenten "Skriv ansökningsbrev". Appen öppnar ett formulär förfyllt med företagsdata från lead-profilen. Studenten verifierar sin profil och triggar pipeline:

```
Research agent  ──  scrapa företaget djupare (kultur, värderingar, nyheter)
Writer agent    ──  generera personaliserat brev (student-profil + företagsdata)
Tone validator  ──  professionellt men mänskligt, inte robotigt
Lang validator  ──  svenska/engelska baserat på företagets detekterade språk
         ↓
Visa brev i UI + "Ladda ner .docx"
```

---

## Student-profil

Sparas som `student_profile.yaml` i projektroten (fylls i en gång, återanvänds).
Ingen databas behövs — profilen är statisk per student.

```yaml
name: "Anna Lindqvist"
education: "YH Java-utvecklare, Handelsakademin Göteborg, 2024–2026"
tech_stack: ["Java", "Spring Boot", "SQL", "Docker"]
experience: "2 år som supporttekniker, hobby-projekt i Python"
languages: ["svenska", "engelska"]
portfolio_url: "https://github.com/annalindqvist"
bio: "Driven och nyfiken, trivs i team och gillar att lösa komplexa problem"
```

---

## Filstruktur (tillägg till Phase 1)

```
lia-leeds-finder/
├── cover_letter/
│   ├── pipeline/
│   │   ├── research_agent.py       # Scrapa företaget: kultur, värderingar, nyheter
│   │   ├── writer_agent.py         # Generera brev via LLM
│   │   └── validators/
│   │       ├── tone_validator.py   # Professionellt men mänskligt
│   │       └── language_validator.py # Rätt språk baserat på företaget
│   └── templates/
│       └── letter_prompt.jinja2    # LLM-prompt-template
├── export/
│   ├── docx_exporter.py            # python-docx → .docx
│   └── xlsx_exporter.py            # openpyxl → .xlsx (leads-export)
├── llm_client.py                   # Provider-abstraktion (OpenRouter / Claude CLI)
├── student_profile.yaml            # Studentens profil (fylls i en gång)
├── .env.example                    # Konfig-mall
└── templates/
    └── cover_letter.html           # Visa brev i UI + nedladdningsknapp
```

---

## LLM-konfiguration

Ingen databas, ingen komplex auth — bara en `.env`-fil:

```env
# Välj provider: openrouter eller claude-cli
LLM_PROVIDER=openrouter

# OpenRouter (https://openrouter.ai)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=anthropic/claude-sonnet-4-5

# Claude CLI — inget nyckel behövs, anropas via subprocess
# LLM_PROVIDER=claude-cli
```

`.env.example` committas (utan nycklar). `.env` läggs i `.gitignore`.

### llm_client.py — provider-abstraktion

```python
async def complete(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "openrouter")
    if provider == "openrouter":
        return await _openrouter(prompt)
    elif provider == "claude-cli":
        return await _claude_cli(prompt)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
```

Resten av koden anropar bara `llm_client.complete(prompt)` — ingen provider-logik läcker ut.

---

## Export-moduler (ingen LibreOffice)

Rena pip-installerbara bibliotek, noll systemdependencies:

| Modul | Bibliotek | Output |
|-------|-----------|--------|
| `docx_exporter.py` | `python-docx` | `.docx` (Word, LibreOffice, Google Docs) |
| `xlsx_exporter.py` | `openpyxl` | `.xlsx` med leads-data, en rad per företag |

### Excel-export (leads)

Kolumner: Företag · Stad · Score · Tier · Tech-taggar · Kontakt-e-post · Kontakt-URL · Match-motivering

Triggas via "Exportera lista"-knapp i results-vyn.

### Word-export (brev)

Enkelt formaterat brev med:
- Datum + adressering
- Brevtext från writer agent
- Studentens kontaktinfo i sidhuvud

---

## Datastrategi — ingen databas

| Data | Lösning |
|------|---------|
| Student-profil | `student_profile.yaml` (statisk fil) |
| Sökresultat | In-memory under sessionen |
| Leads-export | `.xlsx` vid behov |
| Brev | Genereras on-demand, laddas ner som `.docx` |
| Cache senaste sökning | `cache/last_results.json` (optional) |

SQLite tillför ingenting här — all "persistens" sker via export-filerna.

---

## GUI-integration

Phase 1 results-vyn utökas med:

1. **"Exportera leads"**-knapp → laddar ner `.xlsx` med alla STRONG/GOOD leads
2. **"Skriv ansökningsbrev"**-knapp på varje lead-kort → öppnar cover letter-flödet
3. Cover letter-sidan visar brevet, erbjuder redigering + "Ladda ner .docx"

---

## Implementationsordning (Phase 2)

1. `llm_client.py` — provider-abstraktion med stöd för båda providers
2. `export/xlsx_exporter.py` — leads till Excel (oberoende av LLM)
3. `cover_letter/pipeline/research_agent.py` — djupare företagsskrapning
4. `cover_letter/pipeline/writer_agent.py` — LLM-anrop med prompt-template
5. `cover_letter/pipeline/validators/` — tone + language
6. `export/docx_exporter.py` — brev till Word
7. GUI-tillägg i `templates/results.html` + ny `templates/cover_letter.html`

---

## Verifiering

```bash
# Konfigurera
cp .env.example .env
# Fyll i OPENROUTER_API_KEY i .env

# Kör
uv run python app.py

# Flöde att testa:
# 1. Sök leads → results-sida
# 2. Klicka "Exportera leads" → verifiera .xlsx öppnas i Excel/LibreOffice
# 3. Klicka "Skriv ansökningsbrev" på ett STRONG-lead
# 4. Verifiera att brevet är personaliserat (nämner rätt företag + tech-stack)
# 5. Ladda ner .docx → öppnas korrekt i Word/LibreOffice
```
