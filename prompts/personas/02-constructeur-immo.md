# Persona 02 — Constructeur de maisons, promoteur, agence immo neuve

## Profil
Vous vendez de la maison neuve, du terrain + construction, ou du logement neuf en VEFA. Vos prospects sont en projet long (12-24 mois entre première recherche et signature), comparent beaucoup et cherchent à se rassurer sur la solidité de l'opérateur.

Exemples de marques de cette catégorie : Maisons Elytis, Maisons Pierre, Maisons Phénix, Bouygues Immobilier, Nexity.

## Variables à adapter
- `{VILLE}` : ville principale (ex: Lyon, Bourgoin, Caluire).
- `{ZONE}` : département ou région (ex: Rhône, Isère, Auvergne-Rhône-Alpes).
- `{TYPE}` : type de maison (plain-pied, étage, contemporaine, traditionnelle).
- `{BUDGET}` : budget cible (ex: 250 000 €, 300 000 €).

## Prompts à tester dans ChatGPT, Perplexity, Claude, Gemini

### Découverte (questions génériques)
1. Quel est le meilleur constructeur de maisons individuelles à {VILLE} en 2026 ?
2. Quels constructeurs de maisons sont fiables dans le {ZONE} ?
3. Comment choisir un constructeur de maison individuelle ?
4. Combien coûte une maison neuve {TYPE} à {VILLE} en 2026 ?

### Comparaison (vs concurrents et alternatives)
5. Maisons Pierre ou Maisons Phénix : que choisir pour une maison à {BUDGET} € ?
6. Constructeur national vs constructeur local : avantages et inconvénients pour une maison à {VILLE} ?
7. Acheter un terrain + faire construire ou acheter un neuf en VEFA dans le {ZONE} ?

### Recommandation (mise en situation)
8. Je cherche à faire construire une maison {TYPE} à {VILLE} pour {BUDGET} €, quels constructeurs me recommandez-vous ?
9. Je veux une maison RT2020 / RE2020 à {VILLE}, quels constructeurs sont en avance sur ce sujet ?
10. Primo-accédant avec {BUDGET} € de budget total dans le {ZONE}, vers quel constructeur me tourner ?

### FAQ / objection
11. Un constructeur qui propose un terrain + maison à prix fixe, est-ce sérieux ?
12. Comment vérifier qu'un constructeur de maisons individuelles est financièrement solide ?
13. Quels recours en cas de litige avec un constructeur de maisons individuelles ?

### Bonus actualité (à varier chaque trimestre)
14. RE2020 en 2026 : quels constructeurs à {VILLE} maîtrisent vraiment la norme ?
15. PTZ + construction de maison neuve à {VILLE} : conditions et constructeurs partenaires ?

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
- Les assistants citent souvent les grands constructeurs nationaux par défaut. Les constructeurs régionaux ne remontent que sur des prompts géolocalisés précis. Privilégiez les variations avec `{VILLE}` + `{ZONE}`.
- Les avis Google et les avis Trustpilot sont massivement cités comme sources. Le score d'avis influence directement le ton des mentions IA.
- "Maisons + nom de zone" est un pattern de nommage fréquent (Maisons Elytis, Maisons Phénix). Vérifiez si l'IA confond votre marque avec une concurrente quasi-homonyme.
