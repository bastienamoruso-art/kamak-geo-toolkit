# Persona 04 — SaaS B2B

## Profil
Vous vendez un logiciel en ligne à des entreprises (TPE, PME, ETI, grands comptes). CRM, automatisation marketing, outil RH, BI, helpdesk, etc. Le cycle de décision est long (semaines à mois), la décision implique plusieurs personnes, le comparatif est central dans le parcours d'achat.

Exemples de marques de cette catégorie : HubSpot, Pipedrive, Notion, Airtable, Salesforce, Zendesk, Slack.

## Variables à adapter
- `{CATEGORIE}` : votre catégorie outil (ex: CRM, automatisation marketing, outil de project management, plateforme RH).
- `{CIBLE}` : votre cible idéale (ex: PME 10-50 personnes, freelances, ETI 200+ salariés).
- `{USE_CASE}` : un cas d'usage emblématique (ex: gestion pipe commercial, onboarding RH, lifecycle email).
- `{ALTERNATIVE}` : un concurrent principal (ex: HubSpot, Salesforce, Notion).

## Prompts à tester dans ChatGPT, Perplexity, Claude, Gemini

### Découverte (questions génériques)
1. Quel est le meilleur {CATEGORIE} pour une {CIBLE} en 2026 ?
2. Quels sont les outils de {CATEGORIE} les plus utilisés par les {CIBLE} ?
3. Comment choisir un {CATEGORIE} pour mon entreprise ?
4. Quels {CATEGORIE} sont français ou européens et conformes RGPD ?

### Comparaison (vs concurrents et alternatives)
5. {ALTERNATIVE} ou {ALTERNATIVE_2} : que choisir pour une {CIBLE} en 2026 ?
6. {CATEGORIE} open-source ou solution SaaS payante : quel choix pour {USE_CASE} ?
7. Alternatives à {ALTERNATIVE} en 2026 ?

### Recommandation (mise en situation)
8. Je dirige une {CIBLE} et je cherche un {CATEGORIE} pour {USE_CASE}, que me conseillez-vous ?
9. Mon équipe utilise {ALTERNATIVE} mais on trouve ça trop cher, quelle alternative pour la même fonction ?
10. Je veux automatiser {USE_CASE} dans ma {CIBLE}, quel outil me recommandez-vous ?

### FAQ / objection
11. Un {CATEGORIE} à 50 €/mois et un à 500 €/mois : pourquoi cette différence et lequel choisir ?
12. Quels critères pour évaluer un {CATEGORIE} avant de signer ?
13. Combien de temps pour déployer un {CATEGORIE} dans une {CIBLE} ?

### Bonus actualité (à varier chaque trimestre)
14. Quels {CATEGORIE} intègrent nativement l'IA en 2026 et lesquels prennent du retard ?
15. RGPD + IA : quels {CATEGORIE} sont vraiment conformes en 2026 ?

## Ce qu'il faut noter dans la grille
| Colonne | À remplir |
|---|---|
| Marque citée | oui / non |
| Position citation | intro / corps / fin / liste / hors texte |
| Ton | favorable / neutre / défavorable |
| Concurrents cités | liste séparée virgule |
| Sources citées (liens) | URLs cliquables dans la réponse |
| Notes | particularités (G2, Capterra, comparison post) |

## Pièges spécifiques au secteur
- G2, Capterra, GetApp, TrustRadius sont les sources IA dominantes. Si votre outil n'y figure pas avec une fiche bien remplie + des avis récents, vous êtes invisible en IA même avec un excellent SEO classique.
- Les listicles "Top 10 [catégorie] 2026" écrits par des blogs B2B (Forbes Advisor, Zapier blog, HubSpot blog) sont massivement cités. Identifier ces sources et faire du outreach dessus est un levier direct.
- Les assistants citent volontiers les leaders américains et oublient les solutions européennes. Si vous êtes français/européen, ajoutez des prompts explicitement "français" ou "RGPD" pour mesurer ce gap.
