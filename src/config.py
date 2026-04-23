import os
from dotenv import load_dotenv

load_dotenv()

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude-cli")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "minimax/minimax-01")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

# Company data APIs (optional — guest mode works without keys)
FORETAGSAPI_KEY = os.getenv("FORETAGSAPI_KEY", "")
BOLAGSAPI_KEY = os.getenv("BOLAGSAPI_KEY", "")
