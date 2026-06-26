import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def chat_with_copilot(state: Dict[str, Any], user_message: str) -> Dict[str, Any]:
    """
    An interactive copilot that uses the current LangGraph state (memory, impact, decisions)
    to answer actuarial questions.
    """
    api_key = state.get("api_key", "")
    if not api_key:
        return {"error": "API key required for copilot."}
        
    try:
        if api_key.startswith("sk-"):
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o", api_key=api_key)
        else:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, max_retries=0)
    except Exception as e:
        return {"error": f"Failed to initialize LLM: {str(e)}"}
        
    # Extract relevant state
    memory = state.get("investigation_memory", [])
    impact = state.get("business_impact", {})
    options = state.get("decision_options", [])
    chat_history = state.get("chat_history", [])
    notebook = state.get("planner_notebook", [])
    event = state.get("event_reconstruction", "")
    metrics = state.get("drift_metrics", {})
    
    system_prompt = f"""
    You are an AI Actuarial Copilot assisting an actuary.
    You have deep knowledge of the current investigation state. Use this data to answer questions directly, accurately, and concisely.
    Do NOT hallucinate data outside of what is provided.
    
    Drift Metrics: {json.dumps(metrics, indent=2)}
    
    Current Business Impact:
    {json.dumps(impact, indent=2)}
    
    Event Reconstruction: {event}
    
    Planner Reasoning Notebook:
    {json.dumps(notebook, indent=2)}
    
    Suggested Decision Options:
    {json.dumps(options, indent=2)}
    """
    
    # Build message history
    messages = [SystemMessage(content=system_prompt)]
    for msg in chat_history[-5:]: # Keep last 5 turns for context
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
            
    messages.append(HumanMessage(content=user_message))
    
    try:
        if llm:
            response = llm.invoke(messages)
            ai_reply = response.content
            
            # Update chat history
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": ai_reply})
            
            state["chat_history"] = chat_history
            
            return {"reply": ai_reply, "chat_history": chat_history}
        else:
            return {"reply": "LLM not connected. Cannot process query."}
    except Exception as e:
        print(f"Error invoking LLM in copilot: {e}")
        return {"error": f"Failed to get response: {str(e)}"}
