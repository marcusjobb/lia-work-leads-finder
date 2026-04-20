import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv()


async def complete(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "claude-cli")
    if provider == "claude-cli":
        try:
            return await _claude_cli(prompt)
        except Exception as e:
            print(f"[llm_client] claude-cli failed ({e}), falling back to OpenRouter")
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
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", "minimax/minimax-01")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _anthropic(prompt: str) -> str:
    import anthropic as _anthropic_sdk
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    client = _anthropic_sdk.AsyncAnthropic(api_key=api_key)
    msg = await client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text
