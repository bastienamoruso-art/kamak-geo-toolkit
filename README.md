# GEO Toolkit

> Outils open-source pour mesurer la visibilité d'une marque dans les LLM (ChatGPT, Claude, Perplexity, Gemini), en local, sans dashboard à 200 € par mois.
> Pensé pour **consultants SEO/GEO** qui auditent leurs clients et **marques** qui veulent s'auto-mesurer.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## La thèse

Ce que les outils GEO du marché vendent 50-200 € par mois est essentiellement une boucle `for prompt in prompts: openai.chat(...)`. Le problème n'est pas qu'ils existent. Le problème, c'est de payer 200 € pour un appel API et un peu d'UX.

Et même quand on accepte de payer, il y a une limite méthodologique : la réponse qu'un utilisateur réel reçoit ne passe jamais par un appel API brut. Elle passe par son historique de conversation, son abonnement, sa géolocalisation, le routing dynamique entre versions, ses préférences mémorisées.

Si vous voulez mesurer votre visibilité IA en 2026, vous avez **trois signaux complémentaires** :

1. **L'interface réelle** des assistants — testée manuellement. La plus fidèle à ce que voit un prospect.
2. **Vos logs serveurs** — la vérité brute de qui crawl quoi.
3. **L'API en local** — le plus rapide, ~2-5 € de tokens par run au lieu de 200 €/mois.

Ce toolkit vous donne les trois. À combiner, pas à substituer.

---

## Pour qui

- **Consultants SEO/GEO** qui veulent auditer la visibilité IA de leurs clients (input : nom du client + concurrents)
- **Marques** qui veulent s'auto-mesurer dans les LLM (input : leur propre nom + concurrents)
- **Marketers in-house** qui veulent monitorer mois après mois sans s'abonner à un outil tiers

Le tool est utilisé exactement de la même façon dans les trois cas.

---

## Ce qu'il y a dedans

### 1. `prompts/` — Template de prompts par persona · *le plus fidèle*

8 personas types (CGP/courtier, constructeur/immo, e-commerce, SaaS B2B, agence locale, freelance/cabinet, média/blog, marketplace), chacun avec 12 à 15 prompts stratégiques à tester **manuellement** dans ChatGPT, Perplexity, Claude et Gemini.

Une grille de suivi mensuel pour comparer dans le temps. Compte 30 minutes par mois et par persona pour avoir une mesure exploitable. C'est ce qui se rapproche le plus de ce que voit un prospect.

→ [Lire la méthode](./prompts/README.md)

### 2. `scripts/parse-logs.py` — Parser de logs serveur · *la vérité brute*

Un script Python qui parse vos logs Nginx (format `combined`) et produit un rapport HTML + CSV avec :

- Volume de crawl par bot IA (GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, PerplexityBot, Google-Extended, etc. — 12+ user-agents)
- Pages les plus crawlées par bot
- Distribution temporelle du crawl
- Comparatif crawl IA vs crawl SEO classique

Aucune dépendance lourde. Python 3.9+ et Jinja2.

→ [Lire la doc](./scripts/README.md#parse-logspy)
→ [Comment exporter vos logs (o2switch, Nginx, Cloudflare)](./docs/setup-logs.md)

### 3. `scripts/probe-api.py` — Probe des APIs LLM en local · *le plus rapide*

Le 3e outil. C'est exactement ce que vendent les outils GEO du marché, mais en local, sans abonnement, transparent. Vous fournissez vos clés API, le script tape OpenAI, Anthropic, Perplexity et Gemini sur les 12-15 prompts du persona choisi, et produit un rapport :

- **Taux de mention** de la marque par provider
- **Concurrents cités** par chaque modèle
- **Sources web réelles** (URLs vérifiables avec `--web-search` natif)
- **Plan d'action auto-généré** : sites à viser, concurrents leaders, gaps
- **Drill-down** : cliquer un domaine montre les URLs exactes + titres + prompt qui les a déclenchées

Coût : **~2-5 € de tokens par run complet**. Avec le mode `--web-search`, les citations sont vérifiables (vraies URLs) — c'est exactement ce que produit l'interface réelle quand l'utilisateur active "Search the web".

→ [Lire la doc](./scripts/README.md#probe-apipy)

---

## Quickstart 5 minutes

```bash
git clone https://github.com/bastienamoruso-art/kamak-geo-toolkit.git
cd kamak-geo-toolkit/scripts
pip install -r requirements.txt

# Outil 2 : parser logs sur le sample fourni
python parse-logs.py examples/access.log.sample --out ./report
open report/report.html

# Outil 3 : probe API en mode wizard (recommandé pour débuter)
cp .env.example .env
# Éditer .env avec vos clés OpenAI / Anthropic / Perplexity / Gemini
set -a; source .env; set +a
python probe-api.py --wizard
```

Le wizard vous guide en 7 étapes (persona, marque, concurrents, variables, providers, web search, limit) puis vous récapitule le coût avant de lancer.

---

## Méthodologie

### Test manuel vs API : pourquoi les deux

L'API LLM ne reproduit pas l'interface réelle utilisateur :

- Pas d'historique de conversation
- Pas d'abonnement (utilisateur Plus vs gratuit)
- Pas de géolocalisation
- Pas de routing dynamique entre versions du modèle
- Pas de mémoire / personnalisation utilisateur

**L'API donne la tendance et permet la scale.** Le test manuel reste la référence pour la vérité prospect. Les deux sont complémentaires, pas substituables.

### Mode `--web-search` (recommandé)

Active le web search natif de chaque provider :

| Provider | Mode search natif |
|---|---|
| OpenAI | `gpt-4o-mini-search-preview` avec `web_search_options` |
| Anthropic | Tool `web_search_20250305` (citations structurées) |
| Perplexity | Sonar — toujours en mode search natif |
| Gemini | Tool `google_search` (groundingMetadata) |

Les citations retournées sont **vraies URLs vérifiables**, pas hallucinées.

### Variance et tendance

Les réponses LLM ne sont pas déterministes. Refaire tourner le même prompt peut donner un résultat légèrement différent. Comptez sur la **tendance** sur plusieurs runs / plusieurs mois, pas sur une mesure unique.

---

## Limites connues

- **API ≠ interface réelle** — voir Méthodologie ci-dessus.
- **Coût variable** — selon les providers actifs et le mode (search ou non), comptez ~0,50 à 1 € par persona par run.
- **Perplexity** — l'API exige un crédit initial de 50 $ pour activer le compte. Si pas dispo, lancer avec `--models openai,anthropic,gemini`.
- **Volume** — `parse-logs.py` charge tout en mémoire. Au-delà de ~5 M lignes, sharder par jour.

---

## Licence et contribution

MIT. Réutilisable librement, y compris en commercial.

Contributions bienvenues — issue ou PR sur [github.com/bastienamoruso-art/kamak-geo-toolkit](https://github.com/bastienamoruso-art/kamak-geo-toolkit).

Maintenu par [Bastien Amoruso](https://kamak.ai) — newsletter mensuelle sur le SEO × IA : [kamak_.substack.com](https://bastienamoruso.substack.com).
