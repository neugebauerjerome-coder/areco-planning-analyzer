# Route Engine V4.0.2

## Flux

1. Adresse texte.
2. Recherche dans le cache SQLite.
3. Géocodage OpenRouteService si absente.
4. Ordonnancement des sites par proximité.
5. Calcul routier segment par segment.
6. Somme des kilomètres et durées.

## Sécurité

La clé API n’est jamais stockée dans le code source.
Elle est fournie au lancement ou, dans les versions suivantes, via la configuration locale chiffrée.
