# `parse-logs.py` — Parser de logs Nginx pour bots IA

Lit un fichier `access.log` au format Nginx `combined`, identifie les hits des bots IA et SEO, produit un CSV brut + un rapport HTML autonome.

## Installation

```bash
cd scripts
pip install -r requirements.txt
```

Une seule dépendance : Jinja2 (le reste est dans la stdlib Python 3.9+).

## Quickstart

```bash
# Test sur le sample fourni
python parse-logs.py examples/access.log.sample --out ./report
open report/report.html

# Sur vos propres logs
python parse-logs.py /var/log/nginx/access.log --out ./report

# CSV uniquement (pas de HTML)
python parse-logs.py access.log --out ./report --csv-only
```

## Options

| Flag | Défaut | Description |
|---|---|---|
| `logfile` | — | Chemin vers le fichier access.log (positionnel, obligatoire) |
| `--out` / `-o` | `./report` | Dossier de sortie (créé s'il n'existe pas) |
| `--top-pages` | `20` | Top N pages affichées par bot dans le HTML |
| `--config` | `./config/bots.json` | Chemin custom vers le fichier de config bots |
| `--csv-only` | `false` | Saute la génération HTML, ne produit que `hits.csv` |

## Sortie

Dans le dossier `--out` :

- **`hits.csv`** — une ligne par hit bot, colonnes : `date, time, bot_id, bot_name, category, path, status, ip`. Importable Excel, Google Sheets, DuckDB, pandas.
- **`report.html`** — rapport autonome (sauf Chart.js CDN). Ouvrable hors ligne, partageable par mail / Slack.

## Format de log attendu

Format Nginx `combined` (défaut Nginx) :

```
$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
```

Exemple de ligne :

```
54.36.149.65 - - [25/May/2026:14:23:01 +0200] "GET /blog/article HTTP/1.1" 200 12345 "-" "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.0; +https://openai.com/gptbot)"
```

Sur d'autres formats (Apache, Cloudflare JSON), il faut convertir d'abord — voir [docs/setup-logs.md](../docs/setup-logs.md).

## Bots détectés

12 bots IA + 2 bots SEO classiques (Googlebot, Bingbot) pour comparaison. La liste complète est dans `config/bots.json`. Pour ajouter un bot, éditez ce fichier (pattern regex case-insensitive sur le User-Agent).

Bots IA inclus :
- **OpenAI** : GPTBot, OAI-SearchBot, ChatGPT-User
- **Anthropic** : ClaudeBot, anthropic-ai, Claude-Web
- **Perplexity** : PerplexityBot, Perplexity-User
- **Google AI** : Google-Extended, GoogleOther
- **Apple** : Applebot-Extended
- **Meta** : Meta-ExternalAgent, Meta-ExternalFetcher
- **ByteDance** : Bytespider
- **DeepSeek** : DeepSeekBot
- **Mistral** : MistralAI-User
- **You.com** : YouBot
- **Common Crawl** : CCBot

## Limites connues

- **Volume** : le script charge tout en mémoire. Au-delà de ~5 millions de lignes, prévoir un sharding (logrotate par jour, parser par jour).
- **Spoofing** : un IP peut prétendre être GPTBot via le User-Agent. Pour valider, croiser avec les plages IP officielles publiées par OpenAI, Anthropic, etc. — non implémenté ici (volontairement, pour rester offline-friendly).
- **Format** : Nginx combined uniquement. Apache combined fonctionne aussi (format identique). Pour Cloudflare Logpush (JSON), convertir d'abord avec `jq`.

## Aide à l'interprétation

Le rapport donne des chiffres. Voici ce qu'on en fait :

- **Ratio IA / SEO classique** > 1 : votre site est crawlé davantage par les bots IA que par Google/Bing. Signal fort en 2026.
- **Beaucoup de hits, peu de visites** : c'est normal. Anthropic affiche un ratio crawl/visite de 25 000 à 100 000:1. Le crawl ne se traduit pas mécaniquement en trafic.
- **GPTBot oui mais OAI-SearchBot absent** : votre `robots.txt` autorise probablement GPTBot mais pas OAI-SearchBot. Conséquence : vous êtes invisible dans ChatGPT Search alors que vous croyez être indexé.
- **Pages techniques en tête (`/wp-admin/`, `/feed/`)** : ces bots crawlent sans tri. C'est attendu. Filtrer par `/wp-admin/` exclu pour avoir les pages métier.
- **404 fréquents** : le bot tente des URLs inexistantes. Vérifier `robots.txt` et `sitemap.xml`.
