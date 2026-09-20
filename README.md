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
- PDF/custom/custom-library.json: optional metadata for PDFs stored in the custom folder.
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
./library-update.py
```

The script scans the PDF folders and asks for the document name, language, category, and type when a new PDF is found.
PDFs from the main folder are added to library.json, while PDFs in PDF/custom are added to PDF/custom/custom-library.json.

## Notes
- The custom library file is optional. If it does not exist, the web interface simply loads the main library.
- The script creates a backup of the JSON file before updating it.

## Web administration (optional)
A small Flask backend (`backend/`) lets a single system account index new PDFs from `PDF/custom` through `admin.html`, without CLI access.

- Only the system account whose **uid matches `RB_LIBRARY_ADMIN_UID`** (default `1000`) can log in; authentication is delegated to PAM, no separate password is stored.
- New entries and new tag values are only ever written to `PDF/custom/custom-library.json`; `library.json` stays read-only from the web.
- The virtualenv may live anywhere; its absolute path is set in the Apache template. The code and configuration remain in this project folder.
- One-time setup:
  ```bash
  cd /path/to/rb-library
  python3 -m venv /path/to/rb-library-venv
  /path/to/rb-library-venv/bin/pip install -r backend/requirements.txt
  cp backend/admin-config.example.json backend/admin-config.json
  # edit backend/admin-config.json: secret_key, filebrowser_enabled/url
  cp backend/apache-vhost-snippet.conf.example backend/apache-vhost-snippet.conf
  ```
  Complete all placeholders (`__RB_LIBRARY_DIR__`, `__VENV_DIR__`, `__ADMIN_USER__`, `__ADMIN_GROUP__`) in `backend/apache-vhost-snippet.conf` before adding its `Include` inside the existing vhost's `<VirtualHost>` block. The file is a template and must not be included unchanged. This requires `a2enmod wsgi` once for the host, shared by any Python-under-Apache app.
- The virtualenv must use the same Python major/minor version as `mod_wsgi` (for example Python 3.11 with a `mod_wsgi` compiled for Python 3.11). `python-home` points to the virtualenv root, not `bin/python`.
- `PDF/custom/` (which also holds `custom-library.json`) must belong to the account matching `RB_LIBRARY_ADMIN_UID` so the `mod_wsgi` daemon (running as that user) can write to it.

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
- PDF/custom/custom-library.json : métadonnées optionnelles pour les PDFs stockés dans le dossier custom.
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
./library-update.py
```

Le script analyse les dossiers de PDF et demande le nom du document, la langue, la catégorie et le type lorsqu’un nouveau PDF est détecté.
Les PDFs du dossier principal sont ajoutés à library.json, tandis que les PDFs de PDF/custom sont ajoutés à PDF/custom/custom-library.json.

## Notes
- Le fichier de bibliothèque custom est optionnel. S’il n’existe pas, l’interface web charge simplement la bibliothèque principale.
- Le script crée une sauvegarde du fichier JSON avant de le mettre à jour.

## Administration web (optionnel)
Un petit backend Flask (`backend/`) permet à un compte système unique d'indexer les nouveaux PDFs de `PDF/custom` depuis `admin.html`, sans passer par la CLI.

- Seul le compte système dont **l'uid correspond à `RB_LIBRARY_ADMIN_UID`** (défaut `1000`) peut se connecter ; l'authentification est déléguée à PAM, aucun mot de passe séparé n'est stocké.
- Les nouvelles entrées et nouvelles valeurs de tag ne sont écrites que dans `PDF/custom/custom-library.json` ; `library.json` reste en lecture seule depuis le web.
- Le venv peut être placé n'importe où ; son chemin absolu est renseigné dans le modèle Apache. La configuration et le code restent dans ce dossier de projet.
- Mise en place initiale :
  ```bash
  cd /chemin/vers/rb-library
  python3 -m venv /chemin/vers/mon-venv-rb-library
  /chemin/vers/mon-venv-rb-library/bin/pip install -r backend/requirements.txt
  cp backend/admin-config.example.json backend/admin-config.json
  # éditer backend/admin-config.json : secret_key, filebrowser_enabled/url
  cp backend/apache-vhost-snippet.conf.example backend/apache-vhost-snippet.conf
  ```
  Puis compléter tous les placeholders (`__RB_LIBRARY_DIR__`, `__VENV_DIR__`, `__ADMIN_USER__`, `__ADMIN_GROUP__`) dans `backend/apache-vhost-snippet.conf`, avant d'ajouter son `Include` dans le bloc `<VirtualHost>` existant. Le fichier est un modèle et ne doit pas être inclus tel quel. Cela nécessite `a2enmod wsgi` une fois pour l'hôte, partagé par toute appli Python sous Apache.
- Le venv doit utiliser la même version majeure/mineure de Python que `mod_wsgi` (par exemple Python 3.11 avec un `mod_wsgi` compilé pour Python 3.11). `python-home` pointe vers la racine du venv, pas vers `bin/python`.
- `PDF/custom/` (qui contient aussi `custom-library.json`) doit appartenir au compte correspondant à `RB_LIBRARY_ADMIN_UID` pour que le daemon `mod_wsgi` (qui tourne sous cet utilisateur) puisse y écrire.
