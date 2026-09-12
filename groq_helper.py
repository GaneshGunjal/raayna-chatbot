"""
Groq helper with agentic tool calling.
Handles null parameters, type coercion, and multiple tool calls.
"""
import os
import json
import inspect
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"


def _build_param_schema(func):
    """
    Build a schema where every parameter is an OPTIONAL STRING.
    This prevents Groq from sending null, int, or wrong types that would
    fail validation.
    """
    sig = inspect.signature(func)
    properties = {}
    for name, param in sig.parameters.items():
        properties[name] = {
            "type": "string",
            "description": f"{name} (string, optional)"
        }
    return properties


def build_tool_schema(tool_functions: dict):
    """Convert Python functions into Groq's tool schema."""
    tools = []
    for func in tool_functions.values():
        tools.append({
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": (func.__doc__ or "").strip(),
                "parameters": {
                    "type": "object",
                    "properties": _build_param_schema(func),
                    "required": []   # nothing required → Groq can't fail on missing args
                }
            }
        })
    return tools


def _coerce_args(raw_args: dict) -> dict:
    """
    Convert every argument value to a safe string.
    Handles null, numbers, booleans — everything becomes a string.
    Empty string is treated as "not provided" and gets skipped by
    the search functions.
    """
    cleaned = {}
    for k, v in raw_args.items():
        if v is None:
            cleaned[k] = ""
        elif isinstance(v, (int, float)):
            cleaned[k] = str(v)
        elif isinstance(v, bool):
            cleaned[k] = str(v).lower()
        elif isinstance(v, str):
            cleaned[k] = v
        else:
            cleaned[k] = str(v)
    return cleaned


def call_groq_with_tools(
    system_prompt: str,
    user_message: str,
    conversation_history: list,
    tool_functions: dict,
    max_iterations: int = 5,
    force_media: bool = False,
):
    """
    Agentic loop:
    - Model decides which tools to call
    - We execute them, feeding results back
    - Loop until we get a final text answer
    """
    tools = build_tool_schema(tool_functions)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history[-6:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    messages.append({"role": "user", "content": user_message})

    for iteration in range(max_iterations):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.2,
            )
        except Exception as e:
            return (
                f"Sorry, technical issue. Please try again. "
                f"(Error: {str(e)[:200]})"
            )

        response_message = response.choices[0].message

        # If no tool call → final answer
        if not response_message.tool_calls:
            return (
                response_message.content
                or "I'm here to help with property inquiries."
            )

        # Record assistant's tool-call message
        messages.append({
            "role": "assistant",
            "content": response_message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in response_message.tool_calls
            ]
        })

        # Execute each tool call
        for tool_call in response_message.tool_calls:
            func_name = tool_call.function.name

            try:
                raw_args = json.loads(tool_call.function.arguments)
                if not isinstance(raw_args, dict):
                    raw_args = {}
            except (json.JSONDecodeError, TypeError):
                raw_args = {}

            func_args = _coerce_args(raw_args)

            if func_name in tool_functions:
                try:
                    result = tool_functions[func_name](**func_args)
                    result_str = json.dumps(result, indent=2, default=str)
                except Exception as e:
                    result_str = f"Error calling {func_name}: {str(e)}"
            else:
                result_str = f"Unknown function: {func_name}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str
            })

    return "I've gathered the information. Please ask again to summarize."