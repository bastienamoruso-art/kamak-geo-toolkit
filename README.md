# GEO Toolkit — mesurer honnêtement votre visibilité IA

> Deux outils gratuits pour mesurer ce que vous valez vraiment dans ChatGPT, Perplexity, Claude et Gemini.
> Pas via une API qui simule, via vos logs réels et l'interface réelle des assistants.

---

## La thèse

La quasi-totalité des outils GEO du marché envoie des prompts depuis leur infrastructure via l'API d'OpenAI ou d'Anthropic. Ils enregistrent les sources citées. Ils agrègent. C'est techniquement honnête. Et c'est faux.

Parce que la réponse qu'un utilisateur réel reçoit ne passe jamais par un appel API brut. Elle passe par son historique de conversation, son abonnement, sa géolocalisation, le routing dynamique entre versions, ses préférences mémorisées. L'API interroge un modèle dépouillé.

Si vous voulez mesurer votre visibilité IA en 2026, vous avez deux signaux fiables :

1. **Vos logs serveurs** — la vérité brute de qui crawl quoi, à quelle fréquence, sur quelles pages.
2. **L'interface réelle** des assistants — testée manuellement, avec des prompts conçus par persona.

Ce toolkit vous donne les deux.

---

## Ce qu'il y a dedans

### 1. `prompts/` — Template de prompts par persona

8 personas types (CGP, constructeur, e-commerce, SaaS B2B, agence locale, freelance, média, marketplace), chacun avec 12 à 15 prompts stratégiques à tester dans ChatGPT, Perplexity, Claude et Gemini.

Une grille de suivi mensuel pour comparer dans le temps. Compte 30 minutes par mois et par persona pour avoir une mesure exploitable.

→ [Lire la méthode](./prompts/README.md)

### 2. `scripts/` — Parser de logs serveur

Un script Python qui parse vos logs Nginx (format `combined`) et produit un rapport HTML + CSV avec :

- Volume de crawl par bot IA (GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, PerplexityBot, Google-Extended, etc. — 12+ user-agents)
- Pages les plus crawlées par bot
- Distribution temporelle du crawl
- Comparatif crawl IA vs crawl SEO classique

Aucune dépendance lourde. Python 3.9+ et Jinja2 (`pip install jinja2`).

→ [Lire la doc du script](./scripts/README.md)
→ [Comment exporter vos logs (o2switch, Nginx, Cloudflare)](./docs/setup-logs.md)

---

## Quickstart 5 minutes

```bash
git clone https://github.com/bastienamoruso-art/kamak-geo-toolkit.git
cd kamak-geo-toolkit/scripts
pip install -r requirements.txt
python parse-logs.py examples/access.log.sample --out ./report
open report/report.html
```

Vous voyez à quoi ressemble le rapport. Remplacez le fichier d'exemple par vos propres logs et vous avez votre mesure.

---

## Auteur

Bastien Amoruso — consultant SEO × IA chez [KAMAK](https://kamak.ai).

Newsletter mensuelle (analyses SEO + IA) : [kamak_.substack.com](https://kamak_.substack.com).

Si ce toolkit vous est utile, le meilleur retour, c'est de [vous abonner à la newsletter](https://kamak.ai/geo-toolkit) — c'est là que je publie les évolutions de la méthode.

---

## Licence

MIT. Réutilisable librement, y compris en commercial.
