# rb-library

English
=======

rb-library is a small project for managing a PDF library used by the RecoveryBox Project.
It provides a simple web interface to browse documents and a Python script to update the library from PDF files stored in the repository.

## Features
- Browse PDFs from the main library and from a custom library.
- Filter by category, language, and type.
- Search by document name or filename.
- Automatically build links to the corresponding PDF files.

## Project structure
- index.html: web interface for browsing the library.
- library.json: main library metadata.
- custom-library.json: optional metadata for PDFs stored in the custom folder.
- update.py: interactive script to add new PDFs to the library.
- PDF/: main folder containing PDF documents.
- PDF/custom/: optional folder for custom documents.

## Usage

### Browse the library
Open index.html in a browser, or serve the project with a simple local server:

```bash
python3 -m http.server 8000
```

Then open http://127.0.0.1:8000/.

### Update the library
Run the update script from the project root:

```bash
python3 update.py
```

The script scans the PDF folders and asks for the document name, language, category, and type when a new PDF is found.
PDFs from the main folder are added to library.json, while PDFs in PDF/custom are added to custom-library.json.

## Notes
- The custom library file is optional. If it does not exist, the web interface simply loads the main library.
- The script creates a backup of the JSON file before updating it.

Français
========

rb-library est un petit projet de gestion d’une bibliothèque de PDF utilisée par le projet RecoveryBox.
Il propose une interface web simple pour parcourir les documents ainsi qu’un script Python pour mettre à jour la bibliothèque à partir des fichiers PDF présents dans le dépôt.

## Fonctionnalités
- Parcourir les PDFs de la bibliothèque principale et d’une bibliothèque personnalisée.
- Filtrer par catégorie, langue et type.
- Rechercher par nom de document ou nom de fichier.
- Construire automatiquement les liens vers les fichiers PDF correspondants.

## Structure du projet
- index.html : interface web pour parcourir la bibliothèque.
- library.json : métadonnées de la bibliothèque principale.
- custom-library.json : métadonnées optionnelles pour les PDFs stockés dans le dossier custom.
- update.py : script interactif pour ajouter de nouveaux PDFs à la bibliothèque.
- PDF/ : dossier principal contenant les documents PDF.
- PDF/custom/ : dossier optionnel pour les documents personnalisés.

## Utilisation

### Parcourir la bibliothèque
Ouvrez index.html dans un navigateur, ou servez le projet avec un serveur local simple :

```bash
python3 -m http.server 8000
```

Puis ouvrez http://127.0.0.1:8000/.

### Mettre à jour la bibliothèque
Exécutez le script de mise à jour depuis la racine du projet :

```bash
python3 update.py
```

Le script analyse les dossiers de PDF et demande le nom du document, la langue, la catégorie et le type lorsqu’un nouveau PDF est détecté.
Les PDFs du dossier principal sont ajoutés à library.json, tandis que les PDFs de PDF/custom sont ajoutés à custom-library.json.

## Notes
- Le fichier de bibliothèque custom est optionnel. S’il n’existe pas, l’interface web charge simplement la bibliothèque principale.
- Le script crée une sauvegarde du fichier JSON avant de le mettre à jour.
