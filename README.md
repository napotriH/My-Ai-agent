# Reddit Clone - Proiect Python cu Streamlit

Un clone simplu al Reddit-ului construit cu Python și Streamlit, care include toate funcționalitățile de bază ale unei platforme sociale.

## 🚀 Funcționalități

- **Autentificare**: Înregistrare și login pentru utilizatori
- **Feed principal**: Vizualizarea postărilor din toate comunitățile
- **Comunități**: Crearea și explorarea comunităților
- **Postări**: Suport pentru postări text, link-uri și imagini
- **Comentarii**: Sistem de comentarii tip thread cu răspunsuri
- **Profil utilizator**: Gestionarea profilului personal
- **Mesagerie privată**: Trimiterea de mesaje între utilizatori
- **Sistem de voturi**: Upvote/downvote pentru postări și comentarii

## 📁 Structura proiectului

```
REDDIT PY/
├── app.py              # Aplicația principală Streamlit
├── database.py         # Modelele și gestionarea bazei de date
├── requirements.txt    # Dependențele Python
└── README.md          # Documentația proiectului
```

## 🛠️ Instalare și rulare

### 1. Clonează repository-ul
```bash
git clone <url-repository>
cd "REDDIT PY"
```

### 2. Instalează dependențele
```bash
pip install -r requirements.txt
```

### 3. Rulează aplicația
```bash
streamlit run app.py
```

### 4. Accesează aplicația
Deschide browser-ul la adresa: `http://localhost:8501`

## 🌐 Deploy pe Streamlit Cloud

1. Încarcă proiectul pe GitHub
2. Conectează-te la [Streamlit Cloud](https://streamlit.io/cloud)
3. Selectează repository-ul și fișierul `app.py`
4. Deploy-ul se va face automat

## 💾 Baza de date

Proiectul folosește SQLite pentru stocarea datelor, cu următoarele tabele:

- **users**: Informații utilizatori
- **communities**: Comunitățile create
- **posts**: Postările utilizatorilor
- **comments**: Comentariile la postări
- **messages**: Mesajele private
- **community_members**: Relația utilizatori-comunități

## 🔧 Tehnologii folosite

- **Python 3.8+**
- **Streamlit**: Framework pentru interfața web
- **SQLite**: Baza de date
- **UUID**: Generarea ID-urilor unice
- **Hashlib**: Criptarea parolelor

## 📝 Cum să contribui

1. Fork repository-ul
2. Creează o ramură pentru feature-ul tău
3. Commit modificările
4. Push pe ramura ta
5. Creează un Pull Request

## 🐛 Probleme cunoscute

- Sistemul de voturi nu este încă implementat complet
- Upload-ul de imagini necesită configurare suplimentară
- Căutarea în mesaje private nu este implementată

## 📄 Licență

Acest proiect este open source și disponibil sub licența MIT.