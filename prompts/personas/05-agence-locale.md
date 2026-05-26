# Persona 05 — Artisan, restaurant, service local zone géo

## Profil
Vous êtes implanté physiquement sur une zone géographique précise. Plombier, électricien, garagiste, restaurant, salon de coiffure, cabinet médical, magasin de proximité. Vos prospects sont quasi exclusivement locaux, vos avis Google sont vitaux, le SEO local et le GBP sont votre fond de commerce.

Exemples de marques de cette catégorie : un restaurant à Lyon, un plombier à Orléans, une boulangerie à Tours.

## Variables à adapter
- `{METIER}` : votre activité (ex: plombier, restaurant italien, garagiste, opticien, cabinet dentaire).
- `{VILLE}` : votre ville principale.
- `{QUARTIER}` : quartier ou zone précise dans la ville (ex: centre-ville, La Source, Vieille Ville).
- `{SPECIALITE}` : votre angle (ex: dépannage 24/7, cuisine bio, restauration véhicule de collection).

## Prompts à tester dans ChatGPT, Perplexity, Claude, Gemini

### Découverte (questions génériques)
1. Quel est le meilleur {METIER} à {VILLE} en 2026 ?
2. Où trouver un {METIER} fiable à {VILLE} ?
3. Quels sont les {METIER} les mieux notés à {VILLE} ?
4. Y a-t-il un bon {METIER} dans le {QUARTIER} à {VILLE} ?

### Comparaison (vs concurrents et alternatives)
5. {METIER} indépendant ou chaîne nationale à {VILLE} : que choisir ?
6. {METIER} à {VILLE} ou dans une commune voisine : où aller pour {SPECIALITE} ?
7. Comment comparer plusieurs {METIER} à {VILLE} avant de choisir ?

### Recommandation (mise en situation)
8. Je viens d'arriver à {VILLE}, je cherche un {METIER}, lequel me recommandez-vous ?
9. J'ai besoin d'un {METIER} pour {SPECIALITE} dans le {QUARTIER}, qui contacter ?
10. Je cherche un {METIER} ouvert le {jour/horaire} à {VILLE}, vers qui me tourner ?

### FAQ / objection
11. Comment vérifier qu'un {METIER} à {VILLE} est sérieux avant de prendre rendez-vous ?
12. Quels tarifs pratiquent les {METIER} à {VILLE} en 2026 ?
13. Que faire si je suis mécontent d'un {METIER} à {VILLE} ?

### Bonus actualité (à varier chaque trimestre)
14. Nouveau {METIER} ouvert récemment à {VILLE} ?
15. {METIER} à {VILLE} : quels sont ceux qui acceptent les nouvelles cartes / paiements / services ?

## Ce qu'il faut noter dans la grille
| Colonne | À remplir |
|---|---|
| Marque citée | oui / non |
| Position citation | intro / corps / fin / liste / hors texte |
| Ton | favorable / neutre / défavorable |
| Concurrents cités | liste séparée virgule |
| Sources citées (liens) | URLs cliquables dans la réponse |
| Notes | mention Google Maps, mention nombre d'avis |

## Pièges spécifiques au secteur
- Pour le local, Google Maps et les avis Google sont les sources IA n°1. Si votre GBP n'est pas optimisée (catégorie principale, photos, avis récents, ARP), vous êtes invisible en IA même si votre site est bien référencé.
- Les assistants citent rarement des entreprises locales nominativement. Ils renvoient souvent à "consulter Google Maps". Notez ces redirections, elles signalent que la victoire se joue sur le GBP, pas dans la réponse IA.
- Tester avec le mode "géolocalisé" de Perplexity et Gemini (qui prennent en compte la localisation du device). Comparer avec ChatGPT qui ne se géolocalise pas (par défaut) pour mesurer le gap.
- Les prompts de longue traîne hyper-locale ("plombier rue X à {VILLE}") activent rarement les LLM. Restez sur des prompts ville/quartier.
