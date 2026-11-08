import os
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import Annotated, TypedDict

from tools import check_service_status, find_instructions, prepare_ticket

# Загружаем переменные окружения из .env
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
base_url = os.getenv("OPENAI_BASE_URL")

if not api_key:
  raise ValueError(
      "OPENAI_API_KEY is missing! Make sure it is defined in your .env file."
  )


# 1. State с поддержкой истории сообщений
class AgentState(TypedDict):
  messages: Annotated[list[BaseMessage], add_messages]


tools = [find_instructions, check_service_status, prepare_ticket]

llm_kwargs = {
    "model": model_name,
    "api_key": api_key,
    "temperature": 0,
}
if base_url:
  llm_kwargs["base_url"] = base_url

llm = ChatOpenAI(**llm_kwargs)
llm_with_tools = llm.bind_tools(tools)


def reasoner(state: AgentState):
  return {"messages": [llm_with_tools.invoke(state["messages"])]}


# 2. Построение графа
builder = StateGraph(AgentState)
builder.add_node("reasoner", reasoner)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "reasoner")
builder.add_conditional_edges("reasoner", tools_condition)
builder.add_edge("tools", "reasoner")

# 3. Подключаем MemorySaver (Checkpointer)
memory = MemorySaver()
part3_graph = builder.compile(checkpointer=memory)

# 4. Вывод структуры и запуск сессии с памятью
if __name__ == "__main__":
  print("=== PART 3 GRAPH STRUCTURE (Mermaid) ===")
  print(part3_graph.get_graph().draw_mermaid())
  print("=========================================\n")

  try:
    print("=== PART 3 GRAPH STRUCTURE (ASCII) ===")
    part3_graph.get_graph().print_ascii()
    print("=======================================\n")
  except Exception:
    pass

  config = {"configurable": {"thread_id": "session_helpdesk_101"}}

  print("=== STEP 1: Сообщение 1 ===")
  msg1 = "I cannot connect to the Wi-Fi network."
  print(f"User: {msg1}\n")

  for chunk in part3_graph.stream(
      {"messages": [HumanMessage(content=msg1)]}, config=config
  ):
    for node_name, state_update in chunk.items():
      print(f"[{node_name}]")

  snapshot1 = part3_graph.get_state(config)
  print(f"\nAgent Final Reply 1:\n{snapshot1.values['messages'][-1].content}\n")
  print("-" * 50)

  print("\n=== STEP 2: Сообщение 2 (контекстный вопрос без слова Wi-Fi) ===")
  msg2 = "I tried restarting, but it still fails. Please create a ticket for me."
  print(f"User: {msg2}\n")

  for chunk in part3_graph.stream(
      {"messages": [HumanMessage(content=msg2)]}, config=config
  ):
    for node_name, state_update in chunk.items():
      print(f"[{node_name}]")

  snapshot2 = part3_graph.get_state(config)
  print(f"\nAgent Final Reply 2:\n{snapshot2.values['messages'][-1].content}\n")