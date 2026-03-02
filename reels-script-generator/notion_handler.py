"""Lê entradas do Notion DB, detecta links de Reels, e escreve roteiros de volta."""

import re
import json
import logging
import urllib.request
import urllib.error

import config

logger = logging.getLogger(__name__)

INSTAGRAM_REELS_PATTERN = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:reel|reels|p)/[\w-]+/?",
    re.IGNORECASE,
)


def _notion_request(method: str, endpoint: str, body: dict | None = None) -> dict:
    """Faz requisição à API do Notion."""
    url = f"{config.NOTION_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {config.NOTION_API_KEY}",
        "Notion-Version": config.NOTION_VERSION,
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        logger.error("Notion API %s %s → %s: %s", method, endpoint, e.code, error_body)
        raise


def _extract_reels_url(page: dict) -> str | None:
    """Extrai URL de Reels de qualquer propriedade da página."""
    props = page.get("properties", {})

    # 1. Tenta a propriedade configurada como link
    link_prop = props.get(config.REELS_LINK_PROPERTY, {})
    url_value = link_prop.get("url")
    if url_value and INSTAGRAM_REELS_PATTERN.search(url_value):
        return url_value

    # 2. Busca em qualquer propriedade URL
    for prop in props.values():
        if prop.get("type") == "url" and prop.get("url"):
            if INSTAGRAM_REELS_PATTERN.search(prop["url"]):
                return prop["url"]

    # 3. Busca em propriedades rich_text e title
    for prop in props.values():
        prop_type = prop.get("type")
        if prop_type in ("rich_text", "title"):
            texts = prop.get(prop_type, [])
            full_text = "".join(t.get("plain_text", "") for t in texts)
            match = INSTAGRAM_REELS_PATTERN.search(full_text)
            if match:
                return match.group(0)

    return None


def _has_roteiro(page: dict) -> bool:
    """Verifica se a página já tem um roteiro gerado."""
    props = page.get("properties", {})
    roteiro_prop = props.get(config.ROTEIRO_PROPERTY, {})

    if roteiro_prop.get("type") == "rich_text":
        texts = roteiro_prop.get("rich_text", [])
        content = "".join(t.get("plain_text", "") for t in texts)
        return len(content.strip()) > 0

    return False


def get_pending_reels() -> list[dict]:
    """Busca entradas do DB que têm link de Reels mas ainda não têm roteiro."""
    logger.info("Consultando Notion DB: %s", config.NOTION_DATABASE_ID)

    all_pages = []
    has_more = True
    start_cursor = None

    while has_more:
        body = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor

        result = _notion_request(
            "POST",
            f"/databases/{config.NOTION_DATABASE_ID}/query",
            body,
        )
        all_pages.extend(result.get("results", []))
        has_more = result.get("has_more", False)
        start_cursor = result.get("next_cursor")

    pending = []
    for page in all_pages:
        reels_url = _extract_reels_url(page)
        if reels_url and not _has_roteiro(page):
            pending.append({
                "page_id": page["id"],
                "reels_url": reels_url,
                "properties": page.get("properties", {}),
            })

    logger.info("Encontradas %d entradas com Reels pendentes de roteiro", len(pending))
    return pending


def ensure_roteiro_property():
    """Garante que a propriedade 'Roteiro Proposto' existe no DB."""
    logger.info("Verificando se propriedade '%s' existe no DB", config.ROTEIRO_PROPERTY)

    db = _notion_request("GET", f"/databases/{config.NOTION_DATABASE_ID}")
    props = db.get("properties", {})

    if config.ROTEIRO_PROPERTY not in props:
        logger.info("Criando propriedade '%s' no DB", config.ROTEIRO_PROPERTY)
        _notion_request(
            "PATCH",
            f"/databases/{config.NOTION_DATABASE_ID}",
            {
                "properties": {
                    config.ROTEIRO_PROPERTY: {"rich_text": {}},
                }
            },
        )
        logger.info("Propriedade '%s' criada com sucesso", config.ROTEIRO_PROPERTY)
    else:
        logger.info("Propriedade '%s' já existe", config.ROTEIRO_PROPERTY)

    # Também garante a propriedade de status
    if config.STATUS_PROPERTY not in props:
        logger.info("Criando propriedade '%s' no DB", config.STATUS_PROPERTY)
        _notion_request(
            "PATCH",
            f"/databases/{config.NOTION_DATABASE_ID}",
            {
                "properties": {
                    config.STATUS_PROPERTY: {
                        "select": {
                            "options": [
                                {"name": "Pendente", "color": "yellow"},
                                {"name": "Processando", "color": "blue"},
                                {"name": "Concluído", "color": "green"},
                                {"name": "Erro", "color": "red"},
                            ]
                        }
                    },
                }
            },
        )


def update_page_status(page_id: str, status: str):
    """Atualiza o status de processamento de uma página."""
    _notion_request(
        "PATCH",
        f"/pages/{page_id}",
        {
            "properties": {
                config.STATUS_PROPERTY: {
                    "select": {"name": status},
                },
            }
        },
    )


def write_roteiro(page_id: str, roteiro: str):
    """Escreve o roteiro gerado na propriedade da página.

    Notion limita rich_text a 2000 caracteres por bloco,
    então dividimos o texto se necessário.
    """
    MAX_CHUNK = 2000
    chunks = []
    for i in range(0, len(roteiro), MAX_CHUNK):
        chunks.append({
            "type": "text",
            "text": {"content": roteiro[i:i + MAX_CHUNK]},
        })

    _notion_request(
        "PATCH",
        f"/pages/{page_id}",
        {
            "properties": {
                config.ROTEIRO_PROPERTY: {
                    "rich_text": chunks,
                },
                config.STATUS_PROPERTY: {
                    "select": {"name": "Concluído"},
                },
            }
        },
    )
    logger.info("Roteiro salvo na página %s (%d caracteres)", page_id, len(roteiro))
