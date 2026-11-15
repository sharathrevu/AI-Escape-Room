"""Version 2 - Reliable AI Escape Room (Streamlit).
Run:  streamlit run v2/app.py
Without GEMINI_API_KEY the game still works in offline mode (rule-based parser + plain text).
"""
import streamlit as st
from dotenv import load_dotenv

import engine
import llm

load_dotenv()
st.set_page_config(page_title="AI Escape Room v2", page_icon="🗝️")


def new_game():
    st.session_state.state = engine.new_state()
    st.session_state.messages = [("assistant", engine.CONFIG["intro"])]


if "state" not in st.session_state:
    new_game()
client = llm.get_client()
state = st.session_state.state

st.title("🗝️ " + engine.CONFIG["title"] + " - Version 2")
with st.sidebar:
    st.header("How to play")
    st.write(engine.CONFIG["instructions"])
    p = engine.progress(state)
    st.subheader("Status")
    st.write(f"🚪 Door: **{p['door']}**  \n🧩 Puzzles solved: **{p['solved']}/{p['total']}**  \n"
             f"🎒 Inventory: {', '.join(p['inventory']) or 'empty'}  \n❌ Wrong codes: {p['wrong_codes']}")
    st.caption("LLM: " + ("Gemini (narrator + parser)" if client else "offline mode (no API key)"))
    if st.button("🔄 Restart game"):
        new_game()
        st.rerun()

for role, text in st.session_state.messages:
    st.chat_message(role).write(text)

if state["escaped"]:
    st.success("🎉 You escaped! Press Restart to play again.")
elif prompt := st.chat_input("What do you do?"):
    rule = engine.rule_parse(prompt)
    intent = (llm.parse_intent(client, prompt) if client else None) or rule
    intent = engine.sanitize_intent(intent, rule)
    result = engine.apply_action(state, intent)          # Python decides
    reply = llm.narrate(client, result) if client else result["facts"]   # LLM describes
    st.session_state.messages += [("user", prompt), ("assistant", reply)]
    st.rerun()
