"""Rotas CRUD para Notion Databases."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import notion_client
from notion_client import NotionAPIError

router = APIRouter(prefix="/databases", tags=["Databases"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class CreateDatabaseRequest(BaseModel):
    parent_page_id: str
    title: str
    properties: dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "parent_page_id": "page-id-aqui",
                    "title": "Meu Database",
                    "properties": {
                        "Nome": {"title": {}},
                        "Status": {
                            "select": {
                                "options": [
                                    {"name": "A fazer", "color": "red"},
                                    {"name": "Em progresso", "color": "yellow"},
                                    {"name": "Feito", "color": "green"},
                                ]
                            }
                        },
                    },
                }
            ]
        }
    }


class UpdateDatabaseRequest(BaseModel):
    title: str | None = None
    properties: dict | None = None


class QueryDatabaseRequest(BaseModel):
    filter: dict | None = None
    sorts: list | None = None
    page_size: int = 100
    start_cursor: str | None = None


# ── Endpoints ────────────────────────────────────────────────────────────────


def _handle(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except NotionAPIError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})


@router.get("/", summary="Buscar databases acessíveis")
def search_databases(
    query: str = Query("", description="Texto para filtrar databases pelo título"),
    page_size: int = Query(20, ge=1, le=100),
    start_cursor: str | None = Query(None),
):
    """Lista todos os databases acessíveis pela integração Notion."""
    return _handle(notion_client.search_databases, query, page_size, start_cursor)


@router.get("/{database_id}", summary="Obter detalhes de um database")
def get_database(database_id: str):
    """Retorna schema e metadados de um database específico."""
    return _handle(notion_client.get_database, database_id)


@router.post("/", summary="Criar novo database", status_code=201)
def create_database(req: CreateDatabaseRequest):
    """Cria um database dentro de uma página do Notion."""
    return _handle(notion_client.create_database, req.parent_page_id, req.title, req.properties)


@router.patch("/{database_id}", summary="Atualizar database")
def update_database(database_id: str, req: UpdateDatabaseRequest):
    """Atualiza título e/ou propriedades de um database."""
    updates = {}
    if req.title is not None:
        updates["title"] = [{"type": "text", "text": {"content": req.title}}]
    if req.properties is not None:
        updates["properties"] = req.properties
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")
    return _handle(notion_client.update_database, database_id, updates)


@router.post("/{database_id}/query", summary="Consultar registros do database")
def query_database(database_id: str, req: QueryDatabaseRequest):
    """Consulta páginas dentro de um database com filtros e ordenação."""
    return _handle(
        notion_client.query_database,
        database_id,
        req.filter,
        req.sorts,
        req.page_size,
        req.start_cursor,
    )
