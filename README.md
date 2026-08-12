# Airport Operations Data Pipeline

> Eine kompakte End-to-End-Data-Engineering-Pipeline zur Validierung, Bereinigung, Modellierung und Auswertung synthetischer Flughafenbetriebsdaten.

Die Pipeline nutzt **Python** und **pandas** für ETL-Prozesse, dokumentiert Datenqualitätsprobleme nachvollziehbar, erzeugt KPI-Auswertungen, bereitet ein Star Schema für **Power BI** auf und kann validierte Daten optional in **PostgreSQL** laden.

📌 **Hinweis:** Dieses Repository ist als reproduzierbares **Portfolio-Projekt** konzipiert und nicht als produktives Luftfahrtsystem. Sämtliche enthaltenen Flugdaten sind synthetisch.

---

## Problemstellung

Operative CSV-Daten sind in der Praxis selten direkt analysebereit. Fehlende Kennungen, ungültige Flughafencodes, doppelte Datensätze, inkonsistente Routen, fehlerhafte Zeitstempel oder ungültige Passagierzahlen können nachgelagerte Auswertungen verfälschen, wenn sie nicht bereits vor der Analyse erkannt und behandelt werden.

Dieses Projekt trennt deshalb **gültige** und **abgelehnte Datensätze**, dokumentiert die jeweilige Fehlerursache und erstellt aus den validierten Flugdaten strukturierte Reporting-Datensätze. Dadurch bleibt der gesamte Ablauf – von der Quelldatei bis zu den Dashboard-Daten – nachvollziehbar und reproduzierbar.

---

## Ziele des Projekts

- Eine klar strukturierte CSV-basierte ETL-Pipeline mit getrennten Modulen für **Extract**, **Transform**, **Load** und **Reporting** aufbauen.
- Explizite Datenqualitätsregeln anwenden, bevor Datensätze in Analyse- oder Reporting-Ausgaben gelangen.
- Abgelehnte Datensätze nicht stillschweigend verwerfen, sondern inklusive Fehlergrund nachvollziehbar dokumentieren.
- Operative KPI-Berichte für Airlines, Routen, Tages- und Monatsauswertungen sowie Management-Zusammenfassungen erzeugen.
- Ein übersichtliches Star Schema für Power BI bereitstellen.
- Optionales relationales Laden sowie SQL-Analysen mit PostgreSQL demonstrieren.
- Das Projekt lokal einfach ausführbar, testbar und reproduzierbar halten.

---

## 📊 Demo-Ergebnisse

Der im Repository enthaltene Demo-Datensatz wird deterministisch erzeugt und umfasst **800 synthetische Flugdatensätze über einen Zeitraum von sechs Monaten**.

| Kennzahl | Ergebnis |
|---|---:|
| Eingelesene Datensätze | 800 |
| Akzeptierte Datensätze | 728 |
| Abgelehnte Datensätze | 72 |
| Erkannte Datenqualitätsprobleme | 72 |
| Akzeptanzrate | 91,00 % |
| Passagiere in gültigen Flügen | 136.120 |
| Airlines | 8 |
| Routen | 12 |

Ein regulärer Pipeline-Lauf endet beispielsweise mit:

```text
Pipeline completed | extracted=800 | valid=728 | rejected=72 | issues=72
```

---

## Pipeline-Architektur

```text
Synthetische / eigene CSV-Eingabe
               |
               v
        Extract (pandas)
               |
               v
 Normalisieren + Validieren + Anreichern
               |
        +------+-------------------+
        |                          |
        v                          v
 Gültige Flugdaten          Abgelehnte Datensätze
        |                          |
        |                          v
        |                 Datenqualitätsprotokoll
        |
        +-----------+--------------+
                    |
          +---------+----------+----------------+
          |                    |                |
          v                    v                v
   KPI-/CSV-Reports      Power-BI-Tabellen   PostgreSQL
                                           (optional)
```

### ETL-Ablauf

1. **Extract** – `src/extract.py` liest eine nicht leere CSV-Datei in einen pandas DataFrame ein.
2. **Transform** – `src/transform.py` normalisiert Textwerte, validiert Pflichtfelder, lehnt ungültige Zeilen ab, berechnet Verspätungen, ordnet Delay-Kategorien zu und ergänzt Reporting-Felder.
3. **Quality Tracking** – Abgelehnte Datensätze werden in nachvollziehbare Quality-Issue-Einträge mit Regelcode, Qualitätsdimension, Schweregrad, Workflow-Status und Referenz auf die Quellzeile überführt.
4. **Load** – Bereinigte Daten, abgelehnte Datensätze, Quality Issues, KPI-Berichte und Power-BI-Tabellen werden als CSV-Dateien ausgegeben.
5. **Database Load (optional)** – Mit `--with-db` wird das PostgreSQL-Schema erstellt. Dimensionen und Flight Facts werden anschließend mit `psycopg` per Upsert geladen.
6. **Reporting** – Python erzeugt KPI-Auswertungen nach Airline, Route, Tag und Monat sowie Executive-, Quality- und Delay-Reports einschließlich einer Management-Zusammenfassung im Markdown-Format.

---

## ✅ Datenqualitätsprüfungen

Die aktuelle Implementierung enthält folgende Regeln:

| Regel | Dimension | Prüfung | Schweregrad |
|---|---|---|---|
| DQ001 | Vollständigkeit | Fehlende Flight ID | Hoch |
| DQ002 | Gültigkeit | Ungültiges Format der Flight ID | Mittel |
| DQ003 | Eindeutigkeit | Doppelte Flight ID | Hoch |
| DQ004 | Vollständigkeit | Fehlende Airline | Hoch |
| DQ005 | Gültigkeit | Ungültiger Flughafencode des Abflugorts | Hoch |
| DQ006 | Gültigkeit | Ungültiger Flughafencode des Zielorts | Hoch |
| DQ007 | Konsistenz | Abflug- und Zielort sind identisch | Hoch |
| DQ008 | Gültigkeit | Ungültiger geplanter Zeitstempel | Hoch |
| DQ009 | Vollständigkeit | Tatsächliche Zeit fehlt bei einem nicht stornierten Flug | Mittel |
| DQ010 | Gültigkeit | Ungültiger Flugstatus | Hoch |
| DQ011 | Gültigkeit | Passagierzahl ist keine nicht-negative Ganzzahl | Hoch |

Ein nicht stornierter Flug wird als verspätet klassifiziert, wenn die berechnete Verspätung größer als `DELAY_THRESHOLD_MINUTES` ist. Der Standardwert beträgt **15 Minuten**.

---

## Verwendete Technologien

| Bereich | Technologie |
|---|---|
| Datenverarbeitung | Python 3, pandas |
| Datenbank | PostgreSQL, psycopg |
| SQL | Schema Design, Views, Joins, CTEs, Aggregationen, Window Functions |
| Datenmodellierung | Fact- und Dimensionstabellen / Star-Schema-Export |
| Business Intelligence | Power BI, DAX, Power Query |
| Spreadsheet-Reporting | Excel |
| Tests | Python `unittest` |
| Continuous Integration | GitHub Actions |
| Logging | Python `logging` |

---

## 📁 Repository-Struktur

```text
airport-operations-data-pipeline/
├── .github/
│   └── workflows/
│       └── python-tests.yml
├── data/
│   ├── raw/
│   │   └── flights_raw.csv
│   ├── processed/
│   │   └── flights_clean.csv
│   ├── rejected/
│   │   ├── flights_rejected.csv
│   │   └── quality_issues.csv
│   └── powerbi/
│       ├── dim_airline.csv
│       ├── dim_airport.csv
│       ├── dim_date.csv
│       ├── fact_flights.csv
│       └── fact_quality_issues.csv
├── docs/
│   ├── images/
│   ├── data_dictionary.md
│   └── excel_power_query_guide.md
├── powerbi/
│   ├── power_query/
│   ├── airport_operations_dashboard.pdf
│   ├── dax_measures.md
│   ├── model_guide.md
│   └── README.md
├── reports/
│   ├── airport_operations_dashboard.xlsx
│   ├── executive_summary.csv
│   ├── management_summary.md
│   └── ...
├── scripts/
│   └── generate_demo_data.py
├── sql/
│   ├── 01_postgresql_schema.sql
│   ├── 02_views.sql
│   ├── 03_analysis_queries.sql
│   └── 04_data_quality_queries.sql
├── src/
│   ├── config.py
│   ├── extract.py
│   ├── load.py
│   ├── logger_config.py
│   ├── main.py
│   ├── management_summary.py
│   ├── report.py
│   └── transform.py
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔧 Installation und lokaler Start

### 1. Virtuelle Umgebung erstellen

```bash
python -m venv .venv
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Abhängigkeiten installieren

```bash
python -m pip install -r requirements.txt
```

### 3. Pipeline ausführen

```bash
python -m src.main
```

Eine andere CSV-Datei mit denselben erforderlichen Spalten kann über `--input` verwendet werden:

```bash
python -m src.main --input path/to/flights.csv
```

### 4. Tests ausführen

```bash
python -m unittest discover -s tests -v
```

---

## 🔧 Demo-Daten neu erzeugen

Der Quelldatensatz kann mit einem festen Seed reproduzierbar neu erstellt werden:

```bash
python scripts/generate_demo_data.py \
  --rows 800 \
  --seed 42 \
  --output data/raw/flights_raw.csv

python -m src.main
```

Durch eine Änderung von `--rows` oder `--seed` wird ein anderer synthetischer Datensatz erzeugt. Schema und Arten der absichtlich eingebauten Datenqualitätsprobleme bleiben dabei erhalten.

---

## PostgreSQL verwenden

Das Laden in die Datenbank ist optional. Als Standard-Datenbankname wird `airport_data` verwendet; das Projekt arbeitet mit dem PostgreSQL-Schema `airport_ops`.

Vor dem Datenbanklauf müssen die Verbindungswerte in der Shell gesetzt werden:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD="your_password"
export DB_NAME=airport_data
```

Anschließend kann die Pipeline mit Datenbank-Ladevorgang gestartet werden:

```bash
python -m src.main --with-db
```

Die Pipeline führt `sql/01_postgresql_schema.sql` automatisch aus und lädt anschließend Dimensionstabellen, Fact Tables, Quality Issues und Pipeline-Run-Daten.

Reporting-Views können danach separat erstellt werden:

```bash
psql -d airport_data -f sql/02_views.sql
```

`sql/03_analysis_queries.sql` enthält beispielhafte analytische SQL-Abfragen, darunter CTEs und Window Functions.  
`sql/04_data_quality_queries.sql` enthält Abfragen zur Überwachung der Datenqualität und zur Prüfung der Datenintegrität.

📌 **Konfigurationshinweis:** `.env.example` dient als Referenz für die benötigten Umgebungsvariablen. Die Anwendung liest Umgebungsvariablen direkt ein und lädt eine lokale `.env`-Datei nicht automatisch.

---

## 📊 Reporting-Ausgaben

Zu den wichtigsten erzeugten Dateien gehören:

- `data/processed/flights_clean.csv` – akzeptierte und angereicherte Flugdatensätze.
- `data/rejected/flights_rejected.csv` – abgelehnte Quelldatensätze inklusive Ablehnungsgrund.
- `data/rejected/quality_issues.csv` – nachvollziehbarer Quality-Issue-Eintrag für jeden erkannten Fehler.
- `reports/executive_summary.csv` – zentrale operative und Datenqualitäts-KPIs.
- `reports/airline_kpis.csv` und `reports/route_kpis.csv` – Leistungsübersichten nach Airline und Route.
- `reports/daily_kpis.csv` und `reports/monthly_kpis.csv` – zeitbasierte KPI-Trends.
- `reports/data_quality_summary.csv` – gruppierte Auswertung der fehlgeschlagenen Qualitätsregeln.
- `reports/delay_statistics.csv` – deskriptive Statistiken zu Verspätungen.
- `reports/management_summary.md` – kompakte Management-Zusammenfassung.
- `reports/airport_operations_dashboard.xlsx` – statischer Excel-Dashboard-/Report-Snapshot.

Weitere Informationen zu den wichtigsten Datensätzen und Spalten befinden sich in `docs/data_dictionary.md`.

---

## Power-BI-Artefakte

Die Pipeline schreibt BI-fertige Fact- und Dimensionstabellen nach `data/powerbi/`.

Der Ordner `powerbi/` enthält unter anderem:

- das exportierte Dashboard als PDF,
- DAX Measures,
- Hinweise zum Datenmodell und zu den Beziehungen,
- Power-Query-Skripte zum Laden der erzeugten CSV-Dateien.

![Power BI – Datenqualitätsübersicht](docs/images/powerbi_data_quality.png)

⚠️ **Hinweis zur `.pbix`-Datei:** Die ursprüngliche Entwicklungsdatei ist bewusst nicht Bestandteil dieser öffentlich vorbereiteten Version. Power-BI-Binärdateien können umgebungsspezifische Service- und Verbindungsmetadaten enthalten. Die enthaltenen PDF-, DAX-, Power-Query- und Modelldokumentationen sowie die Star-Schema-CSVs ermöglichen dennoch eine fachliche Prüfung und einen reproduzierbaren Neuaufbau des Reports.

---

## ✅ Tests und Continuous Integration

Die Testsuite deckt unter anderem folgende Bereiche ab:

- Transformations- und Validierungsregeln,
- Erkennung doppelter Datensätze,
- Behandlung stornierter Flüge,
- KPI- und Report-Aggregationen,
- Abstimmung der Executive-Kennzahlen,
- Erzeugung von Quality Issues,
- Export des Power-BI-Star-Schemas,
- Edge Case, bei dem alle Eingabedatensätze abgelehnt werden.

GitHub Actions führt bei jedem Push und Pull Request drei Prüfungen aus:

1. Python-Kompilierung.
2. Unit Tests.
3. Vollständiger Pipeline-Smoke-Test mit dem enthaltenen Demo-Datensatz.

---

## Nachgewiesene Kenntnisse

Das Projekt demonstriert praxisnahe Kenntnisse auf Junior-Level in folgenden Bereichen:

- modularer ETL-Entwurf mit Python,
- Datenbereinigung und Transformation mit pandas,
- regelbasierte Datenqualitätsprüfung und Behandlung abgelehnter Datensätze,
- Data Lineage über Quellzeilen und Issue IDs,
- KPI-Erzeugung und deskriptive Analysen,
- relationales Schema Design und SQL-Analyse,
- PostgreSQL-Loading und Upsert-Logik,
- Vorbereitung eines Star Schemas für BI-Werkzeuge,
- Reporting mit Power BI, DAX, Power Query und Excel,
- Unit Testing, Logging und GitHub Actions CI.

---

## 💡 Mögliche Weiterentwicklungen

Die folgenden Punkte sind **noch nicht Teil der aktuellen Implementierung**, bieten sich jedoch als sinnvolle nächste Schritte an:

- Datenbank-Views in den automatisierten Datenbank-Deployment-Prozess integrieren.
- Inkrementelle Verarbeitung anstelle vollständiger Dateiläufe ergänzen.
- Ein leichtgewichtiges Orchestrierungswerkzeug wie Prefect oder Airflow einführen.
- Docker für eine reproduzierbare Python-/PostgreSQL-Umgebung ergänzen.
- Erweiterte Datenqualitätskennzahlen und Run-to-Run-Trendanalysen hinzufügen.
- Weitere Datenquellen wie APIs oder Object Storage unterstützen.
- Eine vollständig bereinigte `.pbix`-Datei ausschließlich aus lokalen Projektquellen neu erstellen.
