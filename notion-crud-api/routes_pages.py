"""Rotas CRUD para Notion Pages e Blocks."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import notion_client
from notion_client import NotionAPIError

router = APIRouter(prefix="/pages", tags=["Pages"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class CreatePageInDatabaseRequest(BaseModel):
    database_id: str
    properties: dict
    children: list[dict] | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "database_id": "database-id-aqui",
                    "properties": {
                        "Nome": {"title": [{"text": {"content": "Minha página"}}]},
                        "Status": {"select": {"name": "A fazer"}},
                    },
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": "Conteúdo aqui."}}]
                            },
                        }
                    ],
                }
            ]
        }
    }


class CreatePageInPageRequest(BaseModel):
    page_id: str
    title: str
    children: list[dict] | None = None


class UpdatePageRequest(BaseModel):
    properties: dict


class AppendBlocksRequest(BaseModel):
    children: list[dict]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "children": [
                        {
                            "object": "block",
                            "type": "heading_2",
                            "heading_2": {
                                "rich_text": [{"type": "text", "text": {"content": "Seção nova"}}]
                            },
                        },
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": "Texto do parágrafo."}}]
                            },
                        },
                    ]
                }
            ]
        }
    }


# ── Helpers ──────────────────────────────────────────────────────────────────


def _handle(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except NotionAPIError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})


# ── Page endpoints ───────────────────────────────────────────────────────────


@router.get("/{page_id}", summary="Obter detalhes de uma página")
def get_page(page_id: str):
    """Retorna propriedades e metadados de uma página."""
    return _handle(notion_client.get_page, page_id)


@router.post("/in-database", summary="Criar página em um database", status_code=201)
def create_page_in_database(req: CreatePageInDatabaseRequest):
    """Cria uma nova página (registro) dentro de um database."""
    parent = {"database_id": req.database_id}
    return _handle(notion_client.create_page, parent, req.properties, req.children)


@router.post("/in-page", summary="Criar sub-página dentro de uma página", status_code=201)
def create_page_in_page(req: CreatePageInPageRequest):
    """Cria uma sub-página dentro de outra página."""
    parent = {"page_id": req.page_id}
    properties = {"title": [{"type": "text", "text": {"content": req.title}}]}
    return _handle(notion_client.create_page, parent, properties, req.children)


@router.patch("/{page_id}", summary="Atualizar propriedades da página")
def update_page(page_id: str, req: UpdatePageRequest):
    """Atualiza as propriedades de uma página existente."""
    return _handle(notion_client.update_page, page_id, req.properties)


@router.delete("/{page_id}", summary="Arquivar (deletar) uma página")
def archive_page(page_id: str):
    """Arquiva uma página (soft delete — pode ser restaurada)."""
    return _handle(notion_client.archive_page, page_id)


@router.post("/{page_id}/restore", summary="Restaurar página arquivada")
def restore_page(page_id: str):
    """Restaura uma página que foi arquivada."""
    return _handle(notion_client.restore_page, page_id)


# ── Block/Content endpoints ──────────────────────────────────────────────────


@router.get("/{page_id}/blocks", summary="Listar conteúdo (blocos) da página")
def get_page_blocks(
    page_id: str,
    page_size: int = Query(100, ge=1, le=100),
    start_cursor: str | None = Query(None),
):
    """Retorna os blocos de conteúdo de uma página (parágrafos, headings, etc.)."""
    return _handle(notion_client.get_block_children, page_id, page_size, start_cursor)


@router.post("/{page_id}/blocks", summary="Adicionar conteúdo à página", status_code=201)
def append_blocks(page_id: str, req: AppendBlocksRequest):
    """Adiciona novos blocos de conteúdo ao final de uma página."""
    return _handle(notion_client.append_block_children, page_id, req.children)


@router.delete("/blocks/{block_id}", summary="Deletar um bloco")
def delete_block(block_id: str):
    """Remove um bloco de conteúdo específico."""
    return _handle(notion_client.delete_block, block_id)
