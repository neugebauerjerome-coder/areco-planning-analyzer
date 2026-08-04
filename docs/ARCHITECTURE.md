# Architecture V4.0.1

Le Core Engine est volontairement indépendant de l’interface utilisateur.

- `arfitec_reader.py` : lecture et correspondance des colonnes.
- `technicians.py` : référentiel techniciens.
- `rules_engine.py` : règles métier et enrichissement.
- `validator.py` : contrôles structurels.
- `service.py` : orchestration du moteur.
- `cli.py` : exécution en ligne de commande.

La V4.0.2 ajoutera `route_engine/` sans modifier les contrats du Core Engine.
