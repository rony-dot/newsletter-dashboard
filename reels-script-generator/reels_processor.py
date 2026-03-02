"""Baixa Reels do Instagram e transcreve o áudio."""

import os
import json
import logging
import subprocess
import tempfile
import urllib.request
import urllib.error

import config

logger = logging.getLogger(__name__)


def _ensure_temp_dir():
    os.makedirs(config.TEMP_DIR, exist_ok=True)


def download_reels(url: str) -> str | None:
    """Baixa o vídeo do Reels usando yt-dlp. Retorna o caminho do arquivo."""
    _ensure_temp_dir()
    output_path = os.path.join(config.TEMP_DIR, "%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--format", "bestaudio[ext=m4a]/bestaudio/best",
        "--output", output_path,
        "--no-overwrites",
        "--extract-audio",
        "--audio-format", "mp3",
        "--quiet",
        "--no-warnings",
        url,
    ]

    logger.info("Baixando Reels: %s", url)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error("yt-dlp falhou: %s", result.stderr)
            return None
    except subprocess.TimeoutExpired:
        logger.error("Timeout ao baixar Reels: %s", url)
        return None
    except FileNotFoundError:
        logger.error("yt-dlp não encontrado. Instale com: pip install yt-dlp")
        return None

    # Encontra o arquivo baixado
    for f in os.listdir(config.TEMP_DIR):
        if f.endswith(".mp3"):
            path = os.path.join(config.TEMP_DIR, f)
            logger.info("Áudio extraído: %s", path)
            return path

    logger.error("Nenhum arquivo de áudio encontrado após download")
    return None


def get_subtitles(url: str) -> str | None:
    """Tenta obter legendas/subtítulos do Reels (mais rápido que transcrever)."""
    _ensure_temp_dir()

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--write-auto-sub",
        "--sub-lang", "pt,en",
        "--skip-download",
        "--sub-format", "json3",
        "--output", os.path.join(config.TEMP_DIR, "%(id)s"),
        "--quiet",
        url,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    # Procura arquivos de legenda
    for f in os.listdir(config.TEMP_DIR):
        if f.endswith((".json3", ".vtt", ".srt")):
            path = os.path.join(config.TEMP_DIR, f)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                # Para json3, extrai o texto
                if f.endswith(".json3"):
                    data = json.loads(content)
                    events = data.get("events", [])
                    texts = []
                    for event in events:
                        segs = event.get("segs", [])
                        for seg in segs:
                            t = seg.get("utf8", "").strip()
                            if t and t != "\n":
                                texts.append(t)
                    text = " ".join(texts)
                else:
                    text = content
                if text.strip():
                    logger.info("Legendas encontradas para o Reels")
                    return text.strip()
            except Exception as e:
                logger.warning("Erro ao ler legenda %s: %s", f, e)

    return None


def transcribe_with_groq(audio_path: str) -> str | None:
    """Transcreve áudio usando Groq Whisper API (grátis)."""
    if not config.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY não configurada")
        return None

    logger.info("Transcrevendo com Groq Whisper...")

    # Lê o arquivo de áudio
    with open(audio_path, "rb") as f:
        audio_data = f.read()

    # Prepara multipart form data manualmente
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    filename = os.path.basename(audio_path)

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: audio/mpeg\r\n\r\n"
    ).encode() + audio_data + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"whisper-large-v3-turbo"
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="language"\r\n\r\n'
        f"pt"
        f"\r\n--{boundary}--\r\n"
    ).encode()

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {config.GROQ_API_KEY}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            text = result.get("text", "")
            if text:
                logger.info("Transcrição Groq concluída (%d caracteres)", len(text))
                return text
    except Exception as e:
        logger.error("Erro na transcrição Groq: %s", e)

    return None


def transcribe_reels(url: str) -> str | None:
    """Pipeline de transcrição: tenta legendas primeiro, depois áudio.

    Estratégia:
    1. Tenta extrair legendas automáticas (grátis, instantâneo)
    2. Se não encontrar, baixa áudio e transcreve com Groq Whisper
    """
    # 1. Tenta legendas primeiro
    subtitles = get_subtitles(url)
    if subtitles:
        return subtitles

    # 2. Baixa e transcreve áudio
    audio_path = download_reels(url)
    if not audio_path:
        logger.error("Não foi possível baixar o áudio do Reels")
        return None

    try:
        # Groq Whisper (grátis)
        transcript = transcribe_with_groq(audio_path)
        if transcript:
            return transcript

        logger.error("Nenhum provedor de transcrição disponível. Configure GROQ_API_KEY.")
        return None
    finally:
        # Limpa arquivo temporário
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)


def cleanup():
    """Remove arquivos temporários."""
    import shutil
    if os.path.exists(config.TEMP_DIR):
        shutil.rmtree(config.TEMP_DIR, ignore_errors=True)
