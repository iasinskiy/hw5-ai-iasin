import json
from pathlib import Path
from langchain_core.tools import tool


@tool
def find_instructions(topic: str) -> str:
  """Looks up Wi-Fi or password instructions in the local helpdesk data."""
  path = Path("data/helpdesk.json")
  if not path.exists():
    return "Helpdesk reference file not found."

  data = json.loads(path.read_text(encoding="utf-8"))
  instructions = data.get("instructions", {})
  topic_lower = topic.lower()

  if "wifi" in topic_lower or "wi-fi" in topic_lower:
    info = instructions.get("wifi")
  elif "pass" in topic_lower:
    info = instructions.get("password")
  else:
    info = None

  if info:
    title = info.get("title", "")
    steps = "\n".join(f"- {s}" for s in info.get("steps", []))
    return f"{title}:\n{steps}"

  return "Topic not found. Available topics: wifi, password."


@tool
def check_service_status(service_name: str) -> str:
  """Looks up whether the requested service is operating or has a known outage."""
  path = Path("data/service_status.json")
  if not path.exists():
    return "Service status file not found."

  data = json.loads(path.read_text(encoding="utf-8"))
  key = service_name.lower().strip()
  if key in data:
    return f"Service '{service_name}' status: {data[key]}"
  return f"Service '{service_name}' status unknown."


@tool
def prepare_ticket(problem_description: str, steps_tried: str) -> str:
  """Produces a local ticket draft from the problem description and steps already tried."""
  ticket = {
      "status": "DRAFT",
      "problem": problem_description,
      "steps_tried": steps_tried,
  }
  return f"Ticket Draft Created Successfully: {json.dumps(ticket)}"