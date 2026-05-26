# `scripts/` — Deux scripts Python

| Script | Mesure | Coût | Vérité |
|---|---|---|---|
| [`parse-logs.py`](#parse-logspy) | Crawl bots IA sur votre site (logs serveur) | Gratuit | Vérité brute (qui crawl quoi) |
| [`probe-api.py`](#probe-apipy) | Mention de votre marque dans les APIs LLM | ~2-5 €/run complet | Approximation rapide (≠ interface réelle) |

> Les deux sont **complémentaires** du test manuel dans l'interface réelle (cf. [`../prompts/`](../prompts/)). Ce dernier reste le plus fidèle à ce qu'un prospect voit. Ces scripts sont là pour la scale et la tendance.

---

## Installation

```bash
cd scripts
pip install -r requirements.txt
```

Une seule dépendance : Jinja2 (le reste est dans la stdlib Python 3.9+).

Pour `probe-api.py`, copiez `.env.example` en `.env` et remplissez vos clés API (les 4 sont optionnelles, le script saute les providers sans clé) :

```bash
cp .env.example .env
# Éditez .env avec vos clés
source .env  # ou export OPENAI_API_KEY=... etc.
```

---

## `parse-logs.py`

Parser de logs Nginx pour identifier le crawl des bots IA.

### Quickstart

```bash
# Test sur le sample fourni
python parse-logs.py examples/access.log.sample --out ./report
open report/report.html

# Sur vos propres logs
python parse-logs.py /var/log/nginx/access.log --out ./report

# CSV uniquement (pas de HTML)
python parse-logs.py access.log --out ./report --csv-only
```

### Options

| Flag | Défaut | Description |
|---|---|---|
| `logfile` | — | Chemin vers le fichier access.log Nginx (positionnel, obligatoire) |
| `--out` / `-o` | `./report` | Dossier de sortie |
| `--top-pages` | `20` | Top N pages affichées par bot dans le HTML |
| `--config` | `./config/bots.json` | Chemin custom vers le fichier de config bots |
| `--csv-only` | `false` | Saute la génération HTML |

### Bots détectés

12 bots IA + 2 bots SEO classiques (Googlebot, Bingbot) pour comparaison. Liste complète dans `config/bots.json` — pour ajouter un bot, éditez ce JSON (pattern regex case-insensitive).

- **OpenAI** : GPTBot, OAI-SearchBot, ChatGPT-User
- **Anthropic** : ClaudeBot, anthropic-ai, Claude-Web
- **Perplexity** : PerplexityBot, Perplexity-User
- **Google AI** : Google-Extended, GoogleOther
- **Apple** : Applebot-Extended
- **Meta** : Meta-ExternalAgent, Meta-ExternalFetcher
- **ByteDance** : Bytespider · **DeepSeek** : DeepSeekBot · **Mistral** : MistralAI-User · **You.com** : YouBot · **Common Crawl** : CCBot

### Format de log

Format Nginx `combined` (défaut). Apache `combined` fonctionne aussi (format identique). Pour Cloudflare Logpush JSON, voir [`../docs/setup-logs.md`](../docs/setup-logs.md).

### Aide à l'interprétation

- **Ratio IA / SEO classique** > 1 : votre site est crawlé davantage par les bots IA que par Google/Bing. Signal fort en 2026.
- **Beaucoup de hits, peu de visites** : c'est normal. Anthropic affiche un ratio crawl/visite de 25 000 à 100 000:1.
- **GPTBot oui mais OAI-SearchBot absent** : votre `robots.txt` autorise probablement GPTBot mais pas OAI-SearchBot. Vous êtes invisible dans ChatGPT Search.
- **404 fréquents** : vérifier `robots.txt` et `sitemap.xml`.

---

## `probe-api.py`

Tape les APIs LLM en local pour mesurer la mention de votre marque sur un persona donné.

### Pourquoi en local plutôt qu'un outil GEO à 200 €/mois

Parce que ce que les outils GEO du marché vendent 50-200 €/mois est essentiellement une boucle `for prompt in prompts: openai.chat(...)`. En local, c'est ~2-5 € de tokens par run complet (8 personas × 15 prompts × 4 modèles = 480 appels).

**Limite à connaître** : l'API n'est PAS l'interface réelle. Pas d'historique utilisateur, pas d'abonnement, pas de géolocalisation, pas de routing dynamique entre versions du modèle. À utiliser pour la **tendance** et la **scale**, à croiser avec le test manuel pour la **vérité prospect**.

### Quickstart

```bash
# 1. Configurer les clés
cp .env.example .env
# Éditer .env, puis :
set -a; source .env; set +a

# 2. Dry-run pour voir les prompts substitués sans dépenser de tokens
python probe-api.py \
  --persona 01-cgp-courtier \
  --brand "Aeconomia" \
  --competitors "Cafpi,Empruntis,Meilleurtaux" \
  --variables '{"VILLE":"Orléans","ZONE":"Loiret","TICKET":"250 000 €","SPECIALITE":"primo-accédants"}' \
  --dry-run

# 3. Run complet
python probe-api.py \
  --persona 01-cgp-courtier \
  --brand "Aeconomia" \
  --competitors "Cafpi,Empruntis,Meilleurtaux" \
  --variables '{"VILLE":"Orléans","ZONE":"Loiret","TICKET":"250 000 €","SPECIALITE":"primo-accédants"}' \
  --out ./probe-report

open probe-report/probe-report.html
```

### Options

| Flag | Défaut | Description |
|---|---|---|
| `--persona` | — | ID persona (obligatoire — ex: `01-cgp-courtier`) |
| `--brand` | — | Votre marque (obligatoire — pour détection mention) |
| `--competitors` | `""` | Concurrents séparés par virgule |
| `--variables` | `{}` | JSON inline override des variables (`VILLE`, `ZONE`, etc.) |
| `--models` | `openai,anthropic,perplexity,mistral` | Liste providers à interroger |
| `--prompts` | `../prompts/prompts.json` | Chemin custom prompts.json |
| `--out` | `./probe-report` | Dossier de sortie |
| `--csv-only` | `false` | Saute la génération HTML |
| `--dry-run` | `false` | Affiche les prompts substitués sans appeler les APIs |

### Providers et modèles utilisés

| Provider | Modèle par défaut | Retrieval web ? |
|---|---|---|
| OpenAI | `gpt-4o-mini` | Non |
| Anthropic | `claude-sonnet-4-5` | Non |
| Perplexity | `sonar` | **Oui** (search temps réel) |
| Mistral | `mistral-large-latest` | Non |

Pour changer un modèle, éditez le dict `MODELS` en haut de `probe-api.py`. Pas de complication d'argparse — c'est volontaire pour rester lisible.

Les clés API non renseignées sont automatiquement skippées si vous limitez `--models` à ceux que vous avez.

### Détection mention et concurrents

Match regex case-insensitive sur le texte de réponse. Position calculée en proportion de la longueur du texte :
- **intro** : mention dans les 25 premiers %
- **corps** : 25-75 %
- **fin** : 75-100 %

Pour les sources citées, Perplexity expose un champ `citations` structuré. Pour les autres providers, regex sur les URLs présentes dans le texte de réponse.

### Coût estimé

Par run complet de 15 prompts sur les 4 providers (60 appels) :

| Provider | Coût indicatif |
|---|---|
| OpenAI gpt-4o-mini | ~0.02 € |
| Anthropic Sonnet | ~0.20 € |
| Perplexity sonar | ~0.30 € |
| Mistral Large | ~0.15 € |
| **Total** | **~0.70 € par persona** |

Soit ~5 € pour les 8 personas. À comparer aux 50-200 €/mois d'un outil GEO commercial.

### Aide à l'interprétation

- **Mention 0% partout** : votre marque n'est pas dans les corpus d'entraînement. Travailler la pression de marque (PR, citations, Wikipedia, mentions par tiers).
- **Mention forte sur Perplexity, faible sur OpenAI/Anthropic** : votre site est bien référencé en SEO classique (Perplexity fait du retrieval) mais peu cité comme autorité. Privilégier les sources que les LLM ont indexées (G2, Capterra, Reddit, Wikipedia, médias).
- **Mention forte OpenAI, faible ailleurs** : OpenAI a parsé du Common Crawl où votre site est bien représenté. Anthropic et Mistral n'utilisent pas exactement les mêmes corpus.
- **Position "fin"** : vous êtes cité en mention secondaire. Position "intro" = vous êtes la première réponse de l'assistant — l'idéal.

---

## Limites communes

- **Volume** : `parse-logs.py` charge tout en mémoire. Au-delà de ~5M lignes, prévoir un sharding (logrotate par jour, parser par jour).
- **Spoofing** : un IP peut prétendre être GPTBot via le User-Agent. Pour valider, croiser avec les plages IP officielles publiées par OpenAI, Anthropic, etc. — non implémenté ici (volontairement, pour rester offline-friendly).
- **Variance API** : les réponses LLM ne sont pas déterministes. Re-faire tourner `probe-api.py` à un autre moment peut donner des résultats différents. Comptez sur la **tendance** sur plusieurs runs, pas sur une mesure unique.
