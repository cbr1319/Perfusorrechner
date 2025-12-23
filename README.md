# Perfusor-Rechner 13H3 (Notion-Embed)

## Lokal starten
```bash
pip install -r requirements.txt
streamlit run app.py
```

## In Notion einbetten
1) App hosten (z.B. Streamlit Community Cloud)
2) In Notion `/embed` → App-URL einfügen

## Streamlit Community Cloud (einfachste Variante)
1) GitHub Repo erstellen und diese Dateien hochladen: `app.py`, `requirements.txt`
2) Auf https://streamlit.io/cloud App deployen (Repo auswählen)
3) Du erhältst eine URL → in Notion einbetten

Hinweis: Die App speichert keine Daten; es werden nur Eingaben in der Session verarbeitet.
