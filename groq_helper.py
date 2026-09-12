"""
Groq helper with agentic tool calling.
"""
import os
import json
import inspect
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"


def build_tool_schema(tool_functions: dict):
    """
    Convert Python functions into Groq's tool schema.
    All parameters are optional strings to avoid validation errors.
    """
    tools = []
    for func in tool_functions.values():
        sig = inspect.signature(func)
        properties = {}

        for name, param in sig.parameters.items():
            properties[name] = {
                "type": "string",
                "description": f"Parameter: {name}"
            }

        tools.append({
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": (func.__doc__ or "").strip(),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": []
                }
            }
        })
    return tools


def call_groq_with_tools(
    system_prompt: str,
    user_message: str,
    conversation_history: list,
    tool_functions: dict,
    max_iterations: int = 5
):
    """
    Agentic loop: model decides which tools to call,
    we execute them, feed results back until final answer.
    """
    tools = build_tool_schema(tool_functions)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history[-6:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    messages.append({"role": "user", "content": user_message})

    for _ in range(max_iterations):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.3
            )
        except Exception as e:
            return f"Sorry, technical issue. Please try again. (Error: {str(e)[:200]})"

        response_message = response.choices[0].message

        if not response_message.tool_calls:
            return response_message.content or "I'm here to help with property inquiries."

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

        for tool_call in response_message.tool_calls:
            func_name = tool_call.function.name

            try:
                func_args = json.loads(tool_call.function.arguments)
                # Remove any None values so the function defaults kick in
                func_args = {k: v for k, v in func_args.items() if v is not None}
                print(f"  [TOOL CALL] {func_name}({func_args})")
            except json.JSONDecodeError:
                func_args = {}
                print(f"  [TOOL CALL] {func_name} (failed to parse args)")

            if func_name in tool_functions:
                try:
                    result = tool_functions[func_name](**func_args)
                    if isinstance(result, list):
                        result_str = json.dumps(result, indent=2, default=str)
                        print(f"  [TOOL RESULT] {len(result)} items found")
                    else:
                        result_str = json.dumps(result, indent=2, default=str)
                        print(f"  [TOOL RESULT] {result_str[:120]}")
                except Exception as e:
                    result_str = f"Error calling {func_name}: {str(e)}"
                    print(f"  [TOOL ERROR] {result_str}")
            else:
                result_str = f"Unknown function: {func_name}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str
            })

    return "I've gathered the information. Please ask again to summarize."