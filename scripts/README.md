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
| `--models` | `openai,anthropic,perplexity,gemini` | Liste providers à interroger (Mistral disponible mais opt-in) |
| `--prompts` | `../prompts/prompts.json` | Chemin custom prompts.json |
| `--out` | `./probe-report` | Dossier de sortie |
| `--csv-only` | `false` | Saute la génération HTML |
| `--ask-sources` | `false` | **Ajoute un 2e appel par prompt** demandant les sources/sites que le modèle utilise (double le coût, mais ramène la liste actionnable des sites à viser pour entrer dans le corpus) |
| `--dry-run` | `false` | Affiche les prompts substitués sans appeler les APIs |

### À quoi sert `--ask-sources` (recommandé pour avoir un plan d'action)

Les modèles non-search (OpenAI, Anthropic, Gemini sans web tool) ne ramènent quasi jamais d'URLs explicites dans leurs réponses. Vous savez qu'un concurrent est cité, mais pas **par quelle source** le modèle puise cette info. Or, c'est précisément ce qu'il faut viser pour entrer dans leur prochain corpus d'entraînement.

Avec `--ask-sources`, le script enchaîne un 2e appel par prompt :

> *« Pour cette réponse, sur quels sites web, comparateurs, médias te bases-tu généralement ? Liste 5 sources concrètes avec URL si possible. »*

Les sources retournées (URLs, noms de domaines, noms de médias) sont extraites, agrégées par provider, et affichées dans le rapport HTML sous **« Sources citées »**. Vous obtenez votre **plan d'action SEO/PR** : les sites à cibler pour faire connaître votre marque aux modèles.

⚠️ Le modèle peut halluciner des URLs (forme correcte mais inexistantes). Les **noms de domaines courants** (`meilleurtaux.com`, `service-public.fr`) sont fiables ; les URLs profondes (`https://example.com/article-xyz`) sont à vérifier avant action.

### Providers et modèles utilisés

| Provider | Modèle par défaut | Retrieval web ? | Inclus par défaut |
|---|---|---|---|
| OpenAI | `gpt-4o-mini` | Non | ✅ |
| Anthropic | `claude-sonnet-4-5` | Non | ✅ |
| Perplexity | `sonar` | **Oui** (search temps réel) | ✅ |
| Gemini | `gemini-2.5-flash` | Non | ✅ |
| Mistral | `mistral-large-latest` | Non | ❌ (opt-in via `--models openai,...,mistral`) |

Le script **skippe automatiquement** les providers dont vous n'avez pas la clé API (warning au démarrage). Vous n'avez qu'OpenAI ? Le script tourne quand même, juste avec OpenAI.

Pour changer un modèle, éditez le dict `MODELS` en haut de `probe-api.py`. Pas de complication d'argparse — c'est volontaire pour rester lisible.

### Quel livrable selon l'interface

Tous les providers donnent **mention marque + concurrents + position**. Mais ce que vous obtenez en plus dépend du provider :

| Provider | Mention marque | Concurrents cités | Sources URL | Représente quelle interface ? |
|---|---|---|---|---|
| **OpenAI** `gpt-4o-mini` | ✅ | ✅ | ❌ | ChatGPT standard (modèle sans web) |
| **Anthropic** `claude-sonnet-4-5` | ✅ | ✅ | ❌ | Claude.ai standard (modèle sans web) |
| **Perplexity** `sonar` | ✅ | ✅ | ✅ **URLs réelles** | Perplexity.ai (search retrieval intégré) |
| **Gemini** `gemini-2.5-flash` | ✅ | ✅ | ❌ | Gemini standard (modèle sans web) |

**Conséquences pratiques** :

- **Sur OpenAI / Anthropic / Gemini** : vous mesurez la présence de votre marque dans le **corpus d'entraînement** du modèle. Si vous n'y êtes pas, vous êtes invisible sur l'interface standard de ces assistants (sauf si l'utilisateur active explicitement un mode web search côté UI, ce que l'API ne reproduit pas).
- **Sur Perplexity** : vous mesurez ce qu'**un utilisateur reçoit réellement** en posant la question — y compris les URLs des sources citées. C'est le plus proche de l'expérience prospect. Si vous avez du bon SEO mais pas de pression de marque, vous serez plus visible sur Perplexity que sur les 3 autres.
- **L'interface réelle ChatGPT/Claude/Gemini** active souvent du web search côté UI (selon abonnement, modèle, fonctionnalités). Pour mesurer ça, le script ne suffit pas — c'est ce que mesure le **test manuel** dans `prompts/`.

Le croisement des 4 providers vous donne :
- **Présence dans le corpus** (OpenAI + Anthropic + Gemini)
- **Présence en search web** (Perplexity)
- **Concurrents perçus par chaque modèle** (utile pour identifier qui mène la perception et qui est sous-représenté)

### Détection mention et concurrents

Match regex case-insensitive sur le texte de réponse. Position calculée en proportion de la longueur du texte :
- **intro** : mention dans les 25 premiers %
- **corps** : 25-75 %
- **fin** : 75-100 %

Pour les sources citées, Perplexity expose un champ `citations` structuré. Pour les autres providers, regex sur les URLs présentes dans le texte de réponse.

### Coût estimé

Par run complet de 15 prompts sur les 4 providers par défaut (60 appels) :

| Provider | Coût indicatif |
|---|---|
| OpenAI gpt-4o-mini | ~0.02 € |
| Anthropic Sonnet | ~0.20 € |
| Perplexity sonar | ~0.30 € (min 50 $ de crédit pour activer le compte) |
| Gemini 2.5 Flash | ~0.02 € (quota gratuit généreux sur AI Studio) |
| **Total** | **~0.55 € par persona** |

Soit ~4-5 € pour les 8 personas sur les 4 providers. À comparer aux 50-200 €/mois d'un outil GEO commercial.

**Note Perplexity** : leur API exige un crédit initial de 50 $ minimum pour activer le compte. Si vous n'avez pas ce budget, lancez avec `--models openai,anthropic,gemini` et complétez à la main sur l'interface Perplexity.ai (c'est ce qu'on appelle l'**Outil 1 — test manuel**, voir [`../prompts/`](../prompts/)).

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
