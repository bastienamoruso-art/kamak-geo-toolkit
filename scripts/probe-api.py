#!/usr/bin/env python3
"""
probe-api.py — Tape les APIs LLM en local pour mesurer la visibilité IA.

Lit un persona depuis prompts.json, soumet chaque prompt à OpenAI,
Anthropic, Perplexity, Gemini (et Mistral en opt-in), selon les
clés API disponibles. Détecte la mention de votre marque, les
concurrents cités, et — avec --web-search — les sources réelles
que les modèles utilisent (vérifiables, pas hallucinées).

L'angle : ce que les outils GEO du marché vendent 50-200 €/mois,
fait en local pour 2-5 € de tokens par run complet.

À utiliser EN COMPLÉMENT du test manuel dans l'interface réelle
(template prompts/) et du parsing logs (parse-logs.py).

Usage :
    export OPENAI_API_KEY=sk-...
    export ANTHROPIC_API_KEY=sk-ant-...
    export PERPLEXITY_API_KEY=pplx-...
    export GEMINI_API_KEY=...
    export MISTRAL_API_KEY=...   # opt-in

    python probe-api.py \\
        --persona 01-cgp-courtier \\
        --brand "Aeconomia" \\
        --competitors "Cafpi,Empruntis,Meilleurtaux" \\
        --variables '{"VILLE":"Orléans","ZONE":"Loiret"}' \\
        --web-search \\
        --out ./probe-report
"""

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


MODELS = {
    "openai": {
        "name": "gpt-4o-mini",
        "name_search": "gpt-4o-mini-search-preview",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "env": "OPENAI_API_KEY",
    },
    "anthropic": {
        "name": "claude-sonnet-4-5",
        "name_search": "claude-sonnet-4-5",
        "endpoint": "https://api.anthropic.com/v1/messages",
        "env": "ANTHROPIC_API_KEY",
    },
    "perplexity": {
        "name": "sonar",
        "name_search": "sonar",
        "endpoint": "https://api.perplexity.ai/chat/completions",
        "env": "PERPLEXITY_API_KEY",
    },
    "gemini": {
        "name": "gemini-2.5-flash",
        "name_search": "gemini-2.5-flash",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        "env": "GEMINI_API_KEY",
    },
    "mistral": {
        "name": "mistral-large-latest",
        "name_search": "mistral-large-latest",
        "endpoint": "https://api.mistral.ai/v1/chat/completions",
        "env": "MISTRAL_API_KEY",
    },
}


def _http_post(url, body, headers, timeout=120):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body_text[:300]}"}
    except Exception as e:
        return {"error": str(e)}


def call_openai(prompt, key, web_search=False):
    model = MODELS["openai"]["name_search"] if web_search else MODELS["openai"]["name"]
    body = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    if web_search:
        body["web_search_options"] = {}
    return _http_post(
        MODELS["openai"]["endpoint"],
        body,
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )


def call_anthropic(prompt, key, web_search=False):
    body = {
        "model": MODELS["anthropic"]["name"],
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    if web_search:
        body["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]
    return _http_post(
        MODELS["anthropic"]["endpoint"],
        body,
        {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )


def call_perplexity(prompt, key, web_search=False):
    return _http_post(
        MODELS["perplexity"]["endpoint"],
        {
            "model": MODELS["perplexity"]["name"],
            "messages": [{"role": "user", "content": prompt}],
            "return_citations": True,
        },
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )


def call_gemini(prompt, key, web_search=False):
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    if web_search:
        body["tools"] = [{"google_search": {}}]
    return _http_post(
        f"{MODELS['gemini']['endpoint']}?key={key}",
        body,
        {"Content-Type": "application/json"},
    )


def call_mistral(prompt, key, web_search=False):
    if web_search:
        print("    [warning] Mistral n'a pas de web_search natif simple via API. Appel sans search.", file=sys.stderr)
    return _http_post(
        MODELS["mistral"]["endpoint"],
        {"model": MODELS["mistral"]["name"], "messages": [{"role": "user", "content": prompt}]},
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )


CALLERS = {
    "openai": call_openai,
    "anthropic": call_anthropic,
    "perplexity": call_perplexity,
    "gemini": call_gemini,
    "mistral": call_mistral,
}


def extract_text(provider, resp):
    if not isinstance(resp, dict) or "error" in resp:
        return None
    try:
        if provider in ("openai", "perplexity", "mistral"):
            return resp["choices"][0]["message"]["content"]
        if provider == "anthropic":
            # Concat tous les blocs de type "text"
            parts = []
            for block in resp.get("content", []):
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "\n".join(parts) if parts else None
        if provider == "gemini":
            parts = resp["candidates"][0]["content"]["parts"]
            return "\n".join(p.get("text", "") for p in parts if isinstance(p, dict))
    except (KeyError, IndexError, TypeError):
        return None
    return None


URL_RE = re.compile(r"https?://[^\s\)\]\,\"\<\>]+")


def extract_citations(provider, resp, text):
    """Citations structurées issues du web search natif quand disponible, sinon URLs dans le texte."""
    if not isinstance(resp, dict) or "error" in resp:
        return []
    urls = set()
    titles = {}

    try:
        if provider == "openai":
            # Chat Completions search-preview : annotations dans message
            msg = resp.get("choices", [{}])[0].get("message", {})
            for ann in msg.get("annotations", []) or []:
                if ann.get("type") == "url_citation":
                    uc = ann.get("url_citation", {})
                    url = uc.get("url")
                    if url:
                        urls.add(url)
                        if uc.get("title"):
                            titles[url] = uc["title"]

        elif provider == "anthropic":
            # Citations attachees aux blocs text + tool_result si web_search
            for block in resp.get("content", []):
                if not isinstance(block, dict):
                    continue
                # Citations attachees au text
                for cit in block.get("citations", []) or []:
                    url = cit.get("url")
                    if url:
                        urls.add(url)
                        if cit.get("title"):
                            titles[url] = cit["title"]
                # Tool result : contient les resultats de recherche
                if block.get("type") == "web_search_tool_result":
                    content = block.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                url = item.get("url")
                                if url:
                                    urls.add(url)
                                    if item.get("title"):
                                        titles[url] = item["title"]

        elif provider == "perplexity":
            for url in resp.get("citations", []) or []:
                if url:
                    urls.add(url)
            # Aussi search_results si present
            for item in resp.get("search_results", []) or []:
                if isinstance(item, dict) and item.get("url"):
                    urls.add(item["url"])
                    if item.get("title"):
                        titles[item["url"]] = item["title"]

        elif provider == "gemini":
            cand = resp.get("candidates", [{}])[0]
            gm = cand.get("groundingMetadata", {})
            for chunk in gm.get("groundingChunks", []) or []:
                if isinstance(chunk, dict) and chunk.get("web"):
                    web = chunk["web"]
                    uri = web.get("uri")
                    title = web.get("title")
                    # Gemini retourne souvent des redirects vertexaisearch.cloud.google.com
                    # avec le vrai domaine dans le title. On stocke comme cle le title
                    # quand c'est le cas pour faciliter l'agregation.
                    if uri and "vertexaisearch.cloud.google.com" in uri and title:
                        # title est genre "cafpi.fr" ou "Cafpi - courtier crédit"
                        # on garde l'uri mais on stocke title comme clef domaine
                        urls.add(uri)
                        titles[uri] = title
                    elif uri:
                        urls.add(uri)
                        if title:
                            titles[uri] = title
    except (KeyError, IndexError, TypeError):
        pass

    # Fallback : URLs trouvées dans le texte (utile sans web_search)
    if text:
        urls.update(URL_RE.findall(text))

    return sorted(urls), titles


def detect_brand(text, brand):
    if not text or not brand:
        return False, ""
    m = re.search(re.escape(brand), text, re.IGNORECASE)
    if not m:
        return False, ""
    pos = m.start() / max(len(text), 1)
    band = "intro" if pos < 0.25 else "corps" if pos < 0.75 else "fin"
    return True, band


def detect_competitors(text, competitors):
    if not text or not competitors:
        return []
    return [c for c in competitors if re.search(re.escape(c), text, re.IGNORECASE)]


def substitute(prompt, variables):
    for k, v in variables.items():
        prompt = prompt.replace("{" + k + "}", str(v))
    return prompt


def domain_of(url, title=None):
    """Extrait le domaine d'une URL pour agrégation.
    Si l'URL est une redirection (Vertex AI Gemini), tente de tirer le domaine du titre."""
    # Cas Gemini redirect : extraire le domaine du titre si possible
    if url and "vertexaisearch.cloud.google.com" in url and title:
        # Le titre Gemini est souvent juste le domaine : "cafpi.fr"
        m = re.search(r"\b([a-z0-9][a-z0-9\-]{1,62}\.(?:fr|com|net|org|info|eu|io|ai|gouv\.fr))\b", title.lower())
        if m:
            return m.group(1)
        return title.lower()
    m = re.match(r"https?://(?:www\.)?([^/\s]+)", url, re.IGNORECASE)
    return m.group(1).lower() if m else url


def main():
    parser = argparse.ArgumentParser(
        description="Probe les APIs LLM pour mesurer la visibilité IA d'une marque.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemple :\n"
            "  python probe-api.py --persona 01-cgp-courtier --brand 'Aeconomia' \\\n"
            "    --competitors 'Cafpi,Empruntis' --web-search \\\n"
            "    --variables '{\"VILLE\":\"Orléans\",\"ZONE\":\"Loiret\"}'\n"
        ),
    )
    parser.add_argument("--prompts", default=None, help="Chemin prompts.json (defaut: ../prompts/prompts.json)")
    parser.add_argument("--persona", required=True, help="ID persona (ex: 01-cgp-courtier)")
    parser.add_argument("--brand", required=True, help="Votre marque (pour detection mention)")
    parser.add_argument("--competitors", default="", help="Concurrents separes par virgule")
    parser.add_argument("--variables", default="{}", help="JSON inline override des variables")
    parser.add_argument("--models", default="openai,anthropic,perplexity,gemini", help="Liste providers (defaut: openai,anthropic,perplexity,gemini ; mistral disponible mais opt-in)")
    parser.add_argument("--out", default="./probe-report", help="Dossier de sortie")
    parser.add_argument("--csv-only", action="store_true", help="Ne produire que le CSV")
    parser.add_argument("--web-search", action="store_true", help="Active le web search NATIF sur chaque provider (OpenAI gpt-4o-mini-search-preview, Anthropic tool web_search, Gemini google_search, Perplexity natif). Sources reelles + verifiables. Cout legerement plus eleve.")
    parser.add_argument("--dry-run", action="store_true", help="Affiche les prompts substitues sans appeler les APIs")

    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    prompts_path = Path(args.prompts) if args.prompts else script_dir.parent / "prompts" / "prompts.json"
    if not prompts_path.exists():
        sys.exit(f"Erreur : prompts.json introuvable : {prompts_path}")

    with open(prompts_path, encoding="utf-8") as f:
        data = json.load(f)

    personas = {p["id"]: p for p in data["personas"]}
    if args.persona not in personas:
        sys.exit(f"Erreur : persona '{args.persona}' inconnu. Disponibles : {', '.join(personas.keys())}")
    persona = personas[args.persona]

    try:
        variables = json.loads(args.variables)
    except json.JSONDecodeError as e:
        sys.exit(f"Erreur : --variables doit etre un JSON valide ({e})")

    competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]
    providers = [p.strip() for p in args.models.split(",") if p.strip()]
    for p in providers:
        if p not in MODELS:
            sys.exit(f"Provider inconnu : {p}. Choix : {', '.join(MODELS.keys())}")

    if args.dry_run:
        print(f"Dry-run sur persona {persona['id']} ({len(persona['prompts'])} prompts)")
        print(f"Variables : {variables}")
        print(f"Providers : {providers}")
        print(f"Web search : {'ACTIVE' if args.web_search else 'desactive'}")
        print(f"Marque : {args.brand}")
        print(f"Concurrents : {competitors}")
        print()
        for prompt_def in persona["prompts"]:
            print(f"  [{prompt_def['id']}] {substitute(prompt_def['text'], variables)}")
        return

    api_keys = {}
    skipped = []
    for p in providers:
        key = os.environ.get(MODELS[p]["env"])
        if not key:
            skipped.append(f"{p} (variable {MODELS[p]['env']} absente)")
            continue
        api_keys[p] = key
    if skipped:
        print(f"Providers skippes : {', '.join(skipped)}", file=sys.stderr)
    providers = [p for p in providers if p in api_keys]
    if not providers:
        sys.exit("Aucune cle API disponible. Renseignez au moins une variable d'env (cf. .env.example).")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(persona["prompts"]) * len(providers)
    print(f"Probing {len(persona['prompts'])} prompts x {len(providers)} providers ({total} calls). Web search: {'ON' if args.web_search else 'OFF'}", file=sys.stderr)

    counter = 0
    for prompt_def in persona["prompts"]:
        prompt_text = substitute(prompt_def["text"], variables)
        for provider in providers:
            counter += 1
            print(f"  [{counter}/{total}] {provider} #{prompt_def['id']}", file=sys.stderr)
            resp = CALLERS[provider](prompt_text, api_keys[provider], web_search=args.web_search)
            text = extract_text(provider, resp)
            urls, titles = extract_citations(provider, resp, text)
            mentioned, position = detect_brand(text, args.brand)
            comp_found = detect_competitors(text, competitors)

            # Domaines uniques pour agregation
            domains = sorted(set(domain_of(u, titles.get(u)) for u in urls))

            results.append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "prompt_id": prompt_def["id"],
                "prompt_category": prompt_def["category"],
                "prompt": prompt_text,
                "provider": provider,
                "model": MODELS[provider]["name_search"] if args.web_search else MODELS[provider]["name"],
                "brand_mentioned": "oui" if mentioned else "non",
                "brand_position": position,
                "competitors_found": ", ".join(comp_found),
                "citations_count": len(urls),
                "citations": " | ".join(urls[:5]),
                "domains_count": len(domains),
                "domains": " | ".join(domains[:10]),
                "response_text": (text or "")[:600],
                "error": resp.get("error", "") if isinstance(resp, dict) else "",
            })

    csv_path = out_dir / "probe-hits.csv"
    fieldnames = [
        "timestamp", "prompt_id", "prompt_category", "provider", "model",
        "brand_mentioned", "brand_position", "competitors_found",
        "citations_count", "citations", "domains_count", "domains",
        "prompt", "response_text", "error",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"CSV  : {csv_path}", file=sys.stderr)

    if args.csv_only:
        return

    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        sys.exit("Jinja2 manquant. Install : pip install jinja2")

    env = Environment(
        loader=FileSystemLoader(str(script_dir / "templates")),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("probe-report.html")

    by_provider = {}
    for p in providers:
        results_p = [r for r in results if r["provider"] == p]
        mentioned = [r for r in results_p if r["brand_mentioned"] == "oui"]
        errors = [r for r in results_p if r["error"]]
        all_competitors = []
        for r in results_p:
            if r["competitors_found"]:
                all_competitors.extend([c.strip() for c in r["competitors_found"].split(",")])
        comp_counts = {}
        for c in all_competitors:
            comp_counts[c] = comp_counts.get(c, 0) + 1
        # Domaines aggregés (sources web search)
        all_domains = []
        for r in results_p:
            if r.get("domains"):
                all_domains.extend([d.strip() for d in r["domains"].split("|") if d.strip()])
        domain_counts = {}
        for d in all_domains:
            domain_counts[d] = domain_counts.get(d, 0) + 1
        by_provider[p] = {
            "total": len(results_p),
            "mentioned": len(mentioned),
            "errors": len(errors),
            "mention_rate": round(len(mentioned) / max(len(results_p), 1) * 100, 1),
            "model": results_p[0]["model"] if results_p else MODELS[p]["name"],
            "competitor_counts": sorted(comp_counts.items(), key=lambda x: -x[1]),
            "source_counts": sorted(domain_counts.items(), key=lambda x: -x[1])[:20],
        }

    html_path = out_dir / "probe-report.html"
    html = template.render(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        persona=persona,
        brand=args.brand,
        competitors=competitors,
        providers=providers,
        by_provider=by_provider,
        results=results,
        variables=variables,
        web_search=args.web_search,
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML : {html_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
