"""Gera roteiro viral usando Claude API com o prompt Rony Roteiros."""

import json
import logging
import urllib.request
import urllib.error

import config
from prompt_template import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def generate_script(transcription: str, reels_url: str) -> str | None:
    """Envia a transcrição para Claude e recebe o roteiro viral."""
    if not config.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY não configurada")
        return None

    user_message = USER_PROMPT_TEMPLATE.format(
        transcription=transcription,
        url=reels_url,
    )

    body = {
        "model": config.CLAUDE_MODEL,
        "max_tokens": 2048,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": user_message},
        ],
    }

    logger.info("Gerando roteiro com Claude (%s)...", config.CLAUDE_MODEL)

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=data,
        headers={
            "x-api-key": config.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())

        # Extrai o texto da resposta
        content_blocks = result.get("content", [])
        text_parts = []
        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block["text"])

        roteiro = "\n".join(text_parts)

        if roteiro:
            logger.info("Roteiro gerado com sucesso (%d caracteres)", len(roteiro))
            return roteiro
        else:
            logger.error("Resposta vazia do Claude")
            return None

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        logger.error("Erro na API Claude: %s - %s", e.code, error_body)
        return None
    except Exception as e:
        logger.error("Erro ao gerar roteiro: %s", e)
        return None
