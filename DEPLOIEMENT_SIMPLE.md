# Déploiement simple — ARECO Planning Analyzer V3

## Méthode la plus simple : Streamlit Community Cloud

1. Créez un dépôt GitHub nommé `areco-planning-analyzer-v3`.
2. Déposez tous les fichiers de ce dossier dans le dépôt.
3. Ouvrez Streamlit Community Cloud.
4. Cliquez sur **New app**.
5. Sélectionnez le dépôt GitHub.
6. Fichier principal : `app.py`.
7. Dans **Advanced settings → Secrets**, ajoutez :

```toml
ORS_API_KEY = "VOTRE_CLE_OPENROUTESERVICE"
```

8. Cliquez sur **Deploy**.

Vous obtenez un lien public du type :

```text
https://areco-planning-analyzer-v3.streamlit.app
```

Le SAV peut ensuite ouvrir ce lien, déposer l’Excel et télécharger le rapport V3.

## Important

- Ne publiez jamais votre clé API dans GitHub.
- La clé doit être placée uniquement dans les secrets Streamlit.
- Pour un usage interne ARECO, limitez le partage du lien aux personnes autorisées.
