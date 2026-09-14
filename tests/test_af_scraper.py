import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pipeline.discovery.af_scraper import scrape_af, _candidate_query_tiers

MOCK_RESPONSE = {
    "hits": [
        {
            "headline": "Python Developer",
            "employer": {"name": "Acme AB"},
            "workplace_address": {"city": "Stockholm", "municipality": "Stockholm"},
            "webpage_url": "https://example.com/job/1",
        },
        {
            "headline": "Django Backend Engineer",
            "employer": {"name": "Tech AB"},
            "workplace_address": {"city": "Stockholm", "municipality": "Stockholm"},
            "webpage_url": "https://example.com/job/2",
        },
    ]
}


@pytest.mark.asyncio
async def test_scrape_returns_companies():
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_RESPONSE
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            get=AsyncMock(return_value=mock_response)
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, _ = await scrape_af(["Python", "Django"], "Stockholm")

    assert len(results) == 2
    assert results[0].name == "Acme AB"
    assert results[0].source == "af"
    assert results[0].city == "Stockholm"
    assert results[0].job_title == "Python Developer"


@pytest.mark.asyncio
async def test_scrape_empty_on_error():
    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            get=AsyncMock(side_effect=Exception("network error"))
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, _ = await scrape_af(["Python"], "Stockholm")

    assert results == []


@pytest.mark.asyncio
async def test_skips_entries_without_employer_name():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "hits": [{"headline": "Job", "employer": {}, "workplace_address": {}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            get=AsyncMock(return_value=mock_response)
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, _ = await scrape_af(["Python"], "Stockholm")

    assert results == []


@pytest.mark.asyncio
async def test_extracts_publication_date():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "hits": [
            {
                "headline": "Python Developer",
                "employer": {"name": "Acme AB"},
                "workplace_address": {"city": "Stockholm"},
                "webpage_url": "https://example.com/job/1",
                "publication_date": "2026-03-15T12:00:00",
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(return_value=mock_response))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, _ = await scrape_af(["Python"], "Stockholm")

    assert results[0].publication_date == "2026-03-15T12:00:00"


@pytest.mark.asyncio
async def test_returns_total_hits():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "total": {"value": 42},
        "hits": [
            {
                "headline": "Python Developer",
                "employer": {"name": "Acme AB"},
                "workplace_address": {"city": "Göteborg"},
                "webpage_url": "https://example.com/job/1",
                "publication_date": "2026-04-01T10:00:00",
            }
        ],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(return_value=mock_response))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, total = await scrape_af(["Python"], "Göteborg")

    assert total == 42
    assert len(results) == 1


@pytest.mark.asyncio
async def test_always_fetches_from_offset_zero():
    mock_response = MagicMock()
    mock_response.json.return_value = {"total": {"value": 42}, "hits": []}
    mock_response.raise_for_status = MagicMock()

    captured_params = {}

    async def capture_get(url, **kwargs):
        captured_params.update(kwargs.get("params", {}))
        return mock_response

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(side_effect=capture_get))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        await scrape_af(["Python"], "Göteborg")

    assert captured_params.get("offset") == 0


# --- _candidate_query_tiers ---

def test_candidate_query_tiers_single_term():
    assert _candidate_query_tiers(["C#"]) == [[["C#"]]]


def test_candidate_query_tiers_empty():
    assert _candidate_query_tiers([]) == [[[]]]


def test_candidate_query_tiers_three_terms_order():
    tiers = _candidate_query_tiers(["A", "B", "C"])
    assert tiers[0] == [["A", "B", "C"]]
    # drop-one-term subsets (favoring dropping the last term first), then singles
    assert tiers[1] == [["A", "B"], ["A", "C"], ["B", "C"]]
    assert tiers[2] == [["A"], ["B"], ["C"]]


# --- fallback when the full term combination returns zero hits ---

@pytest.mark.asyncio
async def test_falls_back_to_fewer_terms_when_combined_query_has_zero_hits():
    """Regression: "C#, Yrkeshögskolelärare, programmering" returned 0 hits
    from the real AF API because "Yrkeshögskolelärare" as one compound word
    doesn't match anything, dragging the whole combined query to zero even
    though "C#" alone has plenty of hits."""

    async def capture_get(url, **kwargs):
        q = kwargs.get("params", {}).get("q", "")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        if "Yrkeshögskolelärare" in q:
            mock_response.json.return_value = {"total": {"value": 0}, "hits": []}
        else:
            mock_response.json.return_value = {
                "total": {"value": 34},
                "hits": [{
                    "headline": "C# Developer",
                    "employer": {"name": "Acme AB"},
                    "workplace_address": {"city": "Göteborg"},
                    "webpage_url": "https://example.com/job/1",
                }],
            }
        return mock_response

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(side_effect=capture_get))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, total = await scrape_af(["C#", "Yrkeshögskolelärare", "programmering"], "Göteborg")

    assert total == 34
    assert len(results) == 1
    assert results[0].name == "Acme AB"


@pytest.mark.asyncio
async def test_falls_back_when_full_query_returns_too_few_hits():
    """Regression: "C#, YH, lärare" (Göteborg) returned only 1 hit combined
    even though "C#, lärare" alone has 34 — not an exact zero, so the
    fallback needs to trigger on a too-low count too, not just total==0."""

    def total_for(q: str) -> int:
        has_c, has_yh, has_l = "C#" in q, "YH" in q, "lärare" in q
        if has_c and has_yh:
            return 1  # true whether or not "lärare" is also present
        if has_c and has_l:
            return 34
        if has_yh and has_l:
            return 5
        if has_c:
            return 34
        if has_yh:
            return 5
        if has_l:
            return 94
        return 0

    async def capture_get(url, **kwargs):
        q = kwargs.get("params", {}).get("q", "")
        total = total_for(q)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "total": {"value": total},
            "hits": [{
                "headline": f"Match ({total})",
                "employer": {"name": "Acme AB"},
                "workplace_address": {"city": "Göteborg"},
                "webpage_url": "https://example.com/job/1",
            }] if total else [],
        }
        return mock_response

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(side_effect=capture_get))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, total = await scrape_af(["C#", "YH", "lärare"], "Göteborg", all_sweden=True)

    assert total == 34
    assert len(results) == 1


@pytest.mark.asyncio
async def test_returns_best_subset_when_none_clear_threshold():
    """If nothing reaches the threshold, return the best-scoring subset seen
    — not whichever subset happened to be tried last."""

    async def capture_get(url, **kwargs):
        q = kwargs.get("params", {}).get("q", "")
        total = 3 if q.strip() == "A Göteborg" else 0
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "total": {"value": total},
            "hits": [{
                "headline": "Match",
                "employer": {"name": "Niche AB"},
                "workplace_address": {"city": "Göteborg"},
                "webpage_url": "https://example.com/job/1",
            }] if total else [],
        }
        return mock_response

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(side_effect=capture_get))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, total = await scrape_af(["A", "B"], "Göteborg")

    assert total == 3
    assert len(results) == 1
    assert results[0].name == "Niche AB"


@pytest.mark.asyncio
async def test_merges_independent_single_terms_when_combo_never_co_occurs():
    """Regression: "java, lärare" and "lärare, java" gave completely
    different results — whichever term was listed/tried first "won" and
    silently hid the other term's results, because the combined query has
    0 hits and the old fallback stopped at the first single term clearing
    the threshold. Both orderings must now return the same merged set."""

    async def capture_get(url, **kwargs):
        q = kwargs.get("params", {}).get("q", "")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        if "java" in q and "lärare" in q:
            total, hits = 0, []
        elif "java" in q:
            total, hits = 43, [{
                "headline": "Java Developer", "employer": {"name": "JavaCo AB"},
                "workplace_address": {"city": "Göteborg"}, "webpage_url": "https://example.com/java",
            }]
        else:
            total, hits = 94, [{
                "headline": "Lärare", "employer": {"name": "Skolan AB"},
                "workplace_address": {"city": "Göteborg"}, "webpage_url": "https://example.com/larare",
            }]
        mock_response.json.return_value = {"total": {"value": total}, "hits": hits}
        return mock_response

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(side_effect=capture_get))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results_a, total_a = await scrape_af(["java", "lärare"], "Göteborg", all_sweden=True)
        results_b, total_b = await scrape_af(["lärare", "java"], "Göteborg", all_sweden=True)

    for results, total in [(results_a, total_a), (results_b, total_b)]:
        assert total == 43 + 94
        assert {c.name for c in results} == {"JavaCo AB", "Skolan AB"}


@pytest.mark.asyncio
async def test_merge_gives_each_term_an_even_share_of_limit():
    """Regression: merging used to fetch `limit` per term then truncate the
    combined list afterward, so whichever term was queried first still
    silently dominated the final results even though the total-hits count
    had become order-independent. Each term must get its own share of
    `limit` instead."""
    captured_limits: list[int] = []

    async def capture_get(url, **kwargs):
        captured_limits.append(kwargs.get("params", {}).get("limit"))
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"total": {"value": 0}, "hits": []}
        return mock_response

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(side_effect=capture_get))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        await scrape_af(["java", "lärare"], "Göteborg", all_sweden=True, limit=20)

    # 1 call for the combined query (0 hits) + 2 calls for the single terms,
    # each capped at limit // 2 = 10
    assert captured_limits[-2:] == [10, 10]


@pytest.mark.asyncio
async def test_merge_dedupes_by_job_url():
    async def capture_get(url, **kwargs):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "total": {"value": 1},
            "hits": [{
                "headline": "Same job seen twice",
                "employer": {"name": "Acme AB"},
                "workplace_address": {"city": "Göteborg"},
                "webpage_url": "https://example.com/same-job",
            }],
        }
        return mock_response

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(side_effect=capture_get))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, total = await scrape_af(["Alpha", "Beta"], "Göteborg", all_sweden=True)

    # both single-term queries return the same ad — should be merged to one
    assert len(results) == 1


@pytest.mark.asyncio
async def test_returns_zero_result_when_every_subset_is_empty():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"total": {"value": 0}, "hits": []}

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(return_value=mock_response))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, total = await scrape_af(["Nonexistent", "Termer"], "Göteborg")

    assert total == 0
    assert results == []
