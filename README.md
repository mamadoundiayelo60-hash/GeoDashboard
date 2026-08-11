# 🗺️ GeoDashboard

**GeoDashboard** est une application SIG interactive développée en Python permettant d'importer, visualiser et analyser des données géographiques directement depuis une interface web.

L'application permet notamment de réaliser des analyses spatiales, d'étudier la couverture territoriale d'équipements et de générer automatiquement des résultats cartographiques et des rapports PDF.

---

## 🎯 Objectif du projet

GeoDashboard a été conçu pour simplifier certaines opérations courantes d'analyse territoriale sans nécessiter l'utilisation directe d'un logiciel SIG desktop.

L'utilisateur peut sélectionner un territoire, importer ses propres données géographiques, effectuer différentes analyses spatiales et visualiser immédiatement les résultats sur une carte interactive.

---

## ✨ Fonctionnalités principales

### 🗺️ Gestion du territoire

- Sélection d'une commune
- Affichage automatique de la limite communale
- Calcul de la superficie du territoire
- Création d'un territoire d'analyse

### 📂 Import de données SIG

L'application permet d'importer plusieurs formats géographiques :

- GeoPackage (`.gpkg`)
- GeoJSON (`.geojson`)
- JSON
- Shapefile compressé (`.zip`)
- KML
- CSV géographique

Les couches importées sont automatiquement ajoutées au projet et peuvent être affichées sur la carte.

### 🌍 Cartographie interactive

La carte interactive permet :

- d'afficher plusieurs couches simultanément ;
- d'activer ou désactiver les couches ;
- de naviguer et zoomer sur le territoire ;
- d'afficher les équipements ponctuels ;
- de visualiser les résultats des analyses spatiales ;
- de changer de fond cartographique.

Plusieurs fonds de carte sont disponibles, notamment OpenStreetMap, CartoDB et OpenTopoMap.

---

## 📐 Analyses spatiales

GeoDashboard intègre plusieurs opérations géographiques.

### Buffer

Création d'une zone tampon autour des entités d'une couche selon une distance définie par l'utilisateur.

Exemple :

```text
Écoles → Buffer 500 m
```

### Intersection

Calcul de l'intersection entre différentes couches géographiques.

### Sélection spatiale

Sélection d'entités selon leur relation spatiale avec une autre couche.

### Jointure spatiale

Association d'informations entre plusieurs couches selon leur position géographique.

### Union

Combinaison de plusieurs géométries afin de produire une nouvelle couche d'analyse.

---

## 📊 Analyse de couverture territoriale

L'une des fonctionnalités principales de GeoDashboard est l'analyse de couverture d'un territoire.

Par exemple, pour étudier l'accessibilité aux écoles à une distance de **500 mètres**, l'application peut calculer automatiquement :

- la superficie totale du territoire ;
- la superficie couverte ;
- la superficie non couverte ;
- le taux de couverture.

Le principe est :

```text
Équipements
      ↓
Buffer
      ↓
Intersection avec le territoire
      ↓
Zone couverte
      ↓
Zone non couverte
      ↓
Indicateurs territoriaux
```

Le taux de couverture est calculé selon :

```text
Taux de couverture =
Surface couverte / Surface totale du territoire × 100
```

---

## 📈 Résultats

Après une analyse, GeoDashboard présente automatiquement différents indicateurs :

- nombre d'entités sources ;
- nombre d'entités résultat ;
- distance utilisée ;
- surface totale du territoire ;
- surface couverte ;
- surface non couverte ;
- taux de couverture.

Les couches produites peuvent ensuite être visualisées directement sur la carte.

---

## 📄 Génération de rapport PDF

GeoDashboard peut générer automatiquement un rapport d'analyse contenant notamment :

- le territoire étudié ;
- les paramètres de l'analyse ;
- les principaux indicateurs ;
- les surfaces couvertes et non couvertes ;
- le taux de couverture ;
- une carte synthétique ;
- une interprétation automatique des résultats.

Cela permet de transformer directement une analyse SIG en document exploitable pour une étude territoriale.

---

## 💾 Export des résultats

Les résultats des analyses peuvent être exportés afin d'être réutilisés dans d'autres logiciels SIG.

Formats disponibles notamment :

- GeoPackage (`.gpkg`)
- GeoJSON (`.geojson`)
- PDF pour les rapports d'analyse

Les données exportées peuvent ensuite être utilisées dans QGIS ou dans d'autres outils compatibles avec les standards géographiques.

---

## 🛠️ Technologies utilisées

| Technologie | Utilisation |
|---|---|
| Python | Langage principal |
| Streamlit | Interface web |
| GeoPandas | Traitement des données géographiques |
| Shapely | Opérations géométriques |
| Folium | Cartographie interactive |
| Pandas | Manipulation des données |
| Matplotlib | Cartographie des rapports |
| ReportLab | Génération des rapports PDF |

---

## 🏗️ Architecture du projet

```text
GeoDashboard/
│
├── app.py
├── requirements.txt
├── README.md
│
├── components/
│   ├── analysis_panel.py
│   ├── attribute_table.py
│   ├── header.py
│   ├── import_panel.py
│   ├── layer_panel.py
│   ├── map_panel.py
│   └── results_panel.py
│
├── models/
│   └── layer.py
│
├── services/
│   ├── analysis/
│   ├── operations/
│   ├── layer_manager.py
│   ├── report_service.py
│   ├── selection_manager.py
│   └── territory_service.py
│
├── styles/
├── tests/
└── utils/
```

L'application repose sur une architecture modulaire séparant l'interface utilisateur, la gestion des couches et les traitements géographiques.

---

## 🚀 Installation

Cloner le dépôt :

```bash
git clone <URL_DU_DEPOT>
```

Entrer dans le projet :

```bash
cd GeoDashboard
```

Créer un environnement virtuel :

```bash
python -m venv .venv
```

Sous Windows PowerShell :

```powershell
.\.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

## ▶️ Lancer GeoDashboard

Une fois l'environnement virtuel activé :

```bash
streamlit run app.py
```

L'application s'ouvre ensuite dans le navigateur.

---

## 🧪 Exemple d'utilisation

Un scénario d'analyse peut être :

```text
1. Sélectionner la commune de Calais
2. Importer une couche d'équipements
3. Créer un buffer de 500 m
4. Calculer la couverture territoriale
5. Visualiser les zones couvertes et non couvertes
6. Consulter les indicateurs
7. Exporter les résultats
8. Générer le rapport PDF
```

---

## 📸 Aperçu

Une capture d'écran de l'application sera ajoutée ici.

```text
GeoDashboard
Territoire → Données → Analyse spatiale → Carte → Indicateurs → Rapport
```

---

## 🔮 Évolutions possibles

Plusieurs fonctionnalités pourront être ajoutées dans les prochaines versions :

- analyses multi-critères ;
- graphiques statistiques avancés ;
- comparaison entre plusieurs communes ;
- davantage d'indicateurs territoriaux ;
- amélioration de la personnalisation cartographique ;
- nouvelles opérations spatiales ;
- tableaux de bord thématiques.

---

## 👤 Auteur
**Mamadou Ndiaye LO**

Python Developer • GIS • Geomatics

GitHub :
https://github.com/mamadoundiayelo60-hash

Projet développé dans le cadre d'un travail autour de la **géomatique, de l'analyse spatiale et de la Data**.

---

## 📌 Version

**GeoDashboard v0.1.0**


---

# License

MIT License
