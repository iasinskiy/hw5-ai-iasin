import json
from pathlib import Path
from typing import Optional, TypedDict
from langgraph.graph import END, START, StateGraph

DATA_PATH = Path("data/helpdesk.json")
HELP_DATA = (
    json.loads(DATA_PATH.read_text(encoding="utf-8")) if DATA_PATH.exists() else {}
)


class HelpdeskState(TypedDict):
  message: str
  category: Optional[str]
  reply: Optional[str]


def read_request(state: HelpdeskState) -> dict:
  msg = state["message"].lower()
  has_wifi = "wifi" in msg or "wi-fi" in msg
  has_pass = "password" in msg

  if has_wifi and has_pass:
    category = "both"
  elif has_wifi:
    category = "wifi"
  elif has_pass:
    category = "password"
  else:
    category = "other"

  return {"category": category}


def format_instructions(topic_data: dict) -> str:
  title = topic_data.get("title", "")
  steps = "\n".join(f"- {step}" for step in topic_data.get("steps", []))
  return f"{title}:\n{steps}"


def wifi_help(state: HelpdeskState) -> dict:
  wifi_data = HELP_DATA.get("instructions", {}).get("wifi", {})
  return {"reply": format_instructions(wifi_data)}


def password_help(state: HelpdeskState) -> dict:
  pass_data = HELP_DATA.get("instructions", {}).get("password", {})
  return {"reply": format_instructions(pass_data)}


def other_help(state: HelpdeskState) -> dict:
  return {
      "reply": (
          "Does your issue concern Wi-Fi or a password? Please clarify."
      )
  }


def clarify_problem(state: HelpdeskState) -> dict:
  return {
      "reply": (
          "Your request mentions both Wi-Fi and a password. Which problem"
          " would you like to solve first?"
      )
  }


def route_request(state: HelpdeskState) -> str:
  cat = state.get("category")
  if cat == "wifi":
    return "wifi_help"
  elif cat == "password":
    return "password_help"
  elif cat == "both":
    return "clarify_problem"
  return "other_help"


builder = StateGraph(HelpdeskState)

builder.add_node("read_request", read_request)
builder.add_node("wifi_help", wifi_help)
builder.add_node("password_help", password_help)
builder.add_node("other_help", other_help)
builder.add_node("clarify_problem", clarify_problem)

builder.add_edge(START, "read_request")
builder.add_conditional_edges(
    "read_request",
    route_request,
    {
        "wifi_help": "wifi_help",
        "password_help": "password_help",
        "other_help": "other_help",
        "clarify_problem": "clarify_problem",
    },
)

builder.add_edge("wifi_help", END)
builder.add_edge("password_help", END)
builder.add_edge("other_help", END)
builder.add_edge("clarify_problem", END)

part1_graph = builder.compile()

if __name__ == "__main__":
  print("=== GRAPH STRUCTURE ===")
  part1_graph.get_graph().print_ascii()
  print("=======================\n")

  test_messages = [
      "I cannot connect to Wi-Fi.",
      "I forgot my PASSWORD.",
      "My laptop screen is broken.",
      "My Wi-Fi password does not work.",
  ]

  for msg in test_messages:
    print(f"\n--- Request: '{msg}' ---")
    result = part1_graph.invoke({"message": msg})
    print(f"Category: {result.get('category')}")
    print(f"Reply:\n{result.get('reply')}")