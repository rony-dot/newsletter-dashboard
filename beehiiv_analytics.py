#!/usr/bin/env python3
"""
Beehiiv Newsletter Analytics
Puxa dados da API do Beehiiv e gera um dashboard interativo HTML.

Uso:
    python beehiiv_analytics.py

Requisitos:
    - Python 3.7+
    - Nenhuma dependência externa (usa apenas bibliotecas padrão)

Autor: Gerado para Rony via Claude
"""

import urllib.request
import json
import os
import sys
from datetime import datetime, timezone
from collections import defaultdict

# ============================================================
# CONFIGURAÇÃO — Edite aqui se necessário
# ============================================================
API_KEY = os.environ.get("BEEHIIV_API_KEY", "ei1tQq53TAgqvrZUZyHQzdRkQMbGi7jQVwNfvz8Im8xrk50HmwuasocTiqPyS7mF")
PUB_ID = os.environ.get("BEEHIIV_PUB_ID", "pub_cd564848-7cb2-4ba8-a802-2d1bd27040dc")
OUTPUT_FILE = "newsletter_dashboard.html"
# Se a API não retornar total_results, usa este valor como fallback.
# Atualize com o número real do seu painel do Beehiiv.
TOTAL_SUBSCRIBERS_OVERRIDE = 2_000_000
# ============================================================

BASE_URL = "https://api.beehiiv.com/v2"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def api_get(endpoint, params=None):
    """Faz GET na API do Beehiiv com paginação automática."""
    url = f"{BASE_URL}{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        if query:
            url += f"?{query}"

    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ERRO API [{e.code}]: {body[:300]}")
        return None
    except Exception as e:
        print(f"  ERRO: {e}")
        return None


def fetch_all_pages(endpoint, params=None, label="items"):
    """Busca todas as páginas de um endpoint paginado (offset + cursor)."""
    all_data = []
    page = 1
    cursor = None
    use_cursor = False
    if params is None:
        params = {}

    while True:
        # Usa cursor-based pagination quando disponível ou após página 100
        if use_cursor and cursor:
            params.pop("page", None)
            params["cursor"] = cursor
            print(f"  Buscando (cursor)...", end=" ", flush=True)
        else:
            params.pop("cursor", None)
            params["page"] = str(page)
            print(f"  Buscando página {page}...", end=" ", flush=True)

        result = api_get(endpoint, params)

        if not result or "data" not in result:
            print("sem dados")
            break

        batch = result["data"]
        if not batch:
            print("vazio")
            break

        all_data.extend(batch)
        print(f"{len(batch)} {label}")

        limit = int(params.get("limit", "50"))

        # Se menos que o limite, acabou
        if len(batch) < limit:
            break

        # Tenta pegar cursor para próxima página
        next_cursor = result.get("next_cursor") or result.get("cursor")
        if next_cursor:
            cursor = next_cursor
            use_cursor = True
        elif page >= 99:
            # Muda para cursor-based antes de bater o limite de 100
            # Usa o último item como referência
            use_cursor = True
            if not cursor:
                # Sem cursor disponível, para aqui
                print(f"  ⚠️  Limite de paginação atingido em {len(all_data)} {label}")
                break
        else:
            page += 1

        if use_cursor and not cursor:
            break

    return all_data


# ============================================================
# 1. BUSCAR DADOS
# ============================================================
def fetch_posts():
    """Busca todos os posts com stats expandidas."""
    print("\n📬 Buscando posts...")
    posts = fetch_all_pages(
        f"/publications/{PUB_ID}/posts",
        params={
            "expand[]": "stats",
            "limit": "50",
            "status": "confirmed",
            "order_by": "publish_date",
            "direction": "asc",
        },
        label="posts",
    )
    print(f"  Total: {len(posts)} posts encontrados")
    return posts


def fetch_subscribers():
    """Busca subscribers de forma inteligente (sem baixar milhões).

    Estratégia:
    - Pega a primeira página para saber o total
    - Busca as últimas 2000 (mais recentes) para calcular crescimento
    - Busca uma amostra das primeiras páginas para ter histórico antigo
    """
    print("\n👥 Buscando subscribers (modo otimizado para bases grandes)...")

    # 1. Primeira chamada para pegar total e estrutura
    first_page = api_get(
        f"/publications/{PUB_ID}/subscriptions",
        params={"limit": "100", "order_by": "created", "direction": "desc"},
    )

    if not first_page or "data" not in first_page:
        print("  Sem dados de subscribers")
        return {"raw": [], "total_from_api": 0}

    # Debug: mostra campos do primeiro subscriber
    if first_page["data"]:
        sample = first_page["data"][0]
        print(f"  🔍 Campos do subscriber: {list(sample.keys())}")
        for k in ["created_at", "created", "subscribed_at", "joined_at", "status"]:
            if k in sample:
                print(f"     {k} = {repr(sample[k])[:80]}")

    total_results = first_page.get("total_results", 0)
    # Se total_results não estiver disponível, tenta pelo page info
    if not total_results:
        page_info = first_page.get("page", {})
        if isinstance(page_info, dict):
            total_pages = page_info.get("total_pages", 0)
            total_results = total_pages * 100

    # Usa o override manual se a API não retornar o total
    if not total_results and TOTAL_SUBSCRIBERS_OVERRIDE:
        total_results = TOTAL_SUBSCRIBERS_OVERRIDE
        print(f"  Total (override manual): ~{total_results:,} subscribers")
    else:
        print(f"  Total na base: {total_results:,} subscribers")

    # 2. Busca os mais recentes (últimas 20 páginas = 2000 subs)
    recent_subs = list(first_page["data"])
    MAX_RECENT_PAGES = 20
    print(f"  Buscando os {MAX_RECENT_PAGES * 100} mais recentes...")
    for page in range(2, MAX_RECENT_PAGES + 1):
        result = api_get(
            f"/publications/{PUB_ID}/subscriptions",
            params={"limit": "100", "page": str(page), "order_by": "created", "direction": "desc"},
        )
        if not result or not result.get("data"):
            break
        batch = result["data"]
        recent_subs.extend(batch)
        if len(batch) < 100:
            break

    print(f"  Recentes coletados: {len(recent_subs)}")

    # 3. Busca os mais antigos (primeiras 10 páginas) para ter início do histórico
    print(f"  Buscando os mais antigos para histórico...")
    old_subs = []
    for page in range(1, 11):
        result = api_get(
            f"/publications/{PUB_ID}/subscriptions",
            params={"limit": "100", "page": str(page), "order_by": "created", "direction": "asc"},
        )
        if not result or not result.get("data"):
            break
        batch = result["data"]
        old_subs.extend(batch)
        if len(batch) < 100:
            break

    print(f"  Antigos coletados: {len(old_subs)}")

    # Combina e deduplica
    all_subs = recent_subs + old_subs
    seen_ids = set()
    unique_subs = []
    for s in all_subs:
        sid = s.get("id", s.get("email", str(len(unique_subs))))
        if sid not in seen_ids:
            seen_ids.add(sid)
            unique_subs.append(s)

    print(f"  Amostra total (deduplicada): {len(unique_subs)}")

    return {"raw": unique_subs, "total_from_api": total_results}


# ============================================================
# 2. PROCESSAR DADOS
# ============================================================
def process_posts(raw_posts):
    """Processa posts crus da API em formato limpo."""
    posts = []
    for p in raw_posts:
        stats = p.get("stats", {}) or {}
        email_stats = stats.get("email", {}) or {}
        web_stats = stats.get("web", {}) or {}

        # Tenta vários formatos de data
        publish_date = p.get("publish_date") or p.get("displayed_date") or p.get("created_at")
        if isinstance(publish_date, (int, float)):
            # Unix timestamp
            dt = datetime.fromtimestamp(publish_date, tz=timezone.utc)
        elif isinstance(publish_date, str):
            try:
                dt = datetime.fromisoformat(publish_date.replace("Z", "+00:00"))
            except:
                dt = None
        else:
            dt = None

        # Helper para extrair valor de campo que pode ser dict, list ou int
        def safe_get(obj, key, default=0):
            """Extrai valor seguro de um campo que pode ter formato variado."""
            val = obj.get(key, default) if isinstance(obj, dict) else default
            if isinstance(val, dict):
                return val
            if isinstance(val, list):
                return {}  # lista não tem .get, retorna dict vazio
            return val

        # Extrai métricas com fallbacks robustos
        recipients = (
            safe_get(email_stats, "recipients", 0)
            or safe_get(stats, "email_recipients", 0)
            or safe_get(stats, "recipients", 0)
            or 0
        )
        delivered = (
            safe_get(email_stats, "delivered", 0)
            or safe_get(stats, "email_delivered", 0)
            or recipients
        )

        opens_field = safe_get(stats, "opens", {})
        clicks_field = safe_get(stats, "clicks", {})

        unique_opens = (
            safe_get(email_stats, "unique_opens", 0)
            or safe_get(stats, "unique_opens", 0)
            or (opens_field.get("unique", 0) if isinstance(opens_field, dict) else 0)
            or 0
        )
        total_opens = (
            safe_get(email_stats, "total_opens", 0)
            or safe_get(stats, "total_opens", 0)
            or (opens_field.get("total", 0) if isinstance(opens_field, dict) else 0)
            or 0
        )
        unique_clicks = (
            safe_get(email_stats, "unique_clicks", 0)
            or safe_get(stats, "unique_clicks", 0)
            or (clicks_field.get("unique", 0) if isinstance(clicks_field, dict) else 0)
            or 0
        )
        total_clicks = (
            safe_get(email_stats, "total_clicks", 0)
            or safe_get(stats, "total_clicks", 0)
            or (clicks_field.get("total", 0) if isinstance(clicks_field, dict) else 0)
            or 0
        )
        unsubscribes = (
            safe_get(email_stats, "unsubscribes", 0)
            or safe_get(stats, "unsubscribes", 0)
            or 0
        )
        spam_reports = (
            safe_get(email_stats, "spam_reports", 0)
            or safe_get(stats, "spam_reports", 0)
            or 0
        )

        # Web stats (campos reais da API: "views" e "clicks")
        web_views = safe_get(web_stats, "views", 0) or safe_get(web_stats, "unique_page_views", 0) or 0
        web_clicks = safe_get(web_stats, "clicks", 0) or safe_get(web_stats, "unique_clicks", 0) or 0

        # Clicks detalhados por URL (stats.clicks é uma lista de links)
        click_details = stats.get("clicks", [])
        top_links = []
        if isinstance(click_details, list):
            for link in click_details[:10]:
                if isinstance(link, dict):
                    top_links.append({
                        "url": link.get("base_url") or link.get("url", ""),
                        "total_clicks": link.get("total_clicks", 0),
                        "unique_clicks": link.get("total_unique_clicks", 0),
                    })

        # Força valores numéricos
        def to_int(v):
            try: return int(v) if v else 0
            except (ValueError, TypeError): return 0

        recipients = to_int(recipients)
        delivered = to_int(delivered)
        unique_opens = to_int(unique_opens)
        total_opens = to_int(total_opens)
        unique_clicks = to_int(unique_clicks)
        total_clicks = to_int(total_clicks)
        unsubscribes = to_int(unsubscribes)
        spam_reports = to_int(spam_reports)
        web_views = to_int(web_views)
        web_clicks = to_int(web_clicks)

        # Calcula rates
        open_rate = (unique_opens / delivered * 100) if delivered > 0 else 0
        click_rate = (unique_clicks / delivered * 100) if delivered > 0 else 0
        cto_rate = (unique_clicks / unique_opens * 100) if unique_opens > 0 else 0
        unsub_rate = (unsubscribes / delivered * 100) if delivered > 0 else 0

        posts.append({
            "id": p.get("id", ""),
            "title": p.get("title", "Sem título") or p.get("subtitle", "Sem título"),
            "date": dt.isoformat() if dt else None,
            "date_label": dt.strftime("%d/%m/%Y") if dt else "N/A",
            "day_of_week": dt.weekday() if dt else None,  # 0=Monday
            "recipients": recipients,
            "delivered": delivered,
            "unique_opens": unique_opens,
            "total_opens": total_opens,
            "unique_clicks": unique_clicks,
            "total_clicks": total_clicks,
            "open_rate": round(open_rate, 1),
            "click_rate": round(click_rate, 1),
            "cto_rate": round(cto_rate, 1),
            "unsubscribes": unsubscribes,
            "unsub_rate": round(unsub_rate, 2),
            "spam_reports": spam_reports,
            "web_views": web_views,
            "web_clicks": web_clicks,
            "top_links": top_links,
            "raw_stats": stats,  # preserva stats originais
        })

    # Filtra posts sem data
    posts = [p for p in posts if p["date"]]
    posts.sort(key=lambda x: x["date"])
    return posts


def process_subscribers(sub_data, posts=None):
    """Processa subscribers em formato limpo.

    Usa amostra parcial + total da API + dados de delivered dos posts.
    """
    raw_subs = sub_data.get("raw", [])
    total_from_api = sub_data.get("total_from_api", 0)

    by_month = defaultdict(lambda: {"new": 0, "active": 0, "inactive": 0})
    active_in_sample = 0
    parsed_dates = 0

    for s in raw_subs:
        status = (s.get("status") or "").lower()

        # Tenta múltiplos campos de data
        created = None
        for field in ["created_at", "created", "subscribed_at", "joined_at", "utm_created_at"]:
            if s.get(field):
                created = s[field]
                break

        dt = None
        if isinstance(created, (int, float)):
            # Unix timestamp (pode ser em segundos ou milissegundos)
            ts = created / 1000 if created > 1e12 else created
            try:
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            except:
                pass
        elif isinstance(created, str):
            # Tenta ISO format
            for fmt_str in ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(created.replace("Z", "+00:00").replace("+00:00", "+0000"), fmt_str)
                    break
                except:
                    pass
            if not dt:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except:
                    pass

        if dt:
            parsed_dates += 1
            month_key = dt.strftime("%Y-%m")
            by_month[month_key]["new"] += 1

        if status == "active":
            active_in_sample += 1

    print(f"  Datas parseadas: {parsed_dates}/{len(raw_subs)}")

    # Estima taxa de ativos com base na amostra
    sample_size = len(raw_subs)
    active_rate = (active_in_sample / sample_size) if sample_size > 0 else 0.85
    total = total_from_api if total_from_api > sample_size else sample_size
    estimated_active = int(total * active_rate)

    # Gera série temporal da amostra
    sorted_months = sorted(by_month.keys())
    cumulative = 0
    timeline_from_subs = []
    for m in sorted_months:
        cumulative += by_month[m]["new"]
        timeline_from_subs.append({
            "month": m,
            "new": by_month[m]["new"],
            "cumulative": cumulative,
        })

    # ALTERNATIVA: usa "delivered" dos posts como proxy de subscriber count ao longo do tempo
    # Isso é muito mais preciso que a amostra para bases grandes
    timeline_from_posts = []
    if posts:
        post_by_month = defaultdict(lambda: {"delivered": 0, "count": 0})
        for p in posts:
            if p.get("delivered", 0) > 0 and p.get("date"):
                month_key = p["date"][:7]
                post_by_month[month_key]["delivered"] = max(post_by_month[month_key]["delivered"], p["delivered"])
                post_by_month[month_key]["count"] += 1

        for m in sorted(post_by_month.keys()):
            timeline_from_posts.append({
                "month": m,
                "subscribers_estimate": post_by_month[m]["delivered"],
                "editions": post_by_month[m]["count"],
            })

    # Usa a timeline dos posts se disponível (mais precisa)
    use_posts_timeline = len(timeline_from_posts) > len(timeline_from_subs)

    return {
        "total": total,
        "active": estimated_active,
        "inactive": total - estimated_active,
        "active_rate_sample": round(active_rate * 100, 1),
        "sample_size": sample_size,
        "is_sampled": total > sample_size,
        "timeline_subs": timeline_from_subs,
        "timeline_posts": timeline_from_posts,
        "use_posts_timeline": use_posts_timeline,
    }


# ============================================================
# 3. GERAR DASHBOARD HTML
# ============================================================
def generate_dashboard(posts, subscribers, raw_stats_sample):
    """Gera o dashboard HTML completo."""

    # Filtra posts: separa web-only (delivered=0) de email posts
    email_posts = [p for p in posts if p.get("delivered", 0) > 0]
    web_only_posts = [p for p in posts if p.get("delivered", 0) == 0]

    print(f"  Posts com email data: {len(email_posts)}")
    print(f"  Posts web-only (excluídos da análise de email): {len(web_only_posts)}")

    posts_json = json.dumps(email_posts, ensure_ascii=False, default=str)
    all_posts_json = json.dumps(posts, ensure_ascii=False, default=str)
    subs_json = json.dumps(subscribers, ensure_ascii=False, default=str)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter Analytics — Beehiiv</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0"></script>
    <style>
        :root {{
            --bg: #f5f5f7; --card: #ffffff; --header-bg: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            --text: #1d1d1f; --text2: #6e6e73; --text-light: #ffffff;
            --orange: #FF6719; --blue: #4C72B0; --green: #34c759; --red: #ff3b30;
            --teal: #55A868; --purple: #8172B3; --brown: #937860;
            --gap: 16px; --radius: 12px;
        }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',Roboto,sans-serif; background:var(--bg); color:var(--text); line-height:1.5; }}
        .container {{ max-width:1440px; margin:0 auto; padding:var(--gap); }}

        /* Header */
        .header {{ background:var(--header-bg); color:var(--text-light); padding:24px 28px; border-radius:var(--radius); margin-bottom:var(--gap); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px; }}
        .header h1 {{ font-size:22px; font-weight:700; letter-spacing:-0.3px; }}
        .header p {{ font-size:13px; color:rgba(255,255,255,0.6); margin-top:2px; }}
        .filters {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; }}
        .filters label {{ font-size:12px; color:rgba(255,255,255,0.6); text-transform:uppercase; letter-spacing:0.5px; }}
        .filters select {{ padding:7px 12px; border:1px solid rgba(255,255,255,0.15); border-radius:6px; background:rgba(255,255,255,0.08); color:#fff; font-size:13px; cursor:pointer; }}
        .filters select option {{ background:#1a1a2e; color:#fff; }}

        /* KPI Cards */
        .kpi-row {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(170px,1fr)); gap:var(--gap); margin-bottom:var(--gap); }}
        .kpi {{ background:var(--card); border-radius:var(--radius); padding:18px 22px; box-shadow:0 1px 3px rgba(0,0,0,0.06); transition:transform 0.15s; }}
        .kpi:hover {{ transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,0.1); }}
        .kpi-label {{ font-size:11px; color:var(--text2); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px; }}
        .kpi-val {{ font-size:26px; font-weight:700; }}
        .kpi-delta {{ font-size:12px; font-weight:500; margin-top:4px; }}
        .kpi-delta.up {{ color:var(--green); }} .kpi-delta.down {{ color:var(--red); }}
        .kpi-desc {{ font-size:11px; color:var(--text2); margin-top:6px; line-height:1.4; }}
        .kpi-bench {{ font-size:10px; color:var(--purple); margin-top:3px; font-style:italic; }}

        /* Insights */
        .insights-box {{ background:var(--card); border-radius:var(--radius); padding:24px 28px; box-shadow:0 1px 3px rgba(0,0,0,0.06); margin-bottom:var(--gap); border-left:4px solid var(--orange); }}
        .insights-box h3 {{ font-size:16px; font-weight:700; margin-bottom:16px; }}
        .insight {{ padding:10px 0; border-bottom:1px solid #f2f2f7; font-size:13px; line-height:1.6; }}
        .insight:last-child {{ border-bottom:none; }}
        .insight-icon {{ margin-right:8px; }}
        .insight-good {{ color:var(--green); }} .insight-warn {{ color:var(--orange); }} .insight-bad {{ color:var(--red); }} .insight-info {{ color:var(--blue); }}
        .sampled-note {{ background:#fff8f0; border:1px solid #ffe0b2; border-radius:8px; padding:12px 16px; font-size:12px; color:#e65100; margin-bottom:var(--gap); }}

        /* Charts */
        .chart-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(420px,1fr)); gap:var(--gap); margin-bottom:var(--gap); }}
        .chart-grid.full {{ grid-template-columns:1fr; }}
        .chart-box {{ background:var(--card); border-radius:var(--radius); padding:20px 24px; box-shadow:0 1px 3px rgba(0,0,0,0.06); }}
        .chart-box h3 {{ font-size:14px; font-weight:600; margin-bottom:16px; }}
        .chart-box canvas {{ max-height:320px; }}

        /* Table */
        .table-box {{ background:var(--card); border-radius:var(--radius); padding:20px 24px; box-shadow:0 1px 3px rgba(0,0,0,0.06); overflow-x:auto; margin-bottom:var(--gap); }}
        .table-box h3 {{ font-size:14px; font-weight:600; margin-bottom:16px; }}
        table {{ width:100%; border-collapse:collapse; font-size:13px; }}
        thead th {{ text-align:left; padding:10px 12px; border-bottom:2px solid #e5e5ea; color:var(--text2); font-size:11px; text-transform:uppercase; letter-spacing:0.5px; cursor:pointer; user-select:none; white-space:nowrap; }}
        thead th:hover {{ color:var(--text); background:#f8f8fa; }}
        tbody td {{ padding:10px 12px; border-bottom:1px solid #f2f2f7; }}
        tbody tr:hover {{ background:#f8f8fa; }}
        .bar {{ display:inline-block; height:6px; border-radius:3px; margin-right:6px; vertical-align:middle; }}

        /* Tabs */
        .tab-row {{ display:flex; gap:8px; margin-bottom:16px; }}
        .tab {{ padding:8px 16px; border-radius:8px; font-size:13px; font-weight:500; cursor:pointer; border:1px solid #e5e5ea; background:#fff; color:var(--text2); transition:all 0.15s; }}
        .tab.active {{ background:var(--orange); color:#fff; border-color:var(--orange); }}
        .tab:hover:not(.active) {{ border-color:var(--orange); color:var(--orange); }}

        /* Debug/Raw */
        .raw-section {{ background:var(--card); border-radius:var(--radius); padding:20px 24px; box-shadow:0 1px 3px rgba(0,0,0,0.06); margin-bottom:var(--gap); }}
        .raw-section summary {{ cursor:pointer; font-weight:600; font-size:14px; }}
        .raw-section pre {{ margin-top:12px; background:#f5f5f7; padding:16px; border-radius:8px; overflow-x:auto; font-size:12px; max-height:400px; overflow-y:auto; }}

        /* Footer */
        footer {{ text-align:center; padding:16px; font-size:12px; color:var(--text2); }}

        @media (max-width:768px) {{
            .header {{ flex-direction:column; align-items:flex-start; }}
            .kpi-row {{ grid-template-columns:repeat(2,1fr); }}
            .chart-grid {{ grid-template-columns:1fr; }}
        }}
        @media print {{
            body {{ background:#fff; }} .filters {{ display:none; }}
            .chart-box,.kpi {{ box-shadow:none; border:1px solid #e5e5ea; break-inside:avoid; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <header class="header">
        <div>
            <h1>Newsletter Analytics</h1>
            <p>Dados atualizados em {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        </div>
        <div class="filters">
            <div><label>Período</label>
                <select id="f-period" onchange="applyFilters()">
                    <option value="all">Todo o período</option>
                    <option value="30">Últimos 30 dias</option>
                    <option value="90">Últimos 90 dias</option>
                    <option value="180">Últimos 6 meses</option>
                    <option value="365">Último ano</option>
                </select>
            </div>
        </div>
    </header>

    <!-- KPI Row -->
    <section class="kpi-row" id="kpis"></section>

    <!-- Subscriber Growth -->
    <section class="chart-grid full"><div class="chart-box"><h3>Crescimento de Subscribers</h3><canvas id="c-growth"></canvas></div></section>

    <!-- Engagement Row -->
    <section class="chart-grid">
        <div class="chart-box"><h3>Open Rate por Edição</h3><canvas id="c-open"></canvas></div>
        <div class="chart-box"><h3>Click Rate por Edição</h3><canvas id="c-click"></canvas></div>
    </section>

    <!-- CTO + Unsub Row -->
    <section class="chart-grid">
        <div class="chart-box"><h3>Click-to-Open Rate (CTOR)</h3><canvas id="c-ctor"></canvas></div>
        <div class="chart-box"><h3>Unsubscribe Rate por Edição</h3><canvas id="c-unsub"></canvas></div>
    </section>

    <!-- Distribution Row -->
    <section class="chart-grid">
        <div class="chart-box"><h3>Distribuição de Open Rate</h3><canvas id="c-open-dist"></canvas></div>
        <div class="chart-box"><h3>Melhor Dia da Semana (Open Rate)</h3><canvas id="c-weekday"></canvas></div>
    </section>

    <!-- Funnel -->
    <section class="chart-grid full"><div class="chart-box"><h3>Funil: Enviados → Abertos → Clicados</h3><canvas id="c-funnel"></canvas></div></section>

    <!-- Web vs Email -->
    <section class="chart-grid full"><div class="chart-box"><h3>Email vs Web: Visualizações e Cliques</h3><canvas id="c-web"></canvas></div></section>

    <!-- Top Links -->
    <section class="chart-grid full"><div class="chart-box"><h3>Top Links Mais Clicados (todas as edições)</h3><canvas id="c-toplinks"></canvas></div></section>

    <!-- Insights -->
    <section class="insights-box" id="insights-section">
        <h3>Insights e Recomendações</h3>
        <div id="insights-list"></div>
    </section>

    <!-- Table -->
    <section class="table-box">
        <h3>Detalhamento por Edição <span style="font-weight:400;font-size:12px;color:var(--text2)">(clique no cabeçalho para ordenar)</span></h3>
        <div id="tbl"></div>
    </section>

    <!-- Raw Stats Debug -->
    <section class="raw-section">
        <details>
            <summary>Ver campos brutos da API (debug)</summary>
            <pre id="raw-stats"></pre>
        </details>
    </section>

    <footer>Newsletter Analytics Dashboard — Dados via Beehiiv API v2</footer>
</div>

<script>
const COLORS = ['#FF6719','#4C72B0','#55A868','#C44E52','#8172B3','#937860','#e6894a','#3d9970'];
const DAYS = ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'];

const POSTS_RAW = {posts_json};
const ALL_POSTS = {all_posts_json};
const SUBS = {subs_json};

let filteredPosts = [...POSTS_RAW];
let charts = {{}};

function fmt(v, t) {{
    if (v == null || isNaN(v)) return '-';
    if (t === '%') return v.toFixed(1) + '%';
    if (t === 'n') {{
        if (Math.abs(v)>=1e6) return (v/1e6).toFixed(1)+'M';
        if (Math.abs(v)>=1e3) return (v/1e3).toFixed(1)+'K';
        return v.toLocaleString('pt-BR');
    }}
    return v.toString();
}}

function applyFilters() {{
    const period = document.getElementById('f-period').value;
    if (period === 'all') {{
        filteredPosts = [...POSTS_RAW];
    }} else {{
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - parseInt(period));
        filteredPosts = POSTS_RAW.filter(p => new Date(p.date) >= cutoff);
    }}
    renderAll();
}}

function renderAll() {{
    renderKPIs();
    renderCharts();
    renderInsights();
    renderTable();
}}

// ── Insights ──
function renderInsights() {{
    const p = filteredPosts;
    if (!p.length) return;
    const insights = [];

    const avgOpen = p.reduce((a,x)=>a+x.open_rate,0)/p.length;
    const avgClick = p.reduce((a,x)=>a+x.click_rate,0)/p.length;
    const avgCTO = p.reduce((a,x)=>a+x.cto_rate,0)/p.length;
    const avgUnsub = p.reduce((a,x)=>a+x.unsub_rate,0)/p.length;

    // Open Rate analysis
    if (avgOpen >= 35) {{
        insights.push({{icon:'✅', cls:'insight-good', text:`Open Rate médio de ${{avgOpen.toFixed(1)}}% está muito acima da média do mercado (15-25%). Sua base é altamente engajada — isso sugere que seus subject lines são eficazes e sua lista é bem qualificada.`}});
    }} else if (avgOpen >= 20) {{
        insights.push({{icon:'✅', cls:'insight-good', text:`Open Rate de ${{avgOpen.toFixed(1)}}% está dentro da média do mercado (15-25%). Há espaço para melhorar com testes A/B de subject lines.`}});
    }} else {{
        insights.push({{icon:'⚠️', cls:'insight-warn', text:`Open Rate de ${{avgOpen.toFixed(1)}}% está abaixo da média (15-25%). Considere limpar subscribers inativos e testar horários de envio diferentes.`}});
    }}

    // Click Rate analysis
    if (avgClick >= 3) {{
        insights.push({{icon:'✅', cls:'insight-good', text:`Click Rate de ${{avgClick.toFixed(1)}}% está acima do benchmark (1-3%). Seus CTAs e links estão performando bem.`}});
    }} else if (avgClick >= 1) {{
        insights.push({{icon:'💡', cls:'insight-info', text:`Click Rate de ${{avgClick.toFixed(1)}}% está na média (1-3%). Para melhorar: posicione CTAs mais acima no email, use botões em vez de links de texto, e reduza o número de links por edição.`}});
    }} else {{
        insights.push({{icon:'⚠️', cls:'insight-warn', text:`Click Rate de ${{avgClick.toFixed(2)}}% está abaixo do benchmark (1-3%). Reveja o posicionamento dos seus links e a clareza dos seus CTAs. Considere também se o conteúdo está alinhado com as expectativas da audiência.`}});
    }}

    // CTOR analysis
    if (avgCTO < 2) {{
        insights.push({{icon:'⚠️', cls:'insight-warn', text:`CTOR (Click-to-Open) de apenas ${{avgCTO.toFixed(1)}}%: quem abre raramente clica. O conteúdo pode não estar entregando o que o subject line promete. Tente incluir links mais relevantes e chamadas à ação mais claras.`}});
    }}

    // Unsub analysis
    if (avgUnsub > 1) {{
        insights.push({{icon:'🚨', cls:'insight-bad', text:`Unsub Rate médio de ${{avgUnsub.toFixed(2)}}% está alto (ideal é abaixo de 0.5%). Investigue quais edições causam mais unsubscribes — pode indicar conteúdo desalinhado ou frequência excessiva.`}});
    }} else if (avgUnsub < 0.2) {{
        insights.push({{icon:'✅', cls:'insight-good', text:`Unsub Rate de ${{avgUnsub.toFixed(2)}}% é excelente — sua audiência está satisfeita com o conteúdo e a frequência.`}});
    }}

    // Best / worst performing post
    const sorted = [...p].sort((a,b) => b.open_rate - a.open_rate);
    const best = sorted[0];
    const worst = sorted[sorted.length-1];
    if (best && worst && sorted.length > 3) {{
        insights.push({{icon:'🏆', cls:'insight-good', text:`Melhor edição: "${{best.title}}" (${{best.date_label}}) com ${{best.open_rate}}% de abertura e ${{best.click_rate}}% de cliques. Analise o que funcionou nesse subject line e conteúdo.`}});
        if (worst.open_rate < avgOpen * 0.7) {{
            insights.push({{icon:'📉', cls:'insight-warn', text:`Pior edição: "${{worst.title}}" (${{worst.date_label}}) com apenas ${{worst.open_rate}}% de abertura. O subject line pode não ter ressoado com a audiência.`}});
        }}
    }}

    // Day of week insight
    const dayData = Array.from({{length:7}},()=>({{sum:0,count:0}}));
    p.forEach(x => {{ if (x.day_of_week!=null) {{ dayData[x.day_of_week].sum+=x.open_rate; dayData[x.day_of_week].count++; }} }});
    const dayAvg = dayData.map(d => d.count>0 ? d.sum/d.count : 0);
    const bestDayIdx = dayAvg.indexOf(Math.max(...dayAvg));
    const bestDayCount = dayData[bestDayIdx].count;
    if (bestDayCount >= 2) {{
        insights.push({{icon:'📅', cls:'insight-info', text:`Melhor dia para envio: ${{DAYS[bestDayIdx]}} com ${{dayAvg[bestDayIdx].toFixed(1)}}% de open rate médio (baseado em ${{bestDayCount}} edições). Considere concentrar envios nesse dia.`}});
    }}

    // Growth trend
    const tl = SUBS.timeline_posts || [];
    if (tl.length >= 3) {{
        const recent = tl.slice(-3);
        const growing = recent[recent.length-1].subscribers_estimate > recent[0].subscribers_estimate;
        if (growing) {{
            insights.push({{icon:'📈', cls:'insight-good', text:`Base de subscribers crescendo nos últimos ${{recent.length}} meses — de ${{fmt(recent[0].subscribers_estimate,'n')}} para ${{fmt(recent[recent.length-1].subscribers_estimate,'n')}}.`}});
        }} else {{
            insights.push({{icon:'📉', cls:'insight-warn', text:`Base de subscribers encolhendo nos últimos meses — de ${{fmt(recent[0].subscribers_estimate,'n')}} para ${{fmt(recent[recent.length-1].subscribers_estimate,'n')}}. Revise estratégias de aquisição e retenção.`}});
        }}
    }}

    // Web views
    const totalWebViews = p.reduce((a,x)=>a+x.web_views,0);
    if (totalWebViews > 0) {{
        insights.push({{icon:'🌐', cls:'insight-info', text:`${{fmt(totalWebViews,'n')}} visualizações web no total. Posts publicados na web ampliam o alcance além da base de email.`}});
    }}

    document.getElementById('insights-list').innerHTML = insights.map(i =>
        `<div class="insight"><span class="insight-icon">${{i.icon}}</span><span class="${{i.cls}}">${{i.text}}</span></div>`
    ).join('');
}}

// ── KPIs ──
function renderKPIs() {{
    const p = filteredPosts;
    const s = SUBS;
    const kpis = [];

    // Usa o maior "delivered" como proxy de total real de subscribers
    const maxDelivered = p.length > 0 ? Math.max(...p.map(x=>x.delivered)) : 0;
    const latestDelivered = p.length > 0 ? p[p.length-1].delivered : 0;
    const subTotal = latestDelivered || s.total || 0;

    if (subTotal > 0) {{
        kpis.push({{
            label:'Total Subscribers (último envio)', val:fmt(subTotal,'n'),
            delta: maxDelivered !== latestDelivered ? 'Pico: '+fmt(maxDelivered,'n') : '',
            cls:'up',
            desc:'Número de emails entregues no envio mais recente. Representa sua base ativa real.',
            bench:'Benchmark: newsletters acima de 100K são consideradas de grande porte.'
        }});
    }}

    if (p.length > 0) {{
        const avgOpen = p.reduce((a,x)=>a+x.open_rate,0)/p.length;
        const avgClick = p.reduce((a,x)=>a+x.click_rate,0)/p.length;
        const avgCTO = p.reduce((a,x)=>a+x.cto_rate,0)/p.length;
        const avgUnsub = p.reduce((a,x)=>a+x.unsub_rate,0)/p.length;
        const totalSent = p.reduce((a,x)=>a+x.delivered,0);

        const mid = Math.floor(p.length/2);
        const h1 = p.slice(0,mid), h2 = p.slice(mid);
        const openDelta = mid>0 ? (h2.reduce((a,x)=>a+x.open_rate,0)/h2.length) - (h1.reduce((a,x)=>a+x.open_rate,0)/h1.length) : 0;
        const clickDelta = mid>0 ? (h2.reduce((a,x)=>a+x.click_rate,0)/h2.length) - (h1.reduce((a,x)=>a+x.click_rate,0)/h1.length) : 0;

        kpis.push({{
            label:'Avg Open Rate', val:fmt(avgOpen,'%'),
            delta:(openDelta>=0?'+':'')+openDelta.toFixed(1)+'pp tendência', cls:openDelta>=0?'up':'down',
            desc:'Percentual de destinatários que abriram o email. É a principal métrica de engajamento.',
            bench:'Benchmark: 15-25% é a média do mercado. Acima de 30% é excelente.'
        }});
        kpis.push({{
            label:'Avg Click Rate', val:fmt(avgClick,'%'),
            delta:(clickDelta>=0?'+':'')+clickDelta.toFixed(1)+'pp tendência', cls:clickDelta>=0?'up':'down',
            desc:'Percentual de destinatários que clicaram em pelo menos um link.',
            bench:'Benchmark: 1-3% é a média. Acima de 3% é muito bom.'
        }});
        kpis.push({{
            label:'Avg CTOR', val:fmt(avgCTO,'%'), delta:'click-to-open rate', cls:avgCTO>10?'up':'down',
            desc:'Click-to-Open Rate: dos que abriram, quantos clicaram. Mede a qualidade do conteúdo.',
            bench:'Benchmark: 8-15% é bom. Acima de 15% é excelente.'
        }});
        kpis.push({{
            label:'Edições Analisadas', val:fmt(p.length,'n'),
            delta:fmt(totalSent,'n')+' emails enviados', cls:'up',
            desc:'Total de edições com dados de email no período selecionado.',
            bench:''
        }});
        kpis.push({{
            label:'Avg Unsub Rate', val:fmt(avgUnsub,'%'), delta:'por edição', cls:avgUnsub<0.5?'up':'down',
            desc:'Percentual que cancela inscrição após cada envio. Monitore picos.',
            bench:'Benchmark: abaixo de 0.5% é saudável. Acima de 1% é sinal de alerta.'
        }});

        // Growth from posts timeline
        const tl = s.timeline_posts || [];
        if (tl.length >= 2) {{
            const last = tl[tl.length-1];
            const prev = tl[tl.length-2];
            const growth = last.subscribers_estimate - prev.subscribers_estimate;
            const growthPct = prev.subscribers_estimate > 0 ? (growth/prev.subscribers_estimate*100) : 0;
            kpis.push({{
                label:'Crescimento Mensal', val:(growth>=0?'+':'')+fmt(growth,'n'),
                delta:(growthPct>=0?'+':'')+growthPct.toFixed(2)+'% vs mês anterior', cls:growth>=0?'up':'down',
                desc:'Variação do nº de destinatários entre os meses mais recentes.',
                bench:'Benchmark: 2-5% de crescimento mensal é saudável.'
            }});
        }}
    }}

    document.getElementById('kpis').innerHTML = kpis.map(k => `
        <div class="kpi">
            <div class="kpi-label">${{k.label}}</div>
            <div class="kpi-val">${{k.val}}</div>
            <div class="kpi-delta ${{k.cls}}">${{k.delta}}</div>
            <div class="kpi-desc">${{k.desc}}</div>
            ${{k.bench ? '<div class="kpi-bench">'+k.bench+'</div>' : ''}}
        </div>`).join('');
}}

// ── Charts ──
function destroyCharts() {{ Object.values(charts).forEach(c => c.destroy()); charts = {{}}; }}

function renderCharts() {{
    destroyCharts();
    const p = filteredPosts;
    const s = SUBS;
    const dates = p.map(x => x.date_label);
    const titles = p.map(x => x.title.length > 30 ? x.title.slice(0,30)+'…' : x.title);

    // 1. Subscriber Growth (usa delivered dos posts como proxy)
    const tl = s.timeline_posts || [];
    if (tl.length > 0) {{
        charts.growth = new Chart(document.getElementById('c-growth'), {{
            data: {{
                labels: tl.map(d=>d.month),
                datasets: [
                    {{ type:'line', label:'Subscribers (por max delivered)', data:tl.map(d=>d.subscribers_estimate), borderColor:COLORS[0], backgroundColor:COLORS[0]+'15', fill:true, tension:0.3, borderWidth:2.5, pointRadius:4, yAxisID:'y' }},
                    {{ type:'bar', label:'Edições/mês', data:tl.map(d=>d.editions), backgroundColor:COLORS[1]+'AA', borderColor:COLORS[1], borderWidth:1, borderRadius:4, yAxisID:'y1' }}
                ]
            }},
            options: {{ responsive:true, maintainAspectRatio:false, interaction:{{mode:'index',intersect:false}},
                plugins:{{legend:{{position:'top',labels:{{usePointStyle:true,padding:20}}}}}},
                scales:{{ y:{{position:'left',beginAtZero:false,title:{{display:true,text:'Subscribers'}},grid:{{color:'#f0f0f0'}},ticks:{{callback:(v)=>fmt(v,'n')}}}}, y1:{{position:'right',beginAtZero:true,title:{{display:true,text:'Edições'}},grid:{{display:false}}}}, x:{{grid:{{display:false}}}} }}
            }}
        }});
    }} else if (s.timeline_subs && s.timeline_subs.length > 0) {{
        const ts = s.timeline_subs;
        charts.growth = new Chart(document.getElementById('c-growth'), {{
            data: {{
                labels: ts.map(d=>d.month),
                datasets: [
                    {{ type:'line', label:'Acumulado (amostra)', data:ts.map(d=>d.cumulative), borderColor:COLORS[0], backgroundColor:COLORS[0]+'15', fill:true, tension:0.3, borderWidth:2.5, pointRadius:4 }}
                ]
            }},
            options: {{ responsive:true, maintainAspectRatio:false,
                plugins:{{legend:{{position:'top',labels:{{usePointStyle:true}}}}}},
                scales:{{ y:{{beginAtZero:false,ticks:{{callback:(v)=>fmt(v,'n')}}}}, x:{{grid:{{display:false}}}} }}
            }}
        }});
    }}

    if (p.length === 0) return;
    const avgOpen = p.reduce((a,x)=>a+x.open_rate,0)/p.length;
    const avgClick = p.reduce((a,x)=>a+x.click_rate,0)/p.length;
    const avgCTO = p.reduce((a,x)=>a+x.cto_rate,0)/p.length;

    const tooltipTitle = (items) => p[items[0].dataIndex]?.title || '';
    const pctLabel = (ctx) => ctx.dataset.label+': '+ctx.parsed.y.toFixed(1)+'%';
    const pctTick = (v) => v+'%';
    const lineOpts = (color, avg) => ({{
        responsive:true, maintainAspectRatio:false,
        plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true}}}}, tooltip:{{callbacks:{{title:tooltipTitle, label:pctLabel}}}} }},
        scales:{{ y:{{beginAtZero:true, ticks:{{callback:pctTick}}}}, x:{{ticks:{{maxRotation:45,font:{{size:10}}}}}} }}
    }});

    // 2. Open Rate
    charts.open = new Chart(document.getElementById('c-open'), {{
        type:'line',
        data:{{ labels:dates, datasets:[
            {{label:'Open Rate',data:p.map(x=>x.open_rate),borderColor:COLORS[2],backgroundColor:COLORS[2]+'20',fill:true,tension:0.3,borderWidth:2,pointRadius:3,pointHoverRadius:6}},
            {{label:'Média ('+avgOpen.toFixed(1)+'%)',data:p.map(()=>avgOpen),borderColor:'#999',borderDash:[5,5],borderWidth:1,pointRadius:0}}
        ]}},
        options:lineOpts(COLORS[2], avgOpen)
    }});

    // 3. Click Rate
    charts.click = new Chart(document.getElementById('c-click'), {{
        type:'line',
        data:{{ labels:dates, datasets:[
            {{label:'Click Rate',data:p.map(x=>x.click_rate),borderColor:COLORS[0],backgroundColor:COLORS[0]+'20',fill:true,tension:0.3,borderWidth:2,pointRadius:3,pointHoverRadius:6}},
            {{label:'Média ('+avgClick.toFixed(1)+'%)',data:p.map(()=>avgClick),borderColor:'#999',borderDash:[5,5],borderWidth:1,pointRadius:0}}
        ]}},
        options:lineOpts(COLORS[0], avgClick)
    }});

    // 4. CTOR
    charts.ctor = new Chart(document.getElementById('c-ctor'), {{
        type:'line',
        data:{{ labels:dates, datasets:[
            {{label:'CTOR',data:p.map(x=>x.cto_rate),borderColor:COLORS[4],backgroundColor:COLORS[4]+'20',fill:true,tension:0.3,borderWidth:2,pointRadius:3,pointHoverRadius:6}},
            {{label:'Média ('+avgCTO.toFixed(1)+'%)',data:p.map(()=>avgCTO),borderColor:'#999',borderDash:[5,5],borderWidth:1,pointRadius:0}}
        ]}},
        options:lineOpts(COLORS[4], avgCTO)
    }});

    // 5. Unsub Rate
    charts.unsub = new Chart(document.getElementById('c-unsub'), {{
        type:'bar',
        data:{{ labels:dates, datasets:[
            {{label:'Unsub Rate',data:p.map(x=>x.unsub_rate),backgroundColor:p.map(x=>x.unsub_rate>1?COLORS[3]+'CC':COLORS[1]+'88'),borderRadius:3}}
        ]}},
        options:{{ responsive:true, maintainAspectRatio:false,
            plugins:{{ legend:{{display:false}}, tooltip:{{callbacks:{{title:tooltipTitle, label:(ctx)=>'Unsub: '+ctx.parsed.y.toFixed(2)+'%'}}}} }},
            scales:{{ y:{{beginAtZero:true,ticks:{{callback:pctTick}}}}, x:{{ticks:{{maxRotation:45,font:{{size:10}}}}}} }}
        }}
    }});

    // 6. Open Rate Distribution
    const bins = [0,10,20,30,40,50,60,70,80,90,100];
    const hist = new Array(bins.length-1).fill(0);
    p.forEach(x => {{ const idx = Math.min(Math.floor(x.open_rate/10), hist.length-1); if(idx>=0) hist[idx]++; }});
    charts.openDist = new Chart(document.getElementById('c-open-dist'), {{
        type:'bar',
        data:{{ labels:bins.slice(0,-1).map((b,i)=>b+'-'+bins[i+1]+'%'), datasets:[{{label:'Edições',data:hist,backgroundColor:COLORS[1]+'BB',borderColor:COLORS[1],borderWidth:1,borderRadius:4}}] }},
        options:{{ responsive:true, maintainAspectRatio:false, plugins:{{legend:{{display:false}}}},
            scales:{{ y:{{beginAtZero:true,title:{{display:true,text:'Nº de edições'}}}}, x:{{title:{{display:true,text:'Open Rate'}}}} }}
        }}
    }});

    // 7. Best Day of Week
    const dayData = Array.from({{length:7}},()=>({{sum:0,count:0}}));
    p.forEach(x => {{ if (x.day_of_week!=null) {{ dayData[x.day_of_week].sum+=x.open_rate; dayData[x.day_of_week].count++; }} }});
    const dayAvg = dayData.map(d => d.count>0 ? d.sum/d.count : 0);
    const maxDay = Math.max(...dayAvg);
    charts.weekday = new Chart(document.getElementById('c-weekday'), {{
        type:'bar',
        data:{{ labels:DAYS, datasets:[{{label:'Avg Open Rate',data:dayAvg,backgroundColor:dayAvg.map(v=>v===maxDay?COLORS[0]+'CC':COLORS[1]+'88'),borderRadius:6}}] }},
        options:{{ responsive:true, maintainAspectRatio:false,
            plugins:{{ legend:{{display:false}}, tooltip:{{callbacks:{{label:(ctx)=>'Open Rate: '+ctx.parsed.y.toFixed(1)+'% ('+dayData[ctx.dataIndex].count+' edições)'}}}} }},
            scales:{{ y:{{beginAtZero:true,ticks:{{callback:pctTick}}}} }}
        }}
    }});

    // 8. Funnel
    charts.funnel = new Chart(document.getElementById('c-funnel'), {{
        type:'bar',
        data:{{ labels:dates, datasets:[
            {{label:'Enviados',data:p.map(x=>x.delivered),backgroundColor:COLORS[1]+'66',borderColor:COLORS[1],borderWidth:1,borderRadius:2}},
            {{label:'Abertos',data:p.map(x=>x.unique_opens),backgroundColor:COLORS[2]+'88',borderColor:COLORS[2],borderWidth:1,borderRadius:2}},
            {{label:'Clicados',data:p.map(x=>x.unique_clicks),backgroundColor:COLORS[0]+'AA',borderColor:COLORS[0],borderWidth:1,borderRadius:2}}
        ]}},
        options:{{ responsive:true, maintainAspectRatio:false, interaction:{{mode:'index',intersect:false}},
            plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true}}}}, tooltip:{{callbacks:{{title:tooltipTitle}}}} }},
            scales:{{ y:{{beginAtZero:true,ticks:{{callback:(v)=>fmt(v,'n')}}}}, x:{{ticks:{{maxRotation:45,font:{{size:10}}}}}} }}
        }}
    }});

    // 9. Web vs Email
    const hasWeb = p.some(x => x.web_views > 0);
    if (hasWeb) {{
        charts.web = new Chart(document.getElementById('c-web'), {{
            type:'bar',
            data:{{ labels:dates, datasets:[
                {{label:'Email Opens',data:p.map(x=>x.unique_opens),backgroundColor:COLORS[1]+'88',borderRadius:3}},
                {{label:'Web Views',data:p.map(x=>x.web_views),backgroundColor:COLORS[2]+'88',borderRadius:3}},
                {{label:'Email Clicks',data:p.map(x=>x.unique_clicks),backgroundColor:COLORS[0]+'88',borderRadius:3}},
                {{label:'Web Clicks',data:p.map(x=>x.web_clicks),backgroundColor:COLORS[4]+'88',borderRadius:3}}
            ]}},
            options:{{ responsive:true, maintainAspectRatio:false, interaction:{{mode:'index',intersect:false}},
                plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true}}}}, tooltip:{{callbacks:{{title:tooltipTitle}}}} }},
                scales:{{ y:{{beginAtZero:true,ticks:{{callback:(v)=>fmt(v,'n')}}}}, x:{{ticks:{{maxRotation:45,font:{{size:10}}}}}} }}
            }}
        }});
    }} else {{
        document.getElementById('c-web').parentElement.parentElement.innerHTML = '<div class="chart-box"><h3>Email vs Web</h3><p style="color:var(--text2);padding:40px;text-align:center">Sem dados de web views nos posts.</p></div>';
    }}

    // 10. Top Links (agregado de todos os posts)
    const linkMap = {{}};
    p.forEach(x => {{
        (x.top_links || []).forEach(lnk => {{
            const url = lnk.url || '';
            if (!url) return;
            if (!linkMap[url]) linkMap[url] = {{url, total:0, unique:0}};
            linkMap[url].total += lnk.total_clicks || 0;
            linkMap[url].unique += lnk.unique_clicks || 0;
        }});
    }});
    const topLinks = Object.values(linkMap).sort((a,b) => b.unique - a.unique).slice(0, 15);
    if (topLinks.length > 0) {{
        const shortUrls = topLinks.map(l => {{
            try {{ const u = new URL(l.url); return u.hostname + u.pathname.slice(0,30); }} catch {{ return l.url.slice(0,40); }}
        }});
        charts.toplinks = new Chart(document.getElementById('c-toplinks'), {{
            type:'bar',
            data:{{ labels:shortUrls, datasets:[
                {{label:'Cliques Únicos',data:topLinks.map(l=>l.unique),backgroundColor:COLORS[0]+'AA',borderRadius:4}},
                {{label:'Cliques Totais',data:topLinks.map(l=>l.total),backgroundColor:COLORS[1]+'66',borderRadius:4}}
            ]}},
            options:{{ responsive:true, maintainAspectRatio:false, indexAxis:'y',
                plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true}}}},
                    tooltip:{{callbacks:{{afterLabel:(ctx)=>topLinks[ctx.dataIndex].url}}}} }},
                scales:{{ x:{{beginAtZero:true,ticks:{{callback:(v)=>fmt(v,'n')}}}}, y:{{ticks:{{font:{{size:10}}}}}} }}
            }}
        }});
    }} else {{
        document.getElementById('c-toplinks').parentElement.parentElement.innerHTML = '<div class="chart-box"><h3>Top Links</h3><p style="color:var(--text2);padding:40px;text-align:center">Sem dados de clicks por URL.</p></div>';
    }}
}}

// ── Table ──
function renderTable() {{
    const p = filteredPosts;
    if (!p.length) {{ document.getElementById('tbl').innerHTML = '<p style="color:var(--text2)">Nenhum post no período.</p>'; return; }}

    const cols = [
        {{f:'title',l:'Edição',fmt:null}},
        {{f:'date_label',l:'Data',fmt:null}},
        {{f:'delivered',l:'Enviados',fmt:'n'}},
        {{f:'unique_opens',l:'Abertos',fmt:'n'}},
        {{f:'open_rate',l:'Open Rate',fmt:'bar-green'}},
        {{f:'unique_clicks',l:'Cliques',fmt:'n'}},
        {{f:'click_rate',l:'Click Rate',fmt:'bar-orange'}},
        {{f:'cto_rate',l:'CTOR',fmt:'%'}},
        {{f:'unsubscribes',l:'Unsubs',fmt:'n'}},
        {{f:'web_views',l:'Web Views',fmt:'n'}},
    ];

    let sortCol = 'date', sortDir = 'desc';
    const maxOpen = Math.max(...p.map(x=>x.open_rate));
    const maxClick = Math.max(...p.map(x=>x.click_rate));

    function render(sorted) {{
        let h = '<table><thead><tr>';
        cols.forEach(c => {{
            const arrow = sortCol===c.f ? (sortDir==='asc'?' ▲':' ▼') : '';
            h += '<th data-col="'+c.f+'">'+c.l+arrow+'</th>';
        }});
        h += '</tr></thead><tbody>';
        sorted.forEach(r => {{
            h += '<tr>';
            cols.forEach(c => {{
                let v = r[c.f];
                if (c.fmt==='n') v = fmt(v,'n');
                else if (c.fmt==='%') v = fmt(v,'%');
                else if (c.fmt==='bar-green') {{
                    const w = maxOpen>0 ? (v/maxOpen*60) : 0;
                    v = '<span class="bar" style="width:'+w+'px;background:var(--teal)"></span>'+v.toFixed(1)+'%';
                }} else if (c.fmt==='bar-orange') {{
                    const w = maxClick>0 ? (v/maxClick*60) : 0;
                    v = '<span class="bar" style="width:'+w+'px;background:var(--orange)"></span>'+v.toFixed(1)+'%';
                }}
                h += '<td>'+v+'</td>';
            }});
            h += '</tr>';
        }});
        h += '</tbody></table>';
        document.getElementById('tbl').innerHTML = h;

        document.querySelectorAll('#tbl th').forEach(th => {{
            th.addEventListener('click', () => {{
                const col = th.dataset.col;
                if (sortCol===col) sortDir = sortDir==='asc'?'desc':'asc';
                else {{ sortCol=col; sortDir='desc'; }}
                doSort();
            }});
        }});
    }}

    function doSort() {{
        const sorted = [...p].sort((a,b) => {{
            let av=a[sortCol], bv=b[sortCol];
            if (typeof av==='string') {{ av=av.toLowerCase(); bv=bv.toLowerCase(); }}
            const cmp = av<bv?-1:av>bv?1:0;
            return sortDir==='asc'?cmp:-cmp;
        }});
        render(sorted);
    }}
    doSort();
}}

// Raw stats debug
if (POSTS_RAW.length > 0 && POSTS_RAW[0].raw_stats) {{
    document.getElementById('raw-stats').textContent = JSON.stringify(POSTS_RAW[0].raw_stats, null, 2);
}}

// Init
applyFilters();
</script>
</body>
</html>"""

    return html


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("  Beehiiv Newsletter Analytics")
    print("=" * 60)
    print(f"  Publication: {PUB_ID}")
    print(f"  Output: {OUTPUT_FILE}")

    # Fetch data
    raw_posts = fetch_posts()
    raw_subs = fetch_subscribers()

    if not raw_posts and not raw_subs.get("raw"):
        print("\n❌ Nenhum dado encontrado. Verifique seu API key e Publication ID.")
        sys.exit(1)

    # Debug: mostra estrutura do primeiro post
    if raw_posts:
        first = raw_posts[0]
        print("\n🔍 Estrutura do primeiro post (stats):")
        stats = first.get("stats", {})
        if isinstance(stats, dict):
            for k, v in stats.items():
                print(f"    {k}: {type(v).__name__} = {repr(v)[:120]}")
        else:
            print(f"    stats é {type(stats).__name__}: {repr(stats)[:200]}")

    # Process
    print("\n⚙️  Processando dados...")
    posts = process_posts(raw_posts) if raw_posts else []
    subscribers = process_subscribers(raw_subs, posts) if raw_subs else {"total": 0, "active": 0, "inactive": 0, "timeline_subs": [], "timeline_posts": []}

    print(f"  Posts processados: {len(posts)}")
    if subscribers.get("is_sampled"):
        print(f"  Subscribers: ~{subscribers['total']:,} total (amostra de {subscribers['sample_size']:,}, ~{subscribers['active_rate_sample']}% ativos)")
    else:
        print(f"  Subscribers: {subscribers['total']:,} (ativos: {subscribers['active']:,})")

    # Grab a raw stats sample for debug
    raw_sample = raw_posts[0].get("stats", {}) if raw_posts else {}

    # Generate dashboard
    print("\n🎨 Gerando dashboard...")
    html = generate_dashboard(posts, subscribers, raw_sample)

    # Save
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ Dashboard gerado: {output_path}")
    print(f"   Abra no navegador para visualizar!")

    # Also save raw JSON for reference
    json_path = output_path.replace(".html", "_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"posts": posts, "subscribers": subscribers}, f, ensure_ascii=False, indent=2, default=str)
    print(f"   Dados brutos: {json_path}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
