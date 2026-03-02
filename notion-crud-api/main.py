"""
Notion CRUD API
───────────────
API REST para gerenciar databases, páginas e conteúdo no Notion.
Documentação interativa disponível em /docs (Swagger UI).

Como rodar:
    export NOTION_API_KEY="secret_..."
    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import NOTION_API_KEY
from routes_databases import router as databases_router
from routes_pages import router as pages_router

app = FastAPI(
    title="Notion CRUD API",
    description=(
        "API REST para operações CRUD no Notion.\n\n"
        "**Funcionalidades:**\n"
        "- Databases: buscar, criar, atualizar, consultar registros\n"
        "- Pages: criar, ler, atualizar, arquivar/restaurar\n"
        "- Blocks: ler conteúdo, adicionar blocos, deletar blocos\n"
        "- Users: listar usuários do workspace\n\n"
        "Configure a variável de ambiente `NOTION_API_KEY` com seu token de integração."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(databases_router)
app.include_router(pages_router)


# ── Rotas utilitárias ────────────────────────────────────────────────────────


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "service": "Notion CRUD API",
        "docs": "/docs",
        "configured": bool(NOTION_API_KEY),
    }


@app.get("/users", tags=["Users"], summary="Listar usuários do workspace")
def list_users():
    import notion_client
    from notion_client import NotionAPIError
    from fastapi import HTTPException

    try:
        return notion_client.list_users()
    except NotionAPIError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})


@app.get("/users/{user_id}", tags=["Users"], summary="Obter detalhes de um usuário")
def get_user(user_id: str):
    import notion_client
    from notion_client import NotionAPIError
    from fastapi import HTTPException

    try:
        return notion_client.get_user(user_id)
    except NotionAPIError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})
