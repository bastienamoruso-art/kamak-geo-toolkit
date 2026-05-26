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
from collections import Counter
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


SOURCE_NOISE = {"google.com", "youtube.com", "vertexaisearch.cloud.google.com", "wikipedia.org", "fr.wikipedia.org", "calendar.google.com"}
SOURCE_INSTITUTIONNELLES = {"orias.fr", "amf-france.org", "anil.org", "service-public.fr", "economie.gouv.fr", "banque-france.fr", "cncgp.fr", "anacofi.asso.fr"}


def generate_insights(by_provider, brand, web_search, competitors):
    """Genere une liste d'insights actionnables a partir des stats agregees."""
    insights = []
    if not by_provider:
        return insights

    total_mentions = sum(s["mentioned"] for s in by_provider.values())
    total_calls = sum(s["total"] for s in by_provider.values())
    global_rate = total_mentions / max(total_calls, 1) * 100

    # 1. Verdict global mention marque
    if global_rate == 0:
        insights.append({
            "type": "critical",
            "title": f"{brand} absent de tous les providers",
            "detail": (
                f"0 mention sur {total_calls} prompts. "
                + (
                    "En mode web search, votre SEO ne vous remonte pas sur ces requêtes. Action : vérifier le ranking Google sur les prompts, et travailler la pression de marque (mentions tierces, comparateurs)."
                    if web_search
                    else "Sans web search : votre marque n'est pas dans le corpus d'entraînement des modèles. Action prioritaire : pression de marque (PR, citations, Wikipedia, mentions par sites d'autorité). Relancez avec --web-search pour mesurer votre SEO réel."
                )
            ),
        })
    elif global_rate < 20:
        insights.append({
            "type": "warning",
            "title": f"{brand} marginalement présent ({global_rate:.0f}%)",
            "detail": f"{total_mentions} mentions sur {total_calls} prompts. Présence faible. Identifiez les prompts gagnants (en filtrant par provider dans la table ci-dessous) et étendez aux catégories voisines (FAQ, comparaison).",
        })
    elif global_rate < 50:
        insights.append({
            "type": "info",
            "title": f"{brand} présent mais non dominant ({global_rate:.0f}%)",
            "detail": f"{total_mentions} mentions sur {total_calls} prompts. Vous êtes connu. Action : capitaliser sur les recommandations (catégorie 'recommandation') où vous n'êtes pas encore cité.",
        })
    else:
        insights.append({
            "type": "ok",
            "title": f"{brand} bien représenté ({global_rate:.0f}%)",
            "detail": f"{total_mentions} mentions sur {total_calls} prompts. Position forte. Action : monitorer mois après mois pour ne pas perdre la position. Vérifier que les concurrents montants ne vous dépassent pas.",
        })

    # 2. Disparités entre providers
    rates = [(p, s["mention_rate"]) for p, s in by_provider.items() if s["total"] > 0]
    rates.sort(key=lambda x: -x[1])
    if len(rates) > 1:
        best, worst = rates[0], rates[-1]
        if best[1] - worst[1] >= 30:
            insights.append({
                "type": "info",
                "title": f"Disparité forte : {best[0]} ({best[1]:.0f}%) vs {worst[0]} ({worst[1]:.0f}%)",
                "detail": (
                    f"Vous êtes mieux indexé par certains corpus que d'autres. "
                    + (
                        "En mode search, c'est lié aux moteurs sous-jacents (Bing pour OpenAI, Google pour Gemini)."
                        if web_search
                        else "Indique que vos contenus sont dans certains corpus de training et pas d'autres. Travailler la diffusion (Common Crawl, Wikipedia, médias d'autorité)."
                    )
                ),
            })

    # 3. Concurrent leader
    all_comp = Counter()
    for s in by_provider.values():
        for c, n in s.get("competitor_counts", []):
            all_comp[c] += n
    if all_comp:
        top_comp, top_n = all_comp.most_common(1)[0]
        second = all_comp.most_common(2)[1] if len(all_comp) > 1 else None
        detail = f"{top_n} mentions cumulées sur {len(by_provider)} providers. C'est le concurrent que les modèles voient comme référence sur ce persona."
        if second:
            detail += f" Second : {second[0]} ({second[1]} mentions)."
        detail += " Analysez sur quels sites/contenus ce concurrent est cité pour comprendre l'écart."
        insights.append({
            "type": "info",
            "title": f"Concurrent dominant aux yeux des IA : {top_comp}",
            "detail": detail,
        })

    # 4. Top sources (uniquement si web search)
    if web_search:
        all_src = Counter()
        for s in by_provider.values():
            for src, n in s.get("source_counts", []):
                all_src[src] += n
        # Filtrer les sources de bruit (google, youtube, etc.)
        filtered = [(s, n) for s, n in all_src.most_common() if s.lower() not in SOURCE_NOISE]
        # Marque elle-meme citée ?
        brand_lower = brand.lower()
        brand_self_cited = [(s, n) for s, n in filtered if brand_lower in s.lower()]
        institutionnel = [(s, n) for s, n in filtered if s.lower() in SOURCE_INSTITUTIONNELLES]
        autres = [(s, n) for s, n in filtered if s.lower() not in SOURCE_INSTITUTIONNELLES and brand_lower not in s.lower()][:5]

        if autres:
            top_str = ", ".join(f"<strong>{s}</strong> ({n})" for s, n in autres[:3])
            insights.append({
                "type": "action",
                "title": "Top sources à viser",
                "detail": (
                    f"Les modèles puisent dans : {top_str}. Action : présence + contenu sur ces sites = leverage direct pour entrer dans le corpus. "
                    f"Vérifier que vos pages sont sur ces sites (fiches annuaires, articles invités, avis clients)."
                ),
            })

        if brand_self_cited:
            insights.append({
                "type": "ok",
                "title": f"Votre site est cité comme source",
                "detail": f"{brand_self_cited[0][0]} ressort {brand_self_cited[0][1]} fois. Bon signal SEO : votre propre contenu remonte dans les sources des modèles.",
            })

        if institutionnel:
            inst_str = ", ".join(f"<strong>{s}</strong>" for s, _ in institutionnel[:3])
            insights.append({
                "type": "info",
                "title": "Sources institutionnelles citées",
                "detail": f"Les modèles s'appuient sur {inst_str}. Vérifiez que votre marque est correctement référencée et trouvable sur ces sites d'autorité (ex: fiche ORIAS visible publiquement).",
            })

    return insights


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


def wizard(personas_data, prompts_path):
    """Mode interactif step-by-step. Retourne un dict de params."""
    BOLD = "\033[1m"
    DIM = "\033[2m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    RESET = "\033[0m"

    print()
    print(f"{BOLD}╭─ KAMAK GEO Toolkit · Probe API · Wizard ─╮{RESET}")
    print(f"{DIM}Sources prompts: {prompts_path}{RESET}")
    print()

    personas_list = personas_data["personas"]

    # 1. Persona
    print(f"{BOLD}[1/7] Persona{RESET}")
    for i, p in enumerate(personas_list, 1):
        print(f"  {i:>2}. {CYAN}{p['id']}{RESET} — {p['name']}")
    while True:
        choice = input(f"{DIM}Choix (1-{len(personas_list)}) : {RESET}").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(personas_list):
                persona = personas_list[idx]
                break
        except ValueError:
            pass
        print(f"{RED}  Choix invalide.{RESET}")

    # 2. Marque
    print()
    print(f"{BOLD}[2/7] Marque{RESET} {DIM}(pour détection mention dans les réponses){RESET}")
    brand = ""
    while not brand:
        brand = input(f"{DIM}Marque : {RESET}").strip()
        if not brand:
            print(f"{RED}  Obligatoire.{RESET}")

    # 3. Concurrents
    print()
    print(f"{BOLD}[3/7] Concurrents{RESET} {DIM}(séparés par virgule, optionnel){RESET}")
    competitors_raw = input(f"{DIM}Concurrents : {RESET}").strip()
    competitors = [c.strip() for c in competitors_raw.split(",") if c.strip()]

    # 4. Variables
    print()
    print(f"{BOLD}[4/7] Variables du persona{RESET}")
    variables = {}
    for var in persona.get("variables", []):
        val = input(f"  {CYAN}{var}{RESET} = ").strip()
        if val:
            variables[var] = val

    # 5. Providers
    print()
    print(f"{BOLD}[5/7] Providers{RESET}")
    available = []
    for p in ["openai", "anthropic", "perplexity", "gemini"]:
        if os.environ.get(MODELS[p]["env"]):
            print(f"  {GREEN}✓{RESET} {p} {DIM}(clé OK){RESET}")
            available.append(p)
        else:
            print(f"  {RED}✗{RESET} {p} {DIM}({MODELS[p]['env']} absente — skippé){RESET}")
    if not available:
        sys.exit(f"{RED}Aucune clé API. Renseignez au moins une variable d'env.{RESET}")
    default_str = ",".join(available)
    choice = input(f"{DIM}Liste (Enter = {default_str}) : {RESET}").strip()
    if choice:
        providers = [p.strip() for p in choice.split(",") if p.strip() in available]
        if not providers:
            providers = available
    else:
        providers = available

    # 6. Web search
    print()
    ws_choice = input(f"{BOLD}[6/7] Web search natif ?{RESET} {DIM}(sources réelles, ~+30% coût) [O/n] : {RESET}").strip().lower()
    web_search = ws_choice not in ("n", "no", "non")

    # 7. Limit
    print()
    nb_prompts = len(persona["prompts"])
    limit_raw = input(f"{BOLD}[7/7] Limit prompts{RESET} {DIM}(Enter = tous = {nb_prompts}) : {RESET}").strip()
    limit = None
    if limit_raw.isdigit():
        limit = max(1, min(int(limit_raw), nb_prompts))

    effective_count = limit or nb_prompts
    total_calls = effective_count * len(providers)
    # Coût indicatif (cents) : sans search ~0.5c/call, avec search ~1.5c/call
    cost_estimate = total_calls * (0.015 if web_search else 0.005)

    print()
    print(f"{BOLD}━━━ Récapitulatif ━━━{RESET}")
    print(f"  Persona       : {CYAN}{persona['id']}{RESET} ({effective_count} prompts)")
    print(f"  Marque        : {YELLOW}{brand}{RESET}")
    print(f"  Concurrents   : {', '.join(competitors) if competitors else DIM + '(aucun)' + RESET}")
    if variables:
        print(f"  Variables     : {', '.join(f'{k}={v}' for k,v in variables.items())}")
    print(f"  Providers     : {', '.join(providers)} ({len(providers)})")
    print(f"  Web search    : {GREEN if web_search else RED}{'ON' if web_search else 'OFF'}{RESET}")
    print(f"  Calls totaux  : {BOLD}{total_calls}{RESET}")
    print(f"  Coût estimé   : {BOLD}~{cost_estimate:.2f} €{RESET}")
    print()
    confirm = input(f"{BOLD}Lancer ? [O/n] : {RESET}").strip().lower()
    if confirm in ("n", "no", "non"):
        sys.exit("Abandonné.")

    return {
        "persona_id": persona["id"],
        "brand": brand,
        "competitors": competitors,
        "variables": variables,
        "providers": providers,
        "web_search": web_search,
        "limit": limit,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Probe les APIs LLM pour mesurer la visibilité IA d'une marque.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Mode wizard (recommandé) :\n"
            "  python probe-api.py --wizard\n\n"
            "Mode direct :\n"
            "  python probe-api.py --persona 01-cgp-courtier --brand 'Aeconomia' \\\n"
            "    --competitors 'Cafpi,Empruntis' --web-search \\\n"
            "    --variables '{\"VILLE\":\"Orléans\",\"ZONE\":\"Loiret\"}'\n"
        ),
    )
    parser.add_argument("--wizard", action="store_true", help="Mode interactif step-by-step (recommande pour debut)")
    parser.add_argument("--prompts", default=None, help="Chemin prompts.json (defaut: ../prompts/prompts.json)")
    parser.add_argument("--persona", default=None, help="ID persona (ex: 01-cgp-courtier) - requis sans --wizard")
    parser.add_argument("--brand", default=None, help="Votre marque (pour detection mention) - requis sans --wizard")
    parser.add_argument("--competitors", default="", help="Concurrents separes par virgule")
    parser.add_argument("--variables", default="{}", help="JSON inline override des variables")
    parser.add_argument("--models", default="openai,anthropic,perplexity,gemini", help="Liste providers (defaut: openai,anthropic,perplexity,gemini ; mistral disponible mais opt-in)")
    parser.add_argument("--out", default="./probe-report", help="Dossier de sortie")
    parser.add_argument("--csv-only", action="store_true", help="Ne produire que le CSV")
    parser.add_argument("--web-search", action="store_true", help="Active le web search NATIF sur chaque provider (OpenAI gpt-4o-mini-search-preview, Anthropic tool web_search, Gemini google_search, Perplexity natif). Sources reelles + verifiables. Cout legerement plus eleve.")
    parser.add_argument("--limit", type=int, default=None, help="Limite le nombre de prompts (defaut: tous). Utile pour test rapide ou budget restreint.")
    parser.add_argument("--dry-run", action="store_true", help="Affiche les prompts substitues sans appeler les APIs")

    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    prompts_path = Path(args.prompts) if args.prompts else script_dir.parent / "prompts" / "prompts.json"
    if not prompts_path.exists():
        sys.exit(f"Erreur : prompts.json introuvable : {prompts_path}")

    with open(prompts_path, encoding="utf-8") as f:
        data = json.load(f)

    personas = {p["id"]: p for p in data["personas"]}

    # Mode wizard : remplit les args manquants en interactif
    if args.wizard:
        wiz = wizard(data, prompts_path)
        args.persona = wiz["persona_id"]
        args.brand = wiz["brand"]
        args.competitors = ",".join(wiz["competitors"])
        args.variables = json.dumps(wiz["variables"])
        args.models = ",".join(wiz["providers"])
        args.web_search = wiz["web_search"]
        args.limit = wiz["limit"]

    # Validation post-wizard
    if not args.persona:
        sys.exit("Erreur : --persona requis (ou utiliser --wizard pour mode interactif).")
    if not args.brand:
        sys.exit("Erreur : --brand requis (ou utiliser --wizard pour mode interactif).")
    if args.persona not in personas:
        sys.exit(f"Erreur : persona '{args.persona}' inconnu. Disponibles : {', '.join(personas.keys())}")
    persona = personas[args.persona]
    if args.limit:
        persona = dict(persona)
        persona["prompts"] = persona["prompts"][:args.limit]

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

            # Liste (url, title) pour drill-down dans le HTML
            citations_pairs = [(u, titles.get(u, "")) for u in urls]
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
                "citations_pairs": citations_pairs,  # in-memory only, not in CSV
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
        # Domaines aggregés avec drill-down (URLs spécifiques + titres + prompt_id)
        domain_counts = {}
        domain_urls = {}  # {domain: [{url, title, prompt_id}]}
        for r in results_p:
            for url, title in r.get("citations_pairs", []):
                dom = domain_of(url, title)
                domain_counts[dom] = domain_counts.get(dom, 0) + 1
                if dom not in domain_urls:
                    domain_urls[dom] = []
                # Dédup par URL
                if not any(u["url"] == url for u in domain_urls[dom]):
                    domain_urls[dom].append({
                        "url": url,
                        "title": title or "",
                        "prompt_id": r["prompt_id"],
                    })
        # Top 20 sources avec leurs URLs détaillées
        sorted_sources = sorted(domain_counts.items(), key=lambda x: -x[1])[:20]
        source_detail = []
        for dom, count in sorted_sources:
            source_detail.append({
                "domain": dom,
                "count": count,
                "urls": domain_urls.get(dom, []),
            })
        by_provider[p] = {
            "total": len(results_p),
            "mentioned": len(mentioned),
            "errors": len(errors),
            "mention_rate": round(len(mentioned) / max(len(results_p), 1) * 100, 1),
            "model": results_p[0]["model"] if results_p else MODELS[p]["name"],
            "competitor_counts": sorted(comp_counts.items(), key=lambda x: -x[1]),
            "source_counts": sorted_sources,  # compat retro pour insights
            "source_detail": source_detail,
        }

    insights = generate_insights(by_provider, args.brand, args.web_search, competitors)

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
        insights=insights,
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML : {html_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
