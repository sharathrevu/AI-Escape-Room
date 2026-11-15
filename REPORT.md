# Report: AI-Powered Escape Room

## 1. Design
**Scenario.** A locked library with six interactive objects (desk, bookshelf/red books, painting, drawer, hidden safe, door) and
three chained puzzles: books → drawer code (4173) → brass key → safe → card + painting signature → door code (1926).

**Version 1** uses a single Gemini chat with a system prompt that contains the room, the secrets and the rules. Streamlit provides the UI;
the chat history is the only memory; victory is detected by a token the LLM emits.

**Version 2** separates concerns: `engine.py` holds the state dict, the rules and the validation functions; `game_config.json` holds the content and solutions;
`llm.py` has two narrow LLM roles: an intent parser (free text → JSON) and a narrator (verified outcome → prose).

## 2. Implementation highlights
- **State:** `flags`, `inventory`, `attempts`, `escaped`. Objects can be hidden until a flag is set, so clues cannot be seen early.
- **Validation:** one handler per action; each checks visibility, inventory, preconditions and codes before changing state.
- **Security:** the parser LLM has no knowledge of solutions; codes come only from a regex; unknown actions do nothing; the narrator output is rejected if it contains numbers not in the verified facts.
- **Offline mode:** a rule-based parser lets the game and tests run without an API key.

## 3. Problems encountered
_Fill in from your own experience. Candidates: [ ] V1 forgot/contradicted progress after N turns; [ ] V1 leaked or accepted a false claim (see TEST_CASES.md);
[ ] Gemini returned non-JSON from the parser, so the fallback parser was added; [ ] alias matching bug with underscored ids (fixed during testing);
[ ] free-tier rate limits._

## 4. Improvements and results
All 10 automated tests pass, covering: uncollected item, wrong code, false "already solved" claim, administrator impersonation,
secret extraction, non-existent object, hidden object, repeated actions and a full walkthrough. Add your V1 observations from TEST_CASES.md here.

## 5. Limitations and future work
Keyword fallback parser; LLM narrator can still add harmless flavour text; no persistence across browser sessions; add multiple rooms, timers and a scoring system.
