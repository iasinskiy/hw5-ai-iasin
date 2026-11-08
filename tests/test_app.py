import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from src.part1 import read_request, route_request
from src.tools import check_service_status, find_instructions, prepare_ticket


# 1. Проверка статической маршрутизации (Part 1)
def test_static_routing_wifi():
  state = read_request({"message": "I cannot connect to Wi-Fi"})
  assert route_request(state) == "wifi_help"


def test_static_routing_password():
  state = read_request({"message": "I forgot my password"})
  assert route_request(state) == "password_help"


def test_static_routing_both():
  state = read_request({"message": "Wi-Fi password isn't working"})
  assert route_request(state) == "clarify_problem"


def test_static_routing_other():
  state = read_request({"message": "My keyboard is broken"})
  assert route_request(state) == "other_help"


# 2. Проверка работы инструментов (Part 2)
def test_find_instructions_tool():
  res = find_instructions.invoke("wifi")
  assert "Campus-Demo" in res or "Wi-Fi" in res


def test_check_service_status_tool():
  res = check_service_status.invoke("Wi-Fi")
  assert "status" in res.lower()


def test_prepare_ticket_tool():
  res = prepare_ticket.invoke(
      {"problem_description": "Network fail", "steps_tried": "Restarted router"}
  )
  assert "DRAFT" in res
  assert "Network fail" in res


# 3. Проверка сохранения памяти и изоляции пользователей (Part 3)
class DummyState(TypedDict):
  messages: Annotated[list, add_messages]


def test_thread_isolation():
  memory = MemorySaver()

  def echo_node(state: DummyState):
    return {"messages": [AIMessage(content="Acknowledged")]}

  builder = StateGraph(DummyState)
  builder.add_node("agent", echo_node)
  builder.add_edge(START, "agent")
  builder.add_edge("agent", END)

  graph = builder.compile(checkpointer=memory)

  # Пользователь A
  config_a = {"configurable": {"thread_id": "demo-user-a"}}
  graph.invoke({"messages": [("user", "Hello from User A")]}, config=config_a)

  # Пользователь B
  config_b = {"configurable": {"thread_id": "demo-user-b"}}
  graph.invoke({"messages": [("user", "Hello from User B")]}, config=config_b)

  state_a = graph.get_state(config_a)
  state_b = graph.get_state(config_b)

  # Проверяем, что контексты сессий не смешиваются
  assert len(state_a.values["messages"]) == 2
  assert len(state_b.values["messages"]) == 2
  assert "User A" in state_a.values["messages"][0].content
  assert "User B" in state_b.values["messages"][0].content