"""Relatório semanal de avaliações da newsletter (poll "O que achou da edição").

Cruza as respostas das enquetes do Beehiiv com os posts enviados por email,
calculando a nota média de cada edição (escala 1 a 5).

Gera:
  - ratings_report.md   (tabela markdown completa)
  - ratings_report.csv  (mesma tabela em CSV)
  - ratings_report.html (tabela estilizada para abrir no navegador)

Uso:
    python ratings_report.py
"""

import os
import csv
import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from collections import defaultdict

API_KEY = os.environ.get(
    "BEEHIIV_API_KEY",
    "ei1tQq53TAgqvrZUZyHQzdRkQMbGi7jQVwNfvz8Im8xrk50HmwuasocTiqPyS7mF",
)
PUB_ID = os.environ.get(
    "BEEHIIV_PUB_ID",
    "pub_cd564848-7cb2-4ba8-a802-2d1bd27040dc",
)

BASE = f"https://api.beehiiv.com/v2/publications/{PUB_ID}"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Escala de notas a partir do rótulo da opção
def label_to_score(label: str):
    l = label.lower().strip()
    if "muito boa" in l:
        return 5
    if "péssima" in l or "pessima" in l:
        return 1
    if "ruim" in l:
        return 2
    if "mediana" in l:
        return 3
    if "boa" in l:  # depois de "muito boa"
        return 4
    return None


def _get(url: str, retries: int = 4) -> dict:
    """GET com retry e backoff exponencial (Beehiiv às vezes responde 503)."""
    delay = 2
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            # 5xx e 429 são temporários — vale tentar de novo
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except Exception:
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise


def fetch_polls() -> list:
    polls, cursor = [], None
    while True:
        url = f"{BASE}/polls?limit=50"
        if cursor:
            url += f"&cursor={cursor}"
        data = _get(url)
        polls.extend(data["data"])
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    # Só as enquetes de avaliação de edição
    return [
        p for p in polls
        if "achou da edi" in (p.get("name", "") + p.get("question", "")).lower()
    ]


def fetch_poll_responses(poll_id: str) -> list:
    responses, cursor = [], None
    while True:
        url = f"{BASE}/polls/{poll_id}/responses?limit=100"
        if cursor:
            url += f"&cursor={cursor}"
        data = _get(url)
        responses.extend(data["data"])
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return responses


def fetch_email_posts() -> list:
    """Busca posts enviados por email com stats."""
    posts, page = [], 1
    while True:
        url = f"{BASE}/posts?limit=50&page={page}&expand[]=stats&status=confirmed&order_by=publish_date&direction=asc"
        data = _get(url)
        posts.extend(data["data"])
        total_pages = data.get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1

    email_posts = []
    for p in posts:
        stats = p.get("stats", {}) or {}
        email = stats.get("email", {}) or {}
        recipients = email.get("recipients", 0) or 0
        if recipients <= 0:
            continue
        # publish_date = quando foi enviada; fallback para created
        ts = p.get("publish_date") or p.get("displayed_date") or p.get("created") or 0
        email_posts.append({
            "id": p["id"],
            "title": p.get("title", "") or "(sem título)",
            "ts": ts,
            "date_label": datetime.utcfromtimestamp(ts).strftime("%d/%m/%Y") if ts else "?",
            "open_rate": round((email.get("open_rate", 0) or 0), 1),
            "unique_opens": email.get("unique_opens", 0) or 0,
        })
    email_posts.sort(key=lambda x: x["ts"])
    return email_posts


def build_rows():
    print("📊 Buscando enquetes de avaliação...")
    polls = fetch_polls()
    print(f"  {len(polls)} enquete(s) de avaliação encontrada(s)")

    all_responses = []
    for poll in polls:
        r = fetch_poll_responses(poll["id"])
        print(f"  '{poll['name']}': {len(r)} respostas")
        all_responses.extend(r)

    print("📬 Buscando edições enviadas por email...")
    email_posts = fetch_email_posts()
    print(f"  {len(email_posts)} edições por email")

    # Cada resposta pertence à edição mais recente enviada antes do voto
    post_ts = [(p["ts"], p) for p in email_posts]

    def find_post(resp_ts):
        best = None
        for ts, post in post_ts:
            if ts <= resp_ts:
                best = post
            else:
                break
        return best

    ratings = defaultdict(list)
    for r in all_responses:
        score = label_to_score(r.get("poll_choice_label", ""))
        if score is None:
            continue
        post = find_post(r.get("created_at", 0))
        if post:
            ratings[post["id"]].append(score)

    rows = []
    for p in email_posts:
        scores = ratings.get(p["id"], [])
        if not scores:
            continue  # só edições com avaliação
        rows.append({
            "date": p["date_label"],
            "title": p["title"],
            "open_rate": p["open_rate"],
            "unique_opens": p["unique_opens"],
            "avg_rating": round(sum(scores) / len(scores), 2),
            "votes": len(scores),
        })

    rows.sort(key=lambda x: datetime.strptime(x["date"], "%d/%m/%Y"), reverse=True)
    return rows


def write_csv(rows, path="ratings_report.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Data", "Titulo", "Taxa de Abertura (%)", "Aberturas Unicas", "Nota Media", "Votos"])
        for r in rows:
            w.writerow([r["date"], r["title"], r["open_rate"], r["unique_opens"], r["avg_rating"], r["votes"]])
    print(f"✅ {path}")


def write_markdown(rows, path="ratings_report.md"):
    total_votes = sum(r["votes"] for r in rows)
    weighted = sum(r["avg_rating"] * r["votes"] for r in rows) / total_votes if total_votes else 0
    gen = datetime.now().strftime("%d/%m/%Y %H:%M")
    lines = [
        f"# 📋 Avaliações da Newsletter — {gen}",
        "",
        f"**{len(rows)} edições avaliadas · {total_votes:,} votos · nota média geral {weighted:.2f}/5**".replace(",", "."),
        "",
        "| Data | Título | Taxa de Abertura | Aberturas Únicas | Nota Média | Votos |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        opens = f"{r['unique_opens']:,}".replace(",", ".")
        lines.append(
            f"| {r['date']} | {r['title']} | {r['open_rate']}% | {opens} | {r['avg_rating']} | {r['votes']} |"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ {path}")
    return weighted, total_votes


def write_html(rows, path="ratings_report.html"):
    total_votes = sum(r["votes"] for r in rows)
    weighted = sum(r["avg_rating"] * r["votes"] for r in rows) / total_votes if total_votes else 0
    gen = datetime.now().strftime("%d/%m/%Y %H:%M")

    def color(rating):
        if rating >= 4.5:
            return "#16a34a"
        if rating >= 4.0:
            return "#65a30d"
        if rating >= 3.5:
            return "#ca8a04"
        return "#dc2626"

    body = "".join(
        f"<tr><td>{r['date']}</td><td class='title'>{r['title']}</td>"
        f"<td>{r['open_rate']}%</td><td>{r['unique_opens']:,}</td>"
        f"<td style='color:{color(r['avg_rating'])};font-weight:700'>{r['avg_rating']}</td>"
        f"<td>{r['votes']}</td></tr>".replace(",", ".")
        for r in rows
    )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Avaliações da Newsletter</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; background:#f8fafc; color:#0f172a; margin:0; padding:32px; }}
  .wrap {{ max-width: 1000px; margin:0 auto; }}
  h1 {{ font-size:24px; margin-bottom:4px; }}
  .sub {{ color:#64748b; margin-bottom:24px; }}
  .kpis {{ display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap; }}
  .kpi {{ background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:16px 20px; flex:1; min-width:160px; }}
  .kpi .v {{ font-size:28px; font-weight:700; }}
  .kpi .l {{ color:#64748b; font-size:13px; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  th {{ background:#0f172a; color:#fff; text-align:left; padding:12px; font-size:13px; }}
  td {{ padding:11px 12px; border-top:1px solid #f1f5f9; font-size:14px; }}
  td.title {{ max-width:380px; }}
  tr:hover td {{ background:#f8fafc; }}
</style></head><body><div class="wrap">
<h1>📋 Avaliações da Newsletter</h1>
<div class="sub">Gerado em {gen} · enquete "O que achou da edição de hoje?"</div>
<div class="kpis">
  <div class="kpi"><div class="v">{len(rows)}</div><div class="l">Edições avaliadas</div></div>
  <div class="kpi"><div class="v">{total_votes:,}</div><div class="l">Votos totais</div></div>
  <div class="kpi"><div class="v">{weighted:.2f}</div><div class="l">Nota média geral (/5)</div></div>
</div>
<table>
<thead><tr><th>Data</th><th>Título</th><th>Taxa de Abertura</th><th>Aberturas Únicas</th><th>Nota Média</th><th>Votos</th></tr></thead>
<tbody>{body}</tbody>
</table>
</div></body></html>""".replace("{total_votes:,}", f"{total_votes:,}").replace(",", ".")

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ {path}")


def main():
    rows = build_rows()
    if not rows:
        print("⚠️  Nenhuma edição com avaliação encontrada.")
        return
    write_csv(rows)
    weighted, total = write_markdown(rows)
    write_html(rows)
    print()
    print(f"📊 {len(rows)} edições · {total} votos · nota média geral {weighted:.2f}/5")


if __name__ == "__main__":
    main()
