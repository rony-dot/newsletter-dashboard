"""Pipeline principal: Notion DB → Reels → Transcrição → Roteiro → Notion DB.

Uso:
    python main.py              # Roda uma vez
    python main.py --watch      # Roda em loop (a cada N minutos)
    python main.py --dry-run    # Mostra o que faria sem executar
"""

import sys
import time
import logging
import argparse

import config
from notion_handler import (
    get_pending_reels,
    ensure_roteiro_property,
    update_page_status,
    write_roteiro,
)
from reels_processor import transcribe_reels, cleanup
from script_generator import generate_script

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline")


def validate_config():
    """Valida que todas as configurações obrigatórias estão presentes."""
    missing = []
    if not config.NOTION_API_KEY:
        missing.append("NOTION_API_KEY")
    if not config.NOTION_DATABASE_ID:
        missing.append("NOTION_DATABASE_ID")
    if not config.ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")

    if missing:
        logger.error("Variáveis de ambiente obrigatórias faltando: %s", ", ".join(missing))
        sys.exit(1)

    if not config.GROQ_API_KEY:
        logger.warning(
            "GROQ_API_KEY não configurada. Transcrição dependerá apenas de legendas automáticas."
        )


def process_single(entry: dict, dry_run: bool = False) -> bool:
    """Processa uma única entrada: transcreve Reels e gera roteiro."""
    page_id = entry["page_id"]
    reels_url = entry["reels_url"]

    logger.info("=" * 60)
    logger.info("Processando: %s", reels_url)
    logger.info("Página: %s", page_id)

    if dry_run:
        logger.info("[DRY RUN] Pulando processamento real")
        return True

    # Marca como processando
    try:
        update_page_status(page_id, "Processando")
    except Exception as e:
        logger.warning("Não foi possível atualizar status: %s", e)

    # 1. Transcreve o Reels
    logger.info("Etapa 1/3: Transcrevendo Reels...")
    transcription = transcribe_reels(reels_url)
    if not transcription:
        logger.error("Falha na transcrição de %s", reels_url)
        try:
            update_page_status(page_id, "Erro")
        except Exception:
            pass
        return False

    logger.info("Transcrição obtida (%d caracteres)", len(transcription))

    # 2. Gera o roteiro
    logger.info("Etapa 2/3: Gerando roteiro com Claude...")
    roteiro = generate_script(transcription, reels_url)
    if not roteiro:
        logger.error("Falha na geração do roteiro para %s", reels_url)
        try:
            update_page_status(page_id, "Erro")
        except Exception:
            pass
        return False

    logger.info("Roteiro gerado (%d caracteres)", len(roteiro))

    # 3. Salva no Notion
    logger.info("Etapa 3/3: Salvando roteiro no Notion...")
    try:
        write_roteiro(page_id, roteiro)
        logger.info("Roteiro salvo com sucesso!")
        return True
    except Exception as e:
        logger.error("Erro ao salvar roteiro no Notion: %s", e)
        try:
            update_page_status(page_id, "Erro")
        except Exception:
            pass
        return False


def run_pipeline(dry_run: bool = False):
    """Executa o pipeline completo uma vez."""
    logger.info("Iniciando pipeline Reels → Roteiro")

    # Garante que as propriedades existem no DB
    if not dry_run:
        ensure_roteiro_property()

    # Busca entradas pendentes
    pending = get_pending_reels()
    if not pending:
        logger.info("Nenhum Reels pendente para processar")
        return

    logger.info("Encontrados %d Reels para processar", len(pending))

    success = 0
    errors = 0

    for entry in pending:
        try:
            if process_single(entry, dry_run):
                success += 1
            else:
                errors += 1
        except Exception as e:
            logger.error("Erro inesperado processando %s: %s", entry["reels_url"], e)
            errors += 1

    logger.info("=" * 60)
    logger.info("Pipeline concluído: %d sucesso, %d erros", success, errors)

    # Limpa arquivos temporários
    cleanup()


def main():
    parser = argparse.ArgumentParser(description="Reels → Roteiro Viral Pipeline")
    parser.add_argument(
        "--watch",
        action="store_true",
        help=f"Roda em loop a cada {config.CHECK_INTERVAL_MINUTES} minutos",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o que faria sem executar",
    )
    args = parser.parse_args()

    validate_config()

    if args.watch:
        logger.info(
            "Modo watch: verificando a cada %d minutos", config.CHECK_INTERVAL_MINUTES
        )
        while True:
            try:
                run_pipeline(dry_run=args.dry_run)
            except Exception as e:
                logger.error("Erro no ciclo do pipeline: %s", e)
            logger.info(
                "Próxima verificação em %d minutos...", config.CHECK_INTERVAL_MINUTES
            )
            time.sleep(config.CHECK_INTERVAL_MINUTES * 60)
    else:
        run_pipeline(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
