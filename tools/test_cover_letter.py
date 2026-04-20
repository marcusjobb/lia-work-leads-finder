#!/usr/bin/env python3
"""End-to-end test: hämta företagsdata, generera ansökningsbrev, validera."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("LLM_PROVIDER", "claude-cli")

from cover_letter.models import StudentProfile
from cover_letter.pipeline.research_agent import research_company
from cover_letter.pipeline.writer_agent import generate_letter
from cover_letter.pipeline.validators.tone_validator import validate_tone
from cover_letter.pipeline.validators.language_validator import validate_language
from models import ContactInfo, LeadProfile, ScoreBreakdown


NEXER_LEAD = LeadProfile(
    company_name="Nexer Tech Talent AB",
    website="https://techtalent.nexergroup.com",
    city="Göteborg",
    tech_tags=["Java", "Spring Boot", "Kubernetes", "REST API", "Kafka"],
    contact=ContactInfo(
        contact_url="https://techtalent.nexergroup.com/jobs/7592914-java-developer/applications/new"
    ),
    score=82.0,
    score_breakdown=ScoreBreakdown(tech_match=90, geo=80, contact=70, activity=90, stability=80),
    match_reason="Exakt Java/Spring Boot-match, aktiv annons, Göteborg",
    tier="STRONG",
)

STUDENT = StudentProfile(
    name="Nisse Nilsson",
    education="YH Java-utvecklare, Handelsakademin Göteborg, 2024–2026",
    tech_stack=["Java", "Spring Boot", "SQL", "Docker", "Git"],
    experience="2 år som supporttekniker på AID Solutions, drift av Linux-servrar, Python-automation",
    languages=["svenska", "engelska"],
    portfolio_url="https://github.com/nissenilsson",
    bio="Lösningsorienterad och trivs med att arbeta nära driftsteam och slutanvändare",
)


async def main():
    print("=== LIA Cover Letter — Flödestest ===\n")

    print("1. Researchar företaget...")
    research = await research_company(NEXER_LEAD)
    print(f"   Detekterat språk: {research.detected_language}")
    print(f"   About-text (utdrag): {research.about_text[:150]}...")
    if research.values:
        print(f"   Värderingar: {research.values[:2]}")

    print("\n2. Genererar brev via LLM...")
    letter = await generate_letter(STUDENT, research)
    print("\n--- BREV ---")
    print(letter)
    print("--- SLUT ---\n")

    print("3. Validerar ton...")
    tone = validate_tone(letter)
    if tone.ok:
        print("   ✓ Ton OK — inga klichéer hittades")
    else:
        print(f"   ✗ Tonproblem: {tone.issues}")

    print("4. Validerar språk...")
    lang = validate_language(letter, research.detected_language)
    if lang.ok:
        print(f"   ✓ Språk OK — {lang.detected}")
    else:
        print(f"   ✗ Språkfel — förväntat {lang.expected}, detekterat {lang.detected}")

    print("\n=== Test klart ===")


if __name__ == "__main__":
    asyncio.run(main())
