
# ARECO Planning Analyzer V3 — application web

Application Streamlit interne pour :

1. déposer un export Excel ARFITEC ;
2. calculer les distances et temps de trajet avec OpenRouteService ;
3. appliquer les règles ARECO V3 ;
4. télécharger un rapport Excel complet et le mail d’accompagnement.

## Installation sous Windows

1. Installer Python 3.11 ou 3.12.
2. Décompresser le dossier.
3. Double-cliquer sur `installer_windows.bat`.
4. Double-cliquer sur `lancer_areco.bat`.
5. Le navigateur ouvre l’application.

## Utilisation

- Saisir la **Basic Key OpenRouteService** dans la barre latérale.
- Déposer le fichier `Commandes service ARFITEC.xlsx`.
- Le référentiel équipes ARECO est déjà intégré.
- Cliquer sur **Analyser le planning**.
- Télécharger le classeur V3.

## Sécurité de la clé

La clé saisie dans l’application n’est pas écrite dans le fichier Excel.
Pour éviter de la saisir à chaque lancement, créez un fichier `.env` à partir de `.env.example`
ou définissez la variable système `ORS_API_KEY`.

## Partage sur le réseau ARECO

### Option simple
Lancer l’application sur un PC et utiliser :

```bat
streamlit run app.py --server.address 0.0.0.0
```

Les collègues du même réseau peuvent ouvrir :

```text
http://ADRESSE-IP-DU-PC:8501
```

### Option serveur
Déployer le dossier sur un serveur Windows, Linux, Azure App Service, Render ou Streamlit Community Cloud.

## Règles intégrées

- NAP : BWI, CLS, DKA, HMO, JLN, RMO, SEL.
- Grands itinérants : CGU, CLS, HMO, JCO, JFR, JLN, JSA, PCO, TDO, TDU.
- Bureau seul : 8 h.
- Bureau avec interventions : 2 h + autres interventions.
- HMY : 2 h.
- Zummo : 2 h.
- Contronics : numéro client commençant par B.
- JSA : Paris intramuros interdit.
- GGR et DME exclus.

## Limite importante

Lorsqu’aucune heure d’intervention n’est fournie dans l’export, l’application ordonne les sites par proximité
ou conserve l’ordre du fichier selon le paramètre choisi. Le trajet routier lui-même est calculé par OpenRouteService.
