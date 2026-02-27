# PhysicsLens 🔭

> AI-powered Free Body Diagram generator for physics students. Paste a Newton's Laws problem (or upload a photo) and get an instant, color-coded FBD.

**Built for the AMD Slingshot Hackathon**

---

## Features

- **AI Text Parsing** — Paste any physics problem and Gemini 2.5 Flash extracts objects, surfaces, forces, and friction into structured JSON
- **Image Upload / OCR** — Snap a photo of a textbook, worksheet, or handwritten problem — Gemini Vision reads and parses it
- **4 Diagram Types** — Inclined plane, horizontal surface, Atwood machine (pulley), and elevator/vertical scenarios
- **Color-Coded Forces** — Gravity (blue), Normal (green), Friction (orange), Applied (red), Tension (purple)
- **Validated Output** — Pydantic v2 models with referential integrity checks
- **Rate Limited** — 10 requests/minute on parsing endpoints (configurable)

---

## Quick Start

### 1. Clone & install

```bash
git clone <repo-url>
cd PhysicsLens
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Set up environment

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

Server starts at **http://localhost:8000**

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check + endpoint list |
| `POST` | `/parse` | Parse a text physics problem → structured JSON |
| `POST` | `/parse-image` | Upload an image of a question → structured JSON |
| `POST` | `/diagram` | Generate SVG diagram from parsed JSON |
| `GET` | `/test-diagram` | Sample inclined plane FBD |
| `GET` | `/test-diagram/horizontal` | Sample horizontal surface FBD |
| `GET` | `/test-diagram/pulley` | Sample Atwood machine FBD |
| `GET` | `/test-diagram/vertical` | Sample elevator FBD |

### Parse a text problem

```bash
curl -X POST http://localhost:8000/parse \
  -H "Content-Type: application/json" \
  -d '{"problem": "A 5 kg block slides down a 30 degree incline with coefficient of friction 0.2"}'
```

### Parse from image

```bash
curl -X POST http://localhost:8000/parse-image \
  -F "file=@photo_of_question.jpg"
```

Supports: JPEG, PNG, WebP, GIF, BMP (max 10MB)

---

## Project Structure

```
PhysicsLens/
├── app/
│   ├── main.py              # FastAPI app, CORS, rate limiting
│   ├── config.py             # Environment config (pydantic-settings)
│   ├── models.py             # Pydantic v2 schemas + validation
│   ├── prompts.py            # AI prompt templates + few-shot examples
│   ├── parser.py             # Gemini text + vision parsing with retry
│   ├── diagrams/
│   │   ├── base.py           # SVG utilities, color palette, arrows
│   │   ├── incline.py        # Inclined plane diagrams
│   │   ├── horizontal.py     # Horizontal surface diagrams
│   │   ├── pulley.py         # Atwood machine diagrams
│   │   └── vertical.py       # Elevator / vertical diagrams
│   └── routes/
│       ├── parse.py          # /parse + /parse-image endpoints
│       └── diagram.py        # /diagram + /test-diagram endpoints
├── tests/
│   ├── test_models.py        # Schema + validation tests
│   ├── test_parser.py        # Parser tests (mocked AI)
│   └── test_diagrams.py      # SVG output tests
├── .env                      # API keys (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Tech Stack

- **Backend:** FastAPI + Uvicorn
- **AI:** Google Gemini 2.5 Flash (text + vision)
- **Validation:** Pydantic v2
- **Rate Limiting:** slowapi
- **Retry:** tenacity
- **Tests:** pytest

---

## Roadmap

- [ ] React + D3.js frontend with interactive diagrams
- [ ] Step-by-step FBD construction walkthrough
- [ ] Newton's equation derivation from diagrams
- [ ] "What if" mode — tweak mass/angle/force live
- [ ] Hindi/Tamil support via Bhashini API
- [ ] Deploy to Railway/Render
