from models import CompanyRaw, ContactInfo, LeadProfile, ScoreBreakdown, SearchConfig
from pipeline.enrichment.tech_analyzer import analyze_tech
from pipeline.enrichment.geo_scorer import score_geo
from pipeline.enrichment.seniority_scorer import score_seniority
from pipeline.enrichment.contact_finder import find_contact
from quality_gate import assign_tier, compute_score

_STABILITY_SCORE_DEFAULT = 50.0


def _assemble(
    company: CompanyRaw,
    config: SearchConfig,
    contact_info: ContactInfo,
    contact_score: float,
) -> LeadProfile:
    analysis_text = " ".join(filter(None, [company.job_title, company.description]))
    tech_score = analyze_tech(config.tech_stack, analysis_text)
    geo_score = score_geo(company.city, config.city, config.all_sweden)
    seniority_score = score_seniority(analysis_text)
    breakdown = ScoreBreakdown(
        tech_match=tech_score,
        geo=geo_score,
        contact=contact_score,
        activity=80.0,  # replaced in Task 3
        stability=_STABILITY_SCORE_DEFAULT,
        seniority=seniority_score,
    )
    score = compute_score(breakdown)
    tier = assign_tier(score)
    matched = [t for t in config.tech_stack if t.lower() in analysis_text.lower()]
    reason_parts = [f"Matchar {', '.join(matched)}"] if matched else []
    if geo_score == 100.0:
        reason_parts.append(company.city)
    elif config.all_sweden:
        reason_parts.append("Hela Sverige")
    return LeadProfile(
        company_name=company.name,
        website=company.website,
        city=company.city,
        source=company.source,
        tech_tags=[t.lower() for t in config.tech_stack if t.lower() in analysis_text.lower()],
        contact=contact_info,
        score=score,
        score_breakdown=breakdown,
        match_reason=", ".join(reason_parts) or "Generell matchning",
        tier=tier,
    )


def build_profile(company: CompanyRaw, config: SearchConfig) -> LeadProfile:
    """Sync build — contact defaults to 0.0."""
    return _assemble(company, config, ContactInfo(), 0.0)


async def build_profile_async(company: CompanyRaw, config: SearchConfig) -> LeadProfile:
    """Async build — scrapes company website for contact info."""
    contact_info, contact_score = await find_contact(company.website)
    return _assemble(company, config, contact_info, contact_score)
