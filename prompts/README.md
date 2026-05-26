# Template de prompts par persona

8 personas types. 12 à 15 prompts par persona. Quatre assistants à tester : **ChatGPT, Perplexity, Claude, Gemini**.

Compte 30 minutes par persona et par mois. Vous obtenez ce qu'un outil GEO automatisé à 200 €/mois prétend mesurer, sauf que vous le mesurez sur l'interface réelle. Donc fidèle à ce qu'un prospect verra.

---

## Pourquoi cette méthode plutôt qu'une API

Un appel API n'est pas une requête utilisateur. La réponse qu'un utilisateur reçoit dépend de son historique, son abonnement, sa géolocalisation, le routing dynamique entre versions du modèle, ses préférences mémorisées. L'API interroge un modèle dépouillé.

Deux personnes différentes qui posent exactement la même question à ChatGPT obtiennent des réponses différentes, avec des sources citées différentes. Aucun outil GEO ne le voit.

Tester manuellement, dans l'interface réelle, depuis un compte standard, c'est ce qui s'approche le plus de la réalité d'un prospect.

---

## Comment utiliser ce template

### Préparation (5 min, une fois)

1. Identifiez votre persona dominant parmi les 8 fichiers. Ouvrez celui qui colle.
2. Adaptez les `{VARIABLES}` aux spécificités de votre marché (zone géo, ticket, type de produit). Les prompts sont écrits avec des placeholders pour rester adaptables.
3. Dupliquez `grille-tracking.csv` en local. Une ligne par prompt × assistant × mois.

### Test mensuel (30 min par persona)

1. Ouvrez chaque assistant **sans historique de conversation** (ChatGPT : "Nouvelle conversation" ou mode incognito recommandé). Désactivez les "Custom instructions" si vous voulez la vue prospect-froid.
2. Collez chaque prompt. Notez dans la grille :
   - Votre marque est-elle citée ? (oui / non)
   - À quelle position dans la réponse ? (intro / corps / fin / nulle part)
   - Quels concurrents sont cités ?
   - Quelles sources sont citées (liens) ?
   - Le ton de la mention est-il favorable, neutre, défavorable ?
3. Faites tourner sur les 4 assistants. ChatGPT (modèle par défaut), Perplexity (mode "Quick"), Claude (Sonnet par défaut), Gemini (modèle par défaut).

### Analyse trimestrielle

Comparez mois après mois. Cherchez les patterns :
- Sur quels prompts vous gagnez en présence ?
- Sur lesquels vous reculez ?
- Quels concurrents montent ?
- Quels nouveaux sites se font citer comme sources ?

Ce que vous mesurez : la **tendance**. Pas une valeur absolue. La variance entre deux exécutions du même prompt est réelle. La tendance, elle, est exploitable.

---

## Les 8 personas

| Fichier | Pour qui |
|---|---|
| [01-cgp-courtier.md](./personas/01-cgp-courtier.md) | CGP, courtier immo, courtier crédit, conseiller patrimoine |
| [02-constructeur-immo.md](./personas/02-constructeur-immo.md) | Constructeur de maisons, promoteur, agence immo neuve |
| [03-ecommerce-personnalise.md](./personas/03-ecommerce-personnalise.md) | E-commerce produit configurable (plaques, gravure, impression, sur-mesure) |
| [04-saas-b2b.md](./personas/04-saas-b2b.md) | SaaS B2B (outils, plateformes, software business) |
| [05-agence-locale.md](./personas/05-agence-locale.md) | Artisan, restaurant, service local zone géo |
| [06-freelance-cabinet.md](./personas/06-freelance-cabinet.md) | Freelance, indépendant, cabinet conseil, agence spécialisée |
| [07-media-blog.md](./personas/07-media-blog.md) | Média en ligne, blog éditorial, site d'autorité |
| [08-marketplace.md](./personas/08-marketplace.md) | Marketplace, plateforme mise en relation, comparateur |

---

## Export machine-readable

Tout est aussi disponible en JSON dans [`prompts.json`](./prompts.json) si vous voulez scripter votre propre suivi.

---

## Quelques règles d'or

- **Ne demandez jamais à un assistant IA si votre marque est citée.** Posez la question d'un utilisateur lambda. Si l'assistant cite spontanément votre marque dans une réponse à une question générique, c'est un signal. S'il faut la nommer pour qu'elle apparaisse, ce n'en est pas un.
- **Variez la formulation entre deux tests.** Un assistant peut citer une marque sur "courtier Orléans" et pas sur "meilleur courtier Orléans". Les deux comptent.
- **Notez les sources citées.** C'est aussi important que la mention de votre marque. Les sources citées sont les sites que l'IA considère comme autorité. Si vos concurrents y figurent et pas vous, c'est un chantier SEO classique.
- **Ne paniquez pas sur la variance d'un mois à l'autre.** Le routing dynamique entre versions peut faire bouger une réponse de 10-15 %. Regardez 3 mois.
