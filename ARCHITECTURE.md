# Architecture

## Version 1 - LLM does everything
```mermaid
flowchart LR
    P[Player] -->|natural language| UI[Streamlit UI]
    UI -->|message + full chat history| LLM[Gemini - Game Master]
    SP[(System prompt: room, secrets, rules)] --> LLM
    LLM -->|narration, may contain the token ESCAPED| UI
    UI --> P
```
State, rules, solutions and win detection all live inside the LLM's context. Nothing is enforced.

## Version 2 - Python decides, LLM describes
```mermaid
flowchart LR
    P[Player] --> UI[Streamlit UI]
    UI --> IP[Intent parser<br/>Gemini JSON + regex fallback]
    IP -->|intent: action, target, item| SAN[sanitize_intent<br/>code extracted by regex only]
    SAN --> ENG[Game engine<br/>validation + handlers]
    CFG[(game_config.json<br/>objects, codes, rules)] --> ENG
    ST[(Game state<br/>flags, inventory, door)] <--> ENG
    ENG -->|verified outcome facts| NAR[Narrator<br/>Gemini]
    NAR --> FIL[Output filter<br/>no new numbers]
    FIL --> UI
    ENG -->|progress, inventory| UI
```
Security boundaries: the parser LLM never sees the solutions; the narrator only sees the already-decided outcome;
the engine is the only code that mutates state; codes are never taken from LLM output.
