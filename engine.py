"""Version 2 - deterministic game engine.
Python owns the state, the rules and the solutions. The LLM never decides
whether an action succeeds; it only (a) translates the player's words into an
intent and (b) narrates the outcome this module computed.
"""
import json
import re
from pathlib import Path

CONFIG = json.loads(Path(__file__).with_name("game_config.json").read_text(encoding="utf-8"))
OBJECTS, ITEMS = CONFIG["objects"], CONFIG["items"]
ACTIONS = {"examine", "take", "use", "enter_code", "move", "inventory", "hint", "unknown"}
NOT_FOUND = "There is nothing like that here that you can interact with."


# ---------- state ----------
def new_state():
    return {"flags": {}, "inventory": [], "attempts": 0, "moves": 0, "escaped": False}


def flag(s, f):
    return bool(s["flags"].get(f))


def visible_objects(s):
    return [k for k, o in OBJECTS.items() if not o.get("hidden_until") or flag(s, o["hidden_until"])]


def progress(s):
    """Non-secret summary for the UI sidebar."""
    return {"solved": sum(flag(s, p) for p in CONFIG["puzzles"]), "total": len(CONFIG["puzzles"]),
            "inventory": [ITEMS[i]["name"] for i in s["inventory"]],
            "door": "OPEN" if s["escaped"] else "LOCKED", "wrong_codes": s["attempts"]}


# ---------- helpers ----------
def R(ok, event, facts):
    return {"ok": ok, "event": event, "facts": facts}


def _find(text, registry):
    """Ids whose alias appears in text (whole words), ordered by position."""
    t, hits = (text or "").lower().replace("_", " "), []
    for k, v in registry.items():
        for a in v["aliases"] + [k.replace("_", " ")]:
            m = re.search(r"\b" + re.escape(a) + r"\b", t)
            if m:
                hits.append((m.start(), k))
                break
    return [k for _, k in sorted(hits)]


def resolve_object(name):
    ids = _find(name, OBJECTS)
    return ids[0] if ids else None


def resolve_item(name):
    ids = _find(name, ITEMS)
    return ids[0] if ids else None


# ---------- action handlers (validation lives here) ----------
def h_examine(s, target, item, code):
    name = target or item
    oid = resolve_object(name)
    if oid:
        if oid not in visible_objects(s):
            return R(False, "not_found", NOT_FOUND)
        o, text = OBJECTS[oid], OBJECTS[oid]["description"]
        for v in o.get("variants", []):
            if flag(s, v["when"]):
                text = v["text"]
        if o.get("on_examine_flag"):
            s["flags"][o["on_examine_flag"]] = True
        return R(True, "examine", text)
    iid = resolve_item(name)
    if iid and iid in s["inventory"]:
        return R(True, "examine_item", ITEMS[iid]["description"])
    return R(False, "not_found", NOT_FOUND)


def h_take(s, target, item, code):
    name = item or target
    iid = resolve_item(name)
    if not iid:
        if resolve_object(name):
            return R(False, "cannot_take", "That cannot be carried away.")
        return R(False, "not_found", NOT_FOUND)
    if iid in s["inventory"]:
        return R(False, "already_have", "You already have that.")
    if not flag(s, ITEMS[iid]["requires_flag"]):          # not reachable yet -> don't leak it exists
        return R(False, "not_found", NOT_FOUND)
    s["inventory"].append(iid)
    s["flags"][iid + "_taken"] = True
    return R(True, "take", f"You take the {ITEMS[iid]['name']} and put it in your pocket.")


def h_use(s, target, item, code):
    oid = resolve_object(target)
    if oid and oid not in visible_objects(s):
        return R(False, "not_found", NOT_FOUND)
    if not item:
        if not oid:
            return R(False, "unclear", "It is unclear what you want to use or open.")
        o = OBJECTS[oid]
        if "unlock_flag" in o:
            if flag(s, o["unlock_flag"]):
                return R(True, "already_open", "That is already open.")
            return R(False, "locked", o["locked_text"])
        return R(False, "no_effect", "Nothing happens.")
    iid = resolve_item(item)
    if not iid or iid not in s["inventory"]:
        return R(False, "missing_item", "You are not carrying that.")
    if not oid:
        return R(False, "unclear", "It is unclear where you want to use that.")
    for r in CONFIG["use_rules"]:
        if r["item"] == iid and r["target"] == oid and flag(s, r["requires_flag"]):
            if flag(s, r["sets_flag"]):
                return R(True, "already_open", "That is already open.")
            s["flags"][r["sets_flag"]] = True
            return R(True, "use", r["text"])
    return R(False, "no_effect", "Nothing happens.")


def h_enter_code(s, target, item, code):
    oid = resolve_object(target)
    if not oid:
        return R(False, "unclear", "It is unclear which lock you want to try a code on.")
    if oid not in visible_objects(s):
        return R(False, "not_found", NOT_FOUND)
    o = OBJECTS[oid]
    if "code" not in o:
        return R(False, "no_keypad", "There is no code lock on that.")
    if flag(s, o["unlock_flag"]):
        return R(True, "already_open", "That is already open.")
    if not code:
        return R(False, "unclear", "A four-digit code is needed. None was given.")
    if code != o["code"]:
        s["attempts"] += 1
        return R(False, "wrong_code", "That code is wrong. The lock does not move.")
    s["flags"][o["unlock_flag"]] = True
    if oid == "door":
        s["escaped"] = True
    return R(True, "unlock", o["unlock_text"])


def h_move(s, target, item, code):
    oid = resolve_object(target)
    if not oid or oid not in visible_objects(s):
        return R(False, "not_found", NOT_FOUND)
    o = OBJECTS[oid]
    if not o.get("movable"):
        return R(False, "no_effect", "It is too heavy or fixed in place and will not budge.")
    if flag(s, o["move_flag"]):
        return R(False, "already_done", "You already moved that.")
    s["flags"][o["move_flag"]] = True
    return R(True, "move", o["move_text"])


def h_inventory(s, target, item, code):
    inv = [ITEMS[i]["name"] for i in s["inventory"]]
    return R(True, "inventory", "You are carrying: " + ", ".join(inv) + "." if inv else "Your pockets are empty.")


def h_hint(s, target, item, code):
    for h in CONFIG["hints"]:
        if not flag(s, h["until"]):
            return R(True, "hint", h["text"])
    return R(True, "hint", "You have everything you need. Try the door.")


def h_unknown(s, target, item, code):
    return R(False, "unknown", "That does not change anything in the room. Game rules cannot be altered by the player.")


HANDLERS = {"examine": h_examine, "take": h_take, "use": h_use, "enter_code": h_enter_code,
            "move": h_move, "inventory": h_inventory, "hint": h_hint}


def apply_action(s, intent):
    """The single entry point that mutates state."""
    if s["escaped"]:
        return R(False, "game_over", "The player has already escaped. The game is over.")
    s["moves"] += 1
    code = intent.get("code")
    code = code if isinstance(code, str) and re.fullmatch(r"\d{4}", code) else None
    return HANDLERS.get(intent.get("action"), h_unknown)(s, intent.get("target"), intent.get("item"), code)


# ---------- offline intent parser (also used as fallback / for code extraction) ----------
def rule_parse(text):
    t = (text or "").lower()
    m = re.search(r"\b(\d{4})\b", t)
    code = m.group(1) if m else None
    objs, items = _find(t, OBJECTS), _find(t, ITEMS)
    has = lambda *w: any(re.search(r"\b" + x, t) for x in w)
    if code:
        action = "enter_code"
    elif has("inventory", "pockets", "what am i carrying", "what do i have"):
        action = "inventory"
    elif has("hint", "stuck", "help"):
        action = "hint"
    elif has("move", "lift", "push", "slide", "behind", "remove"):
        action = "move"
    elif has("take", "pick", "grab", "collect", "retrieve", "pocket"):
        action = "take"
    elif has("use", "unlock", "open", "insert", "try", "turn"):
        action = "use"
    elif has("examine", "look", "inspect", "read", "check", "search", "study"):
        action = "examine"
    else:
        action = "unknown"
    return {"action": action, "target": objs[0] if objs else None,
            "item": items[0] if items else None, "code": code}


def sanitize_intent(intent, rule_intent):
    """Never trust the LLM: unknown actions are dropped and codes come only from a regex."""
    out = {"action": intent.get("action") if intent.get("action") in ACTIONS else "unknown",
           "target": str(intent.get("target") or "")[:60] or None,
           "item": str(intent.get("item") or "")[:60] or None,
           "code": rule_intent["code"]}
    return out
