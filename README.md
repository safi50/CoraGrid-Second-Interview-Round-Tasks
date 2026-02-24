# AI Backend

Async FastAPI service with two capabilities:
- **Company profiles** — fetches and normalises company data from the Finnish Trade Register (YTJ open data API)
- **Metrics extraction** — extracts structured financial/sustainability metrics from unstructured text using Google Gemini

## Stack

Python 3.10+ · FastAPI · Pydantic v2 · httpx · Google Gemini · python-dotenv

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY and GEMINI_MODEL
uvicorn app.main:app --reload
```

Docs available at `http://localhost:8000/docs`

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/company?business_id=<id>` | Company profile by Finnish Business ID (Y-tunnus) |
| `POST` | `/extract` | Extract financial metrics from raw text via Gemini |

**GET** `/company` — Queries the YTJ open data API with the provided Business ID, parses the raw response, and returns a normalised company profile including names, registration date, industry code, and website.

`/company?business_id=0116297-6`
```json
{
  "business_id": "0116297-6",
  "operating_names": ["Nokia Oyj"],
  "main_business_line_code": "46900",
  "registration_date": "1865-05-12",
  "website": "https://www.nokia.com"
}
```

**POST** `/extract` — Sends the input text to Google Gemini with a structured extraction prompt. The model returns JSON which is validated against the `Metrics` schema, with an automatic correction retry if the first response is invalid.

`/extract` `{ "text": "Q1 2024 revenue was 12.5M with a net loss of 200k..." }`
```json
{
  "income": 12500000,
  "net_income": -200000,
  "emissions": null,
  "water_usage": null,
  "quarter": "Q1 2024"
}
```

## Project structure

```
app/
├── main.py               # Routes
├── schema.py             # Pydantic models
├── extract_company_data.py  # YTJ API client & parser
└── structure_output.py   # Gemini extraction pipeline
```
