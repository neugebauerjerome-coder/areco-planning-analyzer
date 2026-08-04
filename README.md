# ARECO Planning Suite Online V5.1.0

Évolution de l’application web :

- tableau de bord détaillé ;
- onglets Synthèse, Techniciens, Trajets, Alertes et Rapports ;
- filtres par statut, technicien et priorité ;
- graphique de charge par technicien ;
- mise à jour de LAL : Almeida-Martins Lucas, 09200 Saint-Girons ;
- rapports Excel, PDF et mail ;
- calcul OpenRouteService.

## Déploiement

Main file : `app.py`

Secret Streamlit :

```toml
ORS_API_KEY = "VOTRE_CLE_OPENROUTESERVICE"
```
