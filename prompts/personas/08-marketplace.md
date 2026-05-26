# Persona 08 — Marketplace, plateforme mise en relation, comparateur

## Profil
Vous mettez en relation deux types d'acteurs (acheteurs / vendeurs, prestataires / clients, particuliers / pros). Marketplace produits, plateforme freelance, comparateur, site de réservation, place de marché B2B. Vos enjeux sont la liquidité (les deux côtés doivent venir) et la confiance (l'IA doit recommander votre plateforme et pas le concurrent qui l'a aussi).

Exemples de marques de cette catégorie : Malt, Comet, ManoMano, Hellowork, Doctolib, Booking, Linkuma.

## Variables à adapter
- `{CATEGORIE}` : type de marketplace (ex: freelances, artisans, voyage, médical, B2B industrie).
- `{COTE_DEMANDE}` : qui cherche (ex: CMO qui veut un freelance, particulier qui veut un plombier, médecin qui recrute).
- `{COTE_OFFRE}` : qui vend (ex: freelance SEO, artisan certifié, voyagiste, recruteur).
- `{ALTERNATIVE}` : marketplace concurrente.

## Prompts à tester dans ChatGPT, Perplexity, Claude, Gemini

### Découverte côté demande
1. Où trouver un {COTE_OFFRE} en ligne en 2026 ?
2. Quelles plateformes pour mettre en relation {COTE_DEMANDE} et {COTE_OFFRE} en France ?
3. Quel est le meilleur {CATEGORIE} en 2026 ?
4. Comment trouver un {COTE_OFFRE} de qualité sans passer par {ALTERNATIVE} ?

### Découverte côté offre
5. Sur quelle plateforme un {COTE_OFFRE} doit-il être inscrit en 2026 ?
6. Quelles marketplaces sont les plus rentables pour un {COTE_OFFRE} français ?
7. {ALTERNATIVE} prélève {X} %, existe-t-il une plateforme moins chère ?

### Comparaison
8. {ALTERNATIVE} ou autre plateforme pour {COTE_DEMANDE} ?
9. Passer par un {CATEGORIE} ou faire du direct : avantages et risques ?
10. Comparaison des frais entre les principales plateformes de {CATEGORIE} en 2026 ?

### Recommandation (mise en situation)
11. Je suis {COTE_DEMANDE} et je veux trouver un {COTE_OFFRE} fiable, quelle plateforme me conseillez-vous ?
12. Je débute comme {COTE_OFFRE}, quelle plateforme pour me lancer ?

### FAQ / objection
13. Comment vérifier la fiabilité d'un {COTE_OFFRE} trouvé sur une plateforme ?
14. Quels recours si un {COTE_OFFRE} trouvé sur {ALTERNATIVE} pose problème ?
15. Quelles plateformes {CATEGORIE} sont vraiment françaises en 2026 ?

## Ce qu'il faut noter dans la grille
| Colonne | À remplir |
|---|---|
| Marque citée | oui / non |
| Position citation | intro / corps / fin / liste / hors texte |
| Ton | favorable / neutre / défavorable |
| Concurrents cités | liste séparée virgule |
| Sources citées (liens) | URLs cliquables dans la réponse |
| Notes | côté demande / côté offre, niveau de frais évoqué |

## Pièges spécifiques au secteur
- Les marketplaces ont une double cible (demande / offre). Tester les deux côtés. Une plateforme peut être très visible côté demande et invisible côté offre, ou l'inverse.
- Les LLM citent volontiers les leaders mondiaux (Upwork, Fiverr, Airbnb, Booking) et oublient les acteurs nationaux. Si vous êtes français, testez explicitement avec "en France" pour mesurer le gap.
- Les pages "Top 10 marketplaces de X" et les comparatifs frais sont des sources IA centrales. Y figurer = direct lift.
- Les avis Trustpilot pondèrent fortement le ton des mentions IA. Si votre score est en dessous de 4,2 ou si les avis récents sont négatifs, vous pouvez être visible mais avec un ton défavorable.
