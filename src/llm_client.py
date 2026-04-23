import asyncio
import logging
import os

import httpx

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    SITE_URL,
)

_log = logging.getLogger(__name__)


async def complete(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "claude-cli")
    if provider == "claude-cli":
        try:
            return await _claude_cli(prompt)
        except Exception as e:
            _log.warning("claude-cli failed (%s), falling back to OpenRouter", e)
            return await _openrouter(prompt)
    if provider == "openrouter":
        return await _openrouter(prompt)
    if provider == "anthropic":
        return await _anthropic(prompt)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


async def _claude_cli(prompt: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "claude", "--print", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err = stderr.decode().strip() or stdout.decode().strip()
        raise RuntimeError(f"exit {proc.returncode}: {err}")
    output = stdout.decode().strip()
    if not output:
        raise RuntimeError("claude-cli returned empty output")
    return output


async def _openrouter(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": SITE_URL,
                "X-Title": "LIA Leads Finder",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        if not resp.is_success:
            raise RuntimeError(f"OpenRouter {resp.status_code}: {resp.text[:300]}")
        return resp.json()["choices"][0]["message"]["content"]


async def _anthropic(prompt: str) -> str:
    import anthropic as _anthropic_sdk
    client = _anthropic_sdk.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    msg = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text
