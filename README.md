# YNHALD Supplier Risk Bot – Railway Backend

FastAPI Backend für den Supplier Risk Assessment Bot.  
Speichert Assessments in PostgreSQL, generiert PDF-Reports und versendet E-Mails.

---

## 🏗 Lokale Entwicklung

```bash
# 1. Repository klonen / Ordner öffnen
cd supplier-risk-backend

# 2. Virtuelle Umgebung
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. .env anlegen
cp .env.example .env
# Dann DATABASE_URL und RESEND_API_KEY eintragen

# 5. Server starten
uvicorn main:app --reload --port 8000
```

API läuft auf: http://localhost:8000  
Docs: http://localhost:8000/docs

---

## 🚀 Railway Deployment (Schritt für Schritt)

### Schritt 1 – GitHub Repository anlegen

```bash
git init
git add .
git commit -m "Initial commit: YNHALD Supplier Risk Backend"
```

Dann auf GitHub ein neues Repository anlegen und pushen:
```bash
git remote add origin https://github.com/DEIN-USER/ynhald-risk-backend.git
git push -u origin main
```

### Schritt 2 – Railway Projekt erstellen

1. https://railway.app aufrufen → **New Project**
2. **Deploy from GitHub repo** wählen
3. Dein Repository auswählen → **Deploy Now**

Railway erkennt den `Dockerfile` automatisch.

### Schritt 3 – PostgreSQL Plugin hinzufügen

Im Railway-Dashboard:
1. **New** → **Database** → **Add PostgreSQL**
2. Auf das PostgreSQL-Plugin klicken → **Connect** tab
3. Die `DATABASE_URL` wird **automatisch** als Umgebungsvariable gesetzt ✅

### Schritt 4 – Umgebungsvariablen setzen

Im Railway-Dashboard → Dein Service → **Variables** tab:

| Variable | Wert | Beschreibung |
|----------|------|--------------|
| `RESEND_API_KEY` | `re_xxx...` | Von resend.com/api-keys |
| `FROM_EMAIL` | `reports@deine-domain.at` | Verifizierte Resend-Domain |
| `FROM_NAME` | `YNHALD Supplier Risk` | Absendername |
| `ALERT_EMAIL` | `azajic@sw-tech.net` | Wohin Sales-Alerts gehen |
| `ALLOWED_ORIGINS` | `*` | Oder deine Frontend-URL |

> **DATABASE_URL** wird von Railway **automatisch** gesetzt – nicht manuell eintragen!

### Schritt 5 – Resend einrichten

1. Konto anlegen: https://resend.com
2. **Domains** → Deine Domain verifizieren (DNS-Einträge setzen)
3. **API Keys** → Key erstellen → Als `RESEND_API_KEY` in Railway eintragen
4. Für erste Tests: `FROM_EMAIL=onboarding@resend.dev` (sendet nur an eigene Adresse)

### Schritt 6 – Deployment prüfen

Nach dem Deploy gibt Railway eine URL aus, z.B.:  
`https://ynhald-risk-backend-production.up.railway.app`

Health-Check:
```
GET https://ynhald-risk-backend-production.up.railway.app/health
```

API-Docs:
```
GET https://ynhald-risk-backend-production.up.railway.app/docs
```

---

## 🔗 Frontend verbinden

Im React-Frontend (`supplier_risk_bot.jsx`) die Railway-URL als API-Endpunkt einsetzen:

```javascript
const BACKEND_URL = "https://ynhald-risk-backend-production.up.railway.app";

// Im submitLead() nach der KI-Analyse:
const backendResponse = await fetch(`${BACKEND_URL}/api/assessment`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    lead: lead,
    industry: indV,
    industryLabel: ind.l,
    answers: answers,
    scores: computed,
    analysis: aiAnalysis,
  }),
});
```

---

## 📡 API Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| `GET` | `/health` | Health-Check |
| `POST` | `/api/assessment` | Assessment speichern + E-Mails senden |
| `GET` | `/api/assessment/{id}` | Assessment abrufen |
| `GET` | `/api/assessment/{id}/pdf` | PDF on-demand generieren |
| `GET` | `/api/assessments` | Alle Assessments auflisten |

### POST /api/assessment – Request Body

```json
{
  "lead": {
    "name": "Max Mustermann",
    "company": "Muster GmbH",
    "supplier": "Lieferant AG",
    "email": "max@firma.de",
    "phone": "+43 1 234 5678"
  },
  "industry": "manufacturing",
  "industryLabel": "Produktion / Industrie",
  "answers": {
    "Q1.1": "Ja",
    "Q1.2": "Nein",
    "Q1.3": "Teilweise"
  },
  "scores": {
    "ds": { "legal": 75, "cyber": 50, "operational": 80, "financial": 60 },
    "final": 67,
    "color": "yellow",
    "crits": [{"id": "Q1.2", "label": "Right-to-Audit"}],
    "top": [],
    "salesFlag": true
  },
  "analysis": {
    "exec": "Executive Summary Text...",
    "impact": "Geschäftsauswirkung Text...",
    "p1": {"title": "Priorität 1", "text": "Maßnahme 1"},
    "p2": {"title": "Priorität 2", "text": "Maßnahme 2"},
    "p3": {"title": "Priorität 3", "text": "Maßnahme 3"},
    "pkg": "Guided Remediation",
    "pkgWhy": "Begründung..."
  }
}
```

---

## 🗄 Datenbankstruktur

Tabelle `assessments`:

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `id` | UUID | Primärschlüssel |
| `company_name` | String | Kundenunternehmen |
| `supplier_name` | String | Bewerteter Lieferant |
| `industry` | String | Branchencode |
| `submitted_by` | String | Name des Einreichers |
| `email` | String | E-Mail des Leads |
| `timestamp` | DateTime | Zeitstempel |
| `answers` | JSON | Alle Fragebogen-Antworten |
| `dimension_scores` | JSON | Scores je Dimension |
| `final_score` | Float | Gesamtscore 0-100 |
| `color` | String | green/yellow/red |
| `sales_flag` | Boolean | Sales-Alert ausgelöst |
| `analysis` | JSON | KI-Analyse |
| `email_sent_lead` | Boolean | E-Mail an Lead gesendet |
| `email_sent_alert` | Boolean | Sales-Alert gesendet |
| `pdf_generated` | Boolean | PDF erstellt |

---

## 🔒 Sicherheit

- CORS ist konfigurierbar über `ALLOWED_ORIGINS`
- Keine API-Keys im Code – nur via Umgebungsvariablen
- PostgreSQL-Verbindung mit `pool_pre_ping` für Stabilität
- Alle personenbezogenen Daten in PostgreSQL (DSGVO-konform)

---

## 📦 Tech Stack

| Komponente | Technologie |
|-----------|-------------|
| Framework | FastAPI 0.115 |
| Server | Uvicorn |
| Datenbank | PostgreSQL (Railway Plugin) |
| ORM | SQLAlchemy 2.0 |
| PDF | fpdf2 |
| E-Mail | Resend API |
| Deployment | Railway (Docker) |
