"""
Cliente wrapper para a API do Notion v1.
Usa apenas a stdlib do Python (urllib) — zero dependências externas para o core.
"""

import json
import urllib.request
import urllib.error
from typing import Any

from config import BASE_URL, get_headers


class NotionAPIError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message
        super().__init__(f"[{status}] {code}: {message}")


def _request(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=get_headers(), method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read().decode())
        raise NotionAPIError(
            status=e.code,
            code=error_body.get("code", "unknown"),
            message=error_body.get("message", str(e)),
        )


# ── Databases ────────────────────────────────────────────────────────────────


def search_databases(query: str = "", page_size: int = 20, start_cursor: str | None = None) -> dict:
    """Busca databases acessíveis pela integração."""
    payload: dict[str, Any] = {
        "filter": {"value": "database", "property": "object"},
        "page_size": page_size,
    }
    if query:
        payload["query"] = query
    if start_cursor:
        payload["start_cursor"] = start_cursor
    return _request("POST", "/search", payload)


def get_database(database_id: str) -> dict:
    """Retorna os detalhes de um database específico."""
    return _request("GET", f"/databases/{database_id}")


def create_database(parent_page_id: str, title: str, properties: dict) -> dict:
    """Cria um novo database dentro de uma página."""
    body = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": properties,
    }
    return _request("POST", "/databases", body)


def update_database(database_id: str, updates: dict) -> dict:
    """Atualiza título e/ou propriedades de um database."""
    return _request("PATCH", f"/databases/{database_id}", updates)


def query_database(
    database_id: str,
    filter: dict | None = None,
    sorts: list | None = None,
    page_size: int = 100,
    start_cursor: str | None = None,
) -> dict:
    """Consulta registros (pages) dentro de um database com filtros e ordenação."""
    payload: dict[str, Any] = {"page_size": page_size}
    if filter:
        payload["filter"] = filter
    if sorts:
        payload["sorts"] = sorts
    if start_cursor:
        payload["start_cursor"] = start_cursor
    return _request("POST", f"/databases/{database_id}/query", payload)


# ── Pages ────────────────────────────────────────────────────────────────────


def get_page(page_id: str) -> dict:
    """Retorna os detalhes de uma página."""
    return _request("GET", f"/pages/{page_id}")


def create_page(parent: dict, properties: dict, children: list | None = None) -> dict:
    """
    Cria uma nova página.
    parent: {"database_id": "..."} ou {"page_id": "..."}
    """
    body: dict[str, Any] = {"parent": parent, "properties": properties}
    if children:
        body["children"] = children
    return _request("POST", "/pages", body)


def update_page(page_id: str, properties: dict) -> dict:
    """Atualiza propriedades de uma página existente."""
    return _request("PATCH", f"/pages/{page_id}", {"properties": properties})


def archive_page(page_id: str) -> dict:
    """Arquiva (soft delete) uma página."""
    return _request("PATCH", f"/pages/{page_id}", {"archived": True})


def restore_page(page_id: str) -> dict:
    """Restaura uma página arquivada."""
    return _request("PATCH", f"/pages/{page_id}", {"archived": False})


# ── Blocks (conteúdo das páginas) ────────────────────────────────────────────


def get_block_children(block_id: str, page_size: int = 100, start_cursor: str | None = None) -> dict:
    """Lista os blocos filhos de uma página ou bloco."""
    params = f"?page_size={page_size}"
    if start_cursor:
        params += f"&start_cursor={start_cursor}"
    return _request("GET", f"/blocks/{block_id}/children{params}")


def append_block_children(block_id: str, children: list[dict]) -> dict:
    """Adiciona blocos de conteúdo a uma página ou bloco."""
    return _request("PATCH", f"/blocks/{block_id}/children", {"children": children})


def delete_block(block_id: str) -> dict:
    """Deleta um bloco específico."""
    return _request("DELETE", f"/blocks/{block_id}")


# ── Users ────────────────────────────────────────────────────────────────────


def list_users(page_size: int = 100, start_cursor: str | None = None) -> dict:
    """Lista os usuários do workspace."""
    params = f"?page_size={page_size}"
    if start_cursor:
        params += f"&start_cursor={start_cursor}"
    return _request("GET", f"/users{params}")


def get_user(user_id: str) -> dict:
    """Retorna detalhes de um usuário."""
    return _request("GET", f"/users/{user_id}")
