# GEO Toolkit — mesurer honnêtement votre visibilité IA

> Trois outils gratuits open-source pour mesurer ce que vous valez vraiment dans ChatGPT, Perplexity, Claude, Gemini et Mistral.
> Pas un dashboard à 200 € par mois. Vos logs réels, l'interface réelle des assistants, et — pour les pressés — un appel API en local pour quelques euros de tokens.

---

## La thèse

Ce que les outils GEO du marché vendent 50-200 € par mois est essentiellement une boucle `for prompt in prompts: openai.chat(...)`. Le problème n'est pas qu'ils existent. Le problème c'est de payer 200 € pour un appel API et un peu d'UX.

Et même quand on accepte de payer, il y a une limite méthodologique : la réponse qu'un utilisateur réel reçoit ne passe jamais par un appel API brut. Elle passe par son historique de conversation, son abonnement, sa géolocalisation, le routing dynamique entre versions, ses préférences mémorisées. L'API interroge un modèle dépouillé.

Si vous voulez mesurer votre visibilité IA en 2026, vous avez **trois signaux complémentaires** :

1. **L'interface réelle** des assistants — testée manuellement. La plus fidèle à ce que voit un prospect.
2. **Vos logs serveurs** — la vérité brute de qui crawl quoi.
3. **L'API en local** — le plus rapide, le moins fidèle, mais ~2-5 € de tokens par run au lieu de 200 €/mois.

Ce toolkit vous donne les trois. À combiner, pas à substituer.

---

## Ce qu'il y a dedans

### 1. `prompts/` — Template de prompts par persona · *le plus fidèle*

8 personas types (CGP, constructeur, e-commerce, SaaS B2B, agence locale, freelance, média, marketplace), chacun avec 12 à 15 prompts stratégiques à tester **manuellement** dans ChatGPT, Perplexity, Claude et Gemini.

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

Le 3e outil. C'est exactement ce que vendent les outils GEO du marché, mais en local, sans abonnement, transparent. Vous fournissez vos clés API, le script tape OpenAI (`gpt-4o-mini`), Anthropic (`claude-sonnet-4-5`), Perplexity (`sonar`) et Mistral (`mistral-large-latest`) sur les 12-15 prompts du persona choisi, et produit un rapport :

- Mention de votre marque par provider (taux %)
- Concurrents cités par provider
- Sources citées (URLs) — Perplexity expose un champ structuré
- Position de la mention dans la réponse (intro / corps / fin)

Coût : **~2-5 € de tokens par run complet** (8 personas × 15 prompts × 4 modèles = 480 appels).

À utiliser **en complément** des deux autres, pas en substitution. L'API n'est pas l'interface réelle — pas d'historique, pas d'abonnement, pas de géolocalisation, pas de routing dynamique. Pour la tendance et la scale, pas pour la vérité prospect.

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

# Outil 3 : probe API (configurer les clés d'abord)
cp .env.example .env
# Éditez .env, puis :
set -a; source .env; set +a
python probe-api.py --persona 01-cgp-courtier --brand "VotreMarque" \
  --variables '{"VILLE":"Paris","ZONE":"Île-de-France"}' --dry-run
```

---

## Auteur

Bastien Amoruso — consultant SEO × IA chez [KAMAK](https://kamak.ai).

Newsletter mensuelle (analyses SEO + IA) : [kamak_.substack.com](https://kamak_.substack.com).

Si ce toolkit vous est utile, le meilleur retour, c'est de [vous abonner à la newsletter](https://kamak.ai/geo-toolkit) — c'est là que je publie les évolutions de la méthode.

---

## Licence

MIT. Réutilisable librement, y compris en commercial.
