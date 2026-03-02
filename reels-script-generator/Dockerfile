FROM python:3.12-slim

# Instala ffmpeg (necessário para yt-dlp extrair áudio)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Modo watch: roda em loop verificando novas entradas
CMD ["python", "main.py", "--watch"]
