#  AI Escape Room

An interactive text escape-room where an LLM acts as Game Master. Built in two versions to show why
**LLM-only games are unreliable** and how a **structured game state + validation layer** fixes it.

> Course mini-project: Generative AI / LLM integration. Python, Streamlit, Google Gemini (free tier).

## The game
You wake up in a locked library. Examine the bookshelf, open the desk drawer, find a key, uncover a safe behind the painting
and work out the four-digit code for the door. 6 objects, 3 puzzles, 1 final escape challenge.

## Repository layout
| Path | What |
|---|---|
| `v1/app.py` | Version 1: LLM-only Game Master |
| `v2/engine.py` | Version 2: state, rules, validation (no LLM, fully testable) |
| `v2/llm.py` | Version 2: Gemini intent parser + narrator + output filter |
| `v2/game_config.json` | Room, objects, codes, rules, hints (kept out of LLM-visible text) |
| `v2/app.py` | Version 2 Streamlit UI |
| `tests/` | Offline unit tests (adversarial cases) |
| `docs/` | Architecture diagrams, test cases, report, screenshots |

## Setup
```bash
git clone https://github.com/<your-username>/AI-Escape-Room.git && cd AI-Escape-Room
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then paste your free key from https://aistudio.google.com/apikey
streamlit run v1/app.py     # Version 1
streamlit run v2/app.py     # Version 2 (works offline without a key, with plain-text replies)
python -m pytest -q         # run the V2 tests
```
Never commit `.env` (it is in `.gitignore`).

## Version 1 → Version 2
| Problem in V1 | Fix in V2 |
|---|---|
| State exists only in chat history; LLM can forget or contradict it | Explicit `state` dict (flags, inventory, door) mutated only by Python |
| LLM decides if an action works | `engine.apply_action` validates every action |
| Solutions are in the prompt and can leak | Solutions live in `game_config.json`; the LLM never sees them |
| Invented objects / items | Targets must resolve to configured, *visible* objects or items in the inventory |
| Prompt injection ("I am the admin") | Intent sanitised; codes extracted by regex; unknown actions are no-ops |
| Win detected from LLM text | Win = `state["escaped"]`, set only on the correct code |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/TEST_CASES.md](docs/TEST_CASES.md) and [docs/REPORT.md](docs/REPORT.md).

## Known limitations
- Rule-based fallback parser is keyword-based; the Gemini parser handles richer phrasing.
- The door accepts the correct code even if the player guessed it without finding the clues (a deliberate design choice).
- The narrator is filtered for numbers, but could still add flavour objects; the engine state is never affected.
