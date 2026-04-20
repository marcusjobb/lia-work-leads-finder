from pathlib import Path

import openpyxl
from openpyxl.styles import Font

from models import LeadProfile

_HEADERS = [
    "Företag", "Stad", "Score", "Tier",
    "Tech-taggar", "Kontakt e-post", "Kontakt URL", "Match-motivering",
]


def export_leads(profiles: list[LeadProfile], path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "LIA Leads"

    ws.append(_HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for p in profiles:
        ws.append([
            p.company_name,
            p.city,
            round(p.score, 1),
            p.tier,
            ", ".join(p.tech_tags),
            p.contact.email or "",
            p.contact.contact_url or p.contact.careers_page or "",
            p.match_reason,
        ])

    wb.save(path)
