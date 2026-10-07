import urllib.request
import json
import pytest

def test_conversation_flows():
    test_cases = [
        {
            "query": "Change UI theme green to red.",
            "expect_intent": "UI_MUTATION",
            "expect_action": "SET_THEME"
        },
        {
            "query": "Change the price of Rosemary Scalp Oil through $30.",
            "expect_intent": "UI_MUTATION",
            "expect_action": "UPDATE_PRODUCT_PRICE"
        },
        {
            "query": "Can you add one more?",
            "expect_intent": "UI_MUTATION",
            "expect_action": "ADD_TO_CART"
        },
        {
            "query": "reduce the card size of rosemary oil",
            "expect_intent": "UI_MUTATION",
            "expect_action": "UPDATE_CARD_STYLE"
        }
    ]

    session_id = "test-session-pytest"

    for tc in test_cases:
        q = tc["query"]
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/chat",
            data=json.dumps({"message": q, "session_id": session_id, "dev_mode": False}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            intent = data.get("intent")
            ui_commands = data.get("ui_commands") or data.get("ui_actions") or []
            action_types = [a.get("action") or a.get("command") for a in ui_commands] if isinstance(ui_commands, list) else []
            
            assert intent == tc["expect_intent"], f"Expected intent {tc['expect_intent']}, got {intent} for '{q}'"
            assert tc["expect_action"] in action_types, f"Expected action {tc['expect_action']} in {action_types} for '{q}'"

