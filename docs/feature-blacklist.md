# Feature: Svartlista företag

## Syfte

Låt användaren permanent dölja företag de inte är intresserade av, direkt från sökresultaten eller detaljvyn — utan att behöva redigera filer.

## Beteende

### Svartlista ett företag
- En **"Dölj"-knapp** visas på varje lead-rad i resultatlistan och på detaljsidan.
- Klick lägger till företaget i svartlistan och sidan uppdateras.

### Visa svartlistade i resultatlistan
- Svartlistade företag visas med en **svart ikon** (t.ex. 🚫 eller ett öga med linje) och nedtonad stil.
- En **toggle** längst upp i resultatlistan låter användaren visa eller dölja svartlistade företag (standard: dolda).

### Ta bort från svartlistan
- På detaljsidan: knappen ändras till "Ta bort från svartlista" om företaget redan är svartlistat.
- Alternativt: en lista på profilsidan (`/profile`) med alla svartlistade företag och en "Ta bort"-länk per rad.

## Lagring

Befintlig SQLite-databas: `cache/company_data.db`.

Ny tabell:
```sql
CREATE TABLE IF NOT EXISTS blacklist (
    company_name TEXT PRIMARY KEY,
    added_at     TEXT DEFAULT (datetime('now'))
);
```

## API-endpoints

| Method | Route | Handling |
|--------|-------|----------|
| `POST` | `/blacklist` | Lägger till `company_name` i blacklist-tabellen |
| `POST` | `/blacklist/remove` | Tar bort `company_name` ur blacklist-tabellen |
| `GET`  | `/blacklist` | Returnerar lista med alla svartlistade namn (används på profilsidan) |

## Berörd kod

| Fil | Ändring |
|-----|---------|
| `pipeline/enrichment/company_cache.py` | Lägg till `BlacklistDB`-klass med `add`, `remove`, `all`, `is_blacklisted` |
| `app.py` | Tre nya routes; läs blacklist vid sökning och märk profiler |
| `models.py` | Lägg till `blacklisted: bool = False` på `LeadProfile` |
| `templates/results.html` | Dölj/visa toggle + ikon + Dölj-knapp per rad |
| `templates/lead_detail.html` | Dölj/Ta bort-knapp beroende på status |
| `templates/profile.html` | Lista med svartlistade + Ta bort-länk |

## Ej i scope

- Synkronisering mellan enheter
- Export av svartlista
- Kommentar/orsak till svartlistning
