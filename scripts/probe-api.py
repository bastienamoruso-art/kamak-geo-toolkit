#!/usr/bin/env python3
"""
probe-api.py — Tape les APIs LLM en local pour mesurer la visibilité IA.

Lit un persona depuis prompts.json, soumet chaque prompt à OpenAI,
Anthropic, Perplexity et Mistral (selon les clés API disponibles),
détecte la mention de votre marque, les concurrents cités et les
sources retournées, puis produit un CSV + un rapport HTML.

L'angle : ce que les outils GEO du marché vendent 50-200 €/mois,
fait en local pour 2-5 € de tokens par run complet (8 personas
× 15 prompts × 4 modèles = 480 appels).

À utiliser EN COMPLÉMENT du test manuel dans l'interface réelle
(template prompts/) et du parsing logs (parse-logs.py). L'API
n'est PAS l'interface réelle : pas d'historique, pas d'abonnement,
pas de géolocalisation, pas de routing dynamique entre versions.

Usage :
    export OPENAI_API_KEY=sk-...
    export ANTHROPIC_API_KEY=sk-ant-...
    export PERPLEXITY_API_KEY=pplx-...
    export MISTRAL_API_KEY=...

    python probe-api.py \\
        --persona 01-cgp-courtier \\
        --brand "Aeconomia" \\
        --competitors "Cafpi,Empruntis,Meilleurtaux" \\
        --variables '{"VILLE":"Orléans","ZONE":"Loiret","TICKET":"250 000 €","SPECIALITE":"primo-accédants"}' \\
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
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "env": "OPENAI_API_KEY",
    },
    "anthropic": {
        "name": "claude-sonnet-4-5",
        "endpoint": "https://api.anthropic.com/v1/messages",
        "env": "ANTHROPIC_API_KEY",
    },
    "perplexity": {
        "name": "sonar",
        "endpoint": "https://api.perplexity.ai/chat/completions",
        "env": "PERPLEXITY_API_KEY",
    },
    "gemini": {
        "name": "gemini-2.5-flash",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        "env": "GEMINI_API_KEY",
    },
    "mistral": {
        "name": "mistral-large-latest",
        "endpoint": "https://api.mistral.ai/v1/chat/completions",
        "env": "MISTRAL_API_KEY",
    },
}


def _http_post(url, body, headers, timeout=60):
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


def call_openai(prompt, key):
    return _http_post(
        MODELS["openai"]["endpoint"],
        {"model": MODELS["openai"]["name"], "messages": [{"role": "user", "content": prompt}]},
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )


def call_anthropic(prompt, key):
    return _http_post(
        MODELS["anthropic"]["endpoint"],
        {
            "model": MODELS["anthropic"]["name"],
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        },
        {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )


def call_perplexity(prompt, key):
    return _http_post(
        MODELS["perplexity"]["endpoint"],
        {
            "model": MODELS["perplexity"]["name"],
            "messages": [{"role": "user", "content": prompt}],
            "return_citations": True,
        },
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )


def call_gemini(prompt, key):
    return _http_post(
        f"{MODELS['gemini']['endpoint']}?key={key}",
        {"contents": [{"parts": [{"text": prompt}]}]},
        {"Content-Type": "application/json"},
    )


def call_mistral(prompt, key):
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
            return resp["content"][0]["text"]
        if provider == "gemini":
            return resp["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None
    return None


URL_RE = re.compile(r"https?://[^\s\)\]\,\"\<\>]+")


def extract_citations(provider, resp, text):
    if not isinstance(resp, dict) or "error" in resp or not text:
        return []
    urls = set()
    if provider == "perplexity" and isinstance(resp.get("citations"), list):
        urls.update(resp["citations"])
    urls.update(URL_RE.findall(text))
    return sorted(urls)


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


def main():
    parser = argparse.ArgumentParser(
        description="Probe les APIs LLM pour mesurer la visibilité IA d'une marque.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemple :\n"
            "  python probe-api.py --persona 01-cgp-courtier --brand 'Aeconomia' \\\n"
            "    --competitors 'Cafpi,Empruntis' \\\n"
            "    --variables '{\"VILLE\":\"Orléans\",\"ZONE\":\"Loiret\"}'\n"
        ),
    )
    parser.add_argument("--prompts", default=None, help="Chemin prompts.json (defaut: ../prompts/prompts.json)")
    parser.add_argument("--persona", required=True, help="ID persona (ex: 01-cgp-courtier)")
    parser.add_argument("--brand", required=True, help="Votre marque (pour detection mention)")
    parser.add_argument("--competitors", default="", help="Concurrents separes par virgule")
    parser.add_argument("--variables", default="{}", help="JSON inline override des variables")
    parser.add_argument("--models", default="openai,anthropic,perplexity,gemini,mistral", help="Liste providers")
    parser.add_argument("--out", default="./probe-report", help="Dossier de sortie")
    parser.add_argument("--csv-only", action="store_true", help="Ne produire que le CSV")
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
        print(f"Marque : {args.brand}")
        print(f"Concurrents : {competitors}")
        print()
        for prompt_def in persona["prompts"]:
            print(f"  [{prompt_def['id']}] {substitute(prompt_def['text'], variables)}")
        return

    api_keys = {}
    for p in providers:
        key = os.environ.get(MODELS[p]["env"])
        if not key:
            sys.exit(f"Cle API manquante pour {p} : variable d'env {MODELS[p]['env']}")
        api_keys[p] = key

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(persona["prompts"]) * len(providers)
    print(f"Probing {len(persona['prompts'])} prompts x {len(providers)} providers ({total} calls)...", file=sys.stderr)

    counter = 0
    for prompt_def in persona["prompts"]:
        prompt_text = substitute(prompt_def["text"], variables)
        for provider in providers:
            counter += 1
            print(f"  [{counter}/{total}] {provider} #{prompt_def['id']}", file=sys.stderr)
            resp = CALLERS[provider](prompt_text, api_keys[provider])
            text = extract_text(provider, resp)
            citations = extract_citations(provider, resp, text)
            mentioned, position = detect_brand(text, args.brand)
            comp_found = detect_competitors(text, competitors)
            results.append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "prompt_id": prompt_def["id"],
                "prompt_category": prompt_def["category"],
                "prompt": prompt_text,
                "provider": provider,
                "model": MODELS[provider]["name"],
                "brand_mentioned": "oui" if mentioned else "non",
                "brand_position": position,
                "competitors_found": ", ".join(comp_found),
                "citations_count": len(citations),
                "citations": " | ".join(citations[:5]),
                "response_text": (text or "")[:600],
                "error": resp.get("error", "") if isinstance(resp, dict) else "",
            })

    csv_path = out_dir / "probe-hits.csv"
    fieldnames = [
        "timestamp", "prompt_id", "prompt_category", "provider", "model",
        "brand_mentioned", "brand_position", "competitors_found",
        "citations_count", "citations", "prompt", "response_text", "error",
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
        by_provider[p] = {
            "total": len(results_p),
            "mentioned": len(mentioned),
            "errors": len(errors),
            "mention_rate": round(len(mentioned) / max(len(results_p), 1) * 100, 1),
            "model": MODELS[p]["name"],
            "competitor_counts": sorted(comp_counts.items(), key=lambda x: -x[1]),
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
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML : {html_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
