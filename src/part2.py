import os
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
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


# 1. Определение State с поддержкой истории сообщений
class AgentState(TypedDict):
  messages: Annotated[list[BaseMessage], add_messages]


# 2. Инициализация инструментов и модели
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


# 3. Узел рассуждения (Reasoner Node)
def reasoner(state: AgentState):
  return {"messages": [llm_with_tools.invoke(state["messages"])]}


# 4. Сборка ReAct графа
builder = StateGraph(AgentState)

builder.add_node("reasoner", reasoner)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "reasoner")
builder.add_conditional_edges("reasoner", tools_condition)
builder.add_edge("tools", "reasoner")

part2_graph = builder.compile()

# 5. Демонстрационный запуск
if __name__ == "__main__":
  print("=== PART 2 GRAPH STRUCTURE (Mermaid) ===")
  print(part2_graph.get_graph().draw_mermaid())
  print("=========================================\n")

  try:
    print("=== PART 2 GRAPH STRUCTURE (ASCII) ===")
    part2_graph.get_graph().print_ascii()
    print("=======================================\n")
  except Exception:
    pass

  complex_query = (
      "Wi-Fi still does not work after I followed the instructions. Is it down?"
      " If it is working, help me prepare a ticket."
  )

  print(f"--- User Request: '{complex_query}' ---\n")

  config = {"recursion_limit": 10}
  inputs = {"messages": [HumanMessage(content=complex_query)]}

  for chunk in part2_graph.stream(inputs, config=config):
    for node_name, state_update in chunk.items():
      print(f"=== Node: {node_name} ===")
      latest_msg = state_update["messages"][-1]
      if hasattr(latest_msg, "tool_calls") and latest_msg.tool_calls:
        print(f"Tool Calls Requested: {latest_msg.tool_calls}\n")
      else:
        print(f"Output: {latest_msg.content}\n")