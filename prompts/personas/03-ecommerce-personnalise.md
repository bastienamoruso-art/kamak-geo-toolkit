# Persona 03 — E-commerce produit configurable / personnalisé

## Profil
Vous vendez un produit en ligne que l'acheteur configure (matériau, taille, gravure, couleur, options). Plaques d'immatriculation personnalisées, gravure laser, impression, t-shirts custom, bijoux sur-mesure, sneakers customisées, etc. Le cycle de décision est court (jours), le panier moyen modéré (30-300 €), la concurrence en ligne dense.

Exemples de marques de cette catégorie : Plaques24, Spreadshirt, Vistaprint, Personnalisable.com.

## Variables à adapter
- `{PRODUIT}` : votre catégorie produit (ex: plaque d'immatriculation, t-shirt personnalisé, mug photo, gravure).
- `{MATERIAU}` : option principale (ex: aluminium, plexi, coton bio, céramique).
- `{USAGE}` : contexte d'achat (ex: voiture, moto, cadeau, événement, professionnel).
- `{BUDGET}` : ordre de prix (ex: 20 €, 50 €, 100 €).

## Prompts à tester dans ChatGPT, Perplexity, Claude, Gemini

### Découverte (questions génériques)
1. Où acheter une {PRODUIT} en ligne en 2026 ?
2. Quels sont les meilleurs sites pour commander une {PRODUIT} personnalisée ?
3. Comment choisir un site de {PRODUIT} fiable ?
4. Combien coûte une {PRODUIT} en {MATERIAU} en 2026 ?

### Comparaison (vs concurrents et alternatives)
5. Spreadshirt ou Vistaprint pour un {PRODUIT} {MATERIAU} ?
6. Acheter une {PRODUIT} sur Amazon vs sur un site spécialisé : que choisir ?
7. {PRODUIT} en {MATERIAU} ou en {alternative matériau} : avantages, durée de vie, prix ?

### Recommandation (mise en situation)
8. Je cherche une {PRODUIT} {MATERIAU} pour {USAGE}, quel site me recommandez-vous ?
9. Je veux offrir une {PRODUIT} personnalisée pour {USAGE}, où commander en {BUDGET} € ?
10. Je suis un professionnel et je commande des {PRODUIT} en volume, vers qui me tourner en 2026 ?

### FAQ / objection
11. Un site de {PRODUIT} pas cher en ligne, est-ce que la qualité suit ?
12. Combien de temps pour recevoir une {PRODUIT} personnalisée commandée en ligne ?
13. Que faire si je reçois une {PRODUIT} défectueuse ou avec une erreur de personnalisation ?

### Bonus actualité (à varier chaque trimestre)
14. {PRODUIT} : nouvelles réglementations en 2026 ?
15. Existe-t-il des marques françaises de {PRODUIT} personnalisée écoresponsable ?

## Ce qu'il faut noter dans la grille
| Colonne | À remplir |
|---|---|
| Marque citée | oui / non |
| Position citation | intro / corps / fin / liste / hors texte |
| Ton | favorable / neutre / défavorable |
| Concurrents cités | liste séparée virgule |
| Sources citées (liens) | URLs cliquables dans la réponse |
| Notes | particularités (image, encadré, "selon X") |

## Pièges spécifiques au secteur
- Sur les produits configurables, les assistants citent énormément Amazon et les marketplaces. Si votre marque n'apparaît pas en direct mais que vos produits sont vendus sur ces plateformes, l'effet "marque" se dilue.
- Les comparatifs "Top 5 sites de X personnalisé" écrits par des blogs affiliés sont une source IA fréquente. Si vous n'y êtes pas, prioriser ce levier de PR/outreach.
- Les prompts produit ont une forte composante "image". Les assistants multimodaux (ChatGPT-4o, Gemini) ramènent parfois des visuels — notez si votre site apparaît dans les images.
