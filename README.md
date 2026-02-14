# 🎵 Partition Generator

Génère des partitions musicales à partir de liens YouTube. Choisissez un instrument, et obtenez une partition PDF de qualité via LilyPond.

## Prérequis

- **Python 3.10+**
- **Node.js 18+**
- **FFmpeg** — `brew install ffmpeg`
- **LilyPond** — `brew install lilypond`

## Installation

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## Lancement

### Backend (port 5001)
> **Note** : Le port 5001 est utilisé pour éviter les conflits avec AirPlay sur macOS.

```bash
cd backend
source venv/bin/activate
python app.py
```

### Frontend (port 5173)
```bash
cd frontend
npm run dev
```

Ouvrir [http://localhost:5173](http://localhost:5173) dans le navigateur.
Le backend sera automatiquement contacté sur [http://localhost:5001](http://localhost:5001).

## Utilisation

1. Collez un lien YouTube
2. Sélectionnez un instrument (Piano, Guitare, Basse, Violon, Flûte, Voix)
3. Cliquez sur **Générer la partition**
4. Attendez le traitement (téléchargement → transcription → génération)
5. Téléchargez le PDF ou utilisez le mode écoute synchronisé
