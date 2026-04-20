from models import CompanyRaw, ContactInfo, LeadProfile, ScoreBreakdown, SearchConfig
from pipeline.enrichment.tech_analyzer import analyze_tech
from pipeline.enrichment.geo_scorer import score_geo
from quality_gate import assign_tier, compute_score

# MVP defaults for unimplemented enrichers
_CONTACT_SCORE_DEFAULT = 0.0
_ACTIVITY_SCORE_DEFAULT = 80.0  # job board listing = recent activity
_STABILITY_SCORE_DEFAULT = 50.0  # unknown


def build_profile(company: CompanyRaw, config: SearchConfig) -> LeadProfile:
    analysis_text = " ".join(filter(None, [company.job_title, company.description]))

    tech_score = analyze_tech(config.tech_stack, analysis_text)
    geo_score = score_geo(company.city, config.city, config.all_sweden)

    breakdown = ScoreBreakdown(
        tech_match=tech_score,
        geo=geo_score,
        contact=_CONTACT_SCORE_DEFAULT,
        activity=_ACTIVITY_SCORE_DEFAULT,
        stability=_STABILITY_SCORE_DEFAULT,
    )
    score = compute_score(breakdown)
    tier = assign_tier(score)

    matched = [t for t in config.tech_stack if t.lower() in analysis_text.lower()]
    reason_parts = []
    if matched:
        reason_parts.append(f"Matchar {', '.join(matched)}")
    if geo_score == 100.0:
        reason_parts.append(company.city)
    elif config.all_sweden:
        reason_parts.append("Hela Sverige")
    match_reason = ", ".join(reason_parts) or "Generell matchning"

    return LeadProfile(
        company_name=company.name,
        website=company.website,
        city=company.city,
        tech_tags=[t.lower() for t in config.tech_stack if t.lower() in analysis_text.lower()],
        contact=ContactInfo(),
        score=score,
        score_breakdown=breakdown,
        match_reason=match_reason,
        tier=tier,
    )
