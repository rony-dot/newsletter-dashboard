"""Configuração centralizada via variáveis de ambiente."""

import os
from dotenv import load_dotenv

load_dotenv()

# === APIs ===
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# === Notion: nomes das propriedades do DB ===
# Propriedade que contém o link do Reels (tipo URL ou rich_text)
REELS_LINK_PROPERTY = os.getenv("REELS_LINK_PROPERTY", "URL")
# Propriedade onde o roteiro será salvo (será criada se não existir)
ROTEIRO_PROPERTY = os.getenv("ROTEIRO_PROPERTY", "Roteiro Proposto")
# Propriedade de status para marcar que já foi processado
STATUS_PROPERTY = os.getenv("STATUS_PROPERTY", "Status Roteiro")

# === Modelo Claude ===
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# === Pipeline ===
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/reels-processor")

# === Notion API ===
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
