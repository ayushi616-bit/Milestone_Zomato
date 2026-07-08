# AI-Powered Restaurant Recommendation System

An AI-powered restaurant recommendation service inspired by Zomato. The system combines structured restaurant data from Hugging Face with Groq LLM re-ranking to deliver personalized, human-like suggestions based on user preferences.

## Documentation

| Document | Description |
|----------|-------------|
| [Docs/context.md](Docs/context.md) | Project overview and success criteria |
| [Docs/architecture.md](Docs/architecture.md) | System architecture and component design |
| [Docs/implementation-plan.md](Docs/implementation-plan.md) | Phase-wise implementation guide |
| [Docs/edge-case.md](Docs/edge-case.md) | Edge case handling reference |

## Prerequisites

- Python 3.10 or higher
- pip

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd Milestone_Zomato
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set your Groq/OpenAI provider details and API keys:

```ini
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

> **Note:** Never commit `.env` to version control. It is listed in `.gitignore`.

---

## Running the Application

### 1. Web User Interface (Streamlit)
Launch the interactive web UI to enter preferences, adjust sliders, and view restaurant recommendation cards:

```bash
PYTHONPATH=. .venv/bin/streamlit run src/app.py
```

### 2. Command Line Interface (CLI)
Query recommendations directly from your terminal. If parameters are omitted, it will prompt you interactively:

```bash
PYTHONPATH=. .venv/bin/python scripts/recommend_cli.py --location Basavanagudi --budget medium --cuisine "South Indian" --min-rating 4.0
```

### 3. Dataset Explorer
Inspect the loaded Zomato dataset, check raw columns, and view unique locations/cuisine stats:

```bash
PYTHONPATH=. .venv/bin/python scripts/explore_dataset.py
```

---

## Verify Installation

Confirm imports work:

```bash
python -c "from src.data.models import Restaurant, UserPreferences; print('OK')"
```

Run the complete test suite (includes unit, integration, and UI tests):

```bash
.venv/bin/pytest
```

---

## Project Structure

```
Milestone_Zomato/
├── scripts/
│   ├── explore_dataset.py     # Explore Zomato schema and distributions
│   ├── recommend_cli.py       # End-to-end CLI recommendations
│   └── filter_smoke_test.py   # Heuristic filters verification
├── src/
│   ├── data/
│   │   ├── loader.py          # Hugging Face dataset ingestion
│   │   ├── preprocessor.py    # Text, rating, cost normalizer
│   │   ├── store.py           # In-memory lazily-loaded caching store
│   │   └── models.py          # Domain data classes (Restaurant, etc.)
│   ├── filters/
│   │   └── filter_engine.py   # Deterministic constraints filtering
│   ├── llm/
│   │   ├── client.py          # Groq/OpenAI client implementation
│   │   ├── prompt_builder.py  # Message constructing templates
│   │   └── parser.py          # Response validations & retry logic
│   ├── presentation/
│   │   └── formatter.py       # Display formatting and conversion
│   ├── config.py              # Environment configuration loader
│   ├── validators.py          # User input schema validation
│   └── app.py                 # Streamlit web UI application
├── tests/                     # Pytest suite files
│   ├── conftest.py            # Shared fixtures
│   ├── test_app.py            # UI integration tests
│   ├── test_config.py
│   ├── test_filter_engine.py
│   ├── test_formatter.py
│   ├── test_llm_client.py
│   ├── test_loader.py
│   ├── test_models.py
│   ├── test_parser.py
│   ├── test_preprocessor.py
│   ├── test_prompt_builder.py
│   └── test_validators.py
├── .env.example
├── requirements.txt
└── README.md
```

## Configuration

Key settings in `src/config.py` (overridable via environment):

| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_PROVIDER` | `groq` | LLM client API provider (`groq` or `openai`) |
| `GROQ_API_KEY` | — | Groq API Key (from `.env` when provider is `groq`) |
| `OPENAI_API_KEY` | — | OpenAI API Key (from `.env` when provider is `openai`) |
| `LLM_MODEL` | `llama-3.1-8b-instant` | Model name (automatically selects `llama-3.1-8b-instant` for `groq`, `gpt-4o-mini` for `openai`) |
| `candidate_cap` | `20` | Max restaurants sent to LLM |
| `top_k_recommendations` | `5` | Number of recommendations to return |

## Development Status

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | Complete | Project setup, domain models, config |
| 1 | Complete | Data ingestion and preprocessing |
| 2 | Complete | Filtering and candidate preparation |
| 3 | Complete | LLM recommendation engine |
| 4 | Complete | Orchestration and presentation |
| 5 | Complete | User interface |
| 6 | Complete | Hardening and delivery |

## License

See repository license for details.
