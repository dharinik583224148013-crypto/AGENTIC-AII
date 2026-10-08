"""
Calculator Agent for Agentic AI Practice
-----------------------------------------
Performs arithmetic operations using a unified 'calculator' tool in JSON format.
Takes 2 input numbers and 1 operation from the user, routes them through the
Gemini LLM (Reasoner), executes the tool with JSON arguments, and returns the result.

Built with standard Python and the official Google GenAI SDK (google-genai).
No external frameworks (no LangChain, no CrewAI, no AutoGen).
"""

import os
import sys
import json
from typing import Any, Dict
from google import genai
from google.genai import types

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ============================================================================
# 1. API KEY & MODEL CONFIGURATION
# ============================================================================
# Insert your Gemini API key here, or set the GEMINI_API_KEY environment variable.
GEMINI_API_KEY: str = "AQ.Ab8RN6Kl3Acf4RJWcs8ynDBdbgmB_t4N_FFQ17pWshbu0_vqFQ"

# Model used for tool calling and reasoning
DEFAULT_MODEL: str = "gemini-3.5-flash"

def get_api_key() -> str:
    """Retrieve API key from code variable or environment variable."""
    if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("PASTE_YOUR"):
        return GEMINI_API_KEY.strip()
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    return ""


# ============================================================================
# 2. PYTHON CALCULATOR TOOL IMPLEMENTATION
# ============================================================================
def calculator(num1: float, num2: float, operation: str) -> float | str:
    """
    Performs arithmetic calculation given 2 input numbers and 1 operation.
    Supported operations: add (+), subtract (-), multiply (*), divide (/).
    """
    op = operation.strip().lower()

    if op in ["add", "+", "plus", "addition"]:
        return num1 + num2
    elif op in ["subtract", "-", "minus", "subtraction"]:
        return num1 - num2
    elif op in ["multiply", "*", "into", "times", "multiplication"]:
        return num1 * num2
    elif op in ["divide", "/", "division", "by"]:
        if num2 == 0:
            return "Error: Division by zero is undefined."
        return num1 / num2
    else:
        return f"Error: Unsupported operation '{operation}'. Supported operations: add (+), subtract (-), multiply (*), divide (/)."

# Tool registry mapping tool name to the Python function
TOOL_REGISTRY = {
    "calculator": calculator
}


# ============================================================================
# 3. JSON TOOL SPECIFICATION (Gemini / OpenAPI Schema)
# ============================================================================
# This JSON schema informs the LLM that the calculator tool requires
# 2 inputs (num1, num2) and 1 operation.
CALCULATOR_TOOL_JSON = {
    "name": "calculator",
    "description": "Performs an arithmetic operation (+, -, *, /) on two numbers given 2 input numbers and 1 operation.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "num1": {
                "type": "NUMBER",
                "description": "The first input number (first operand)."
            },
            "num2": {
                "type": "NUMBER",
                "description": "The second input number (second operand)."
            },
            "operation": {
                "type": "STRING",
                "description": "The arithmetic operation: 'add', 'subtract', 'multiply', or 'divide'.",
                "enum": ["add", "subtract", "multiply", "divide"]
            }
        },
        "required": ["num1", "num2", "operation"]
    }
}

def build_gemini_tools_config() -> types.GenerateContentConfig:
    """Converts the JSON tool schema into Gemini SDK Tool configuration."""
    function_declaration = types.FunctionDeclaration(**CALCULATOR_TOOL_JSON)
    tool = types.Tool(function_declarations=[function_declaration])
    return types.GenerateContentConfig(
        tools=[tool],
        temperature=0.0  # Zero temperature for deterministic, accurate tool calling
    )


# ============================================================================
# 4. TOOL DISPATCHER & AGENTIC LOOP
# ============================================================================
def execute_tool(func_name: str, func_args: Dict[str, Any]) -> Any:
    """
    Dispatcher: Takes tool name and JSON arguments supplied by LLM,
    runs the Python function, and returns the result.
    """
    if func_name not in TOOL_REGISTRY:
        return f"Error: Unknown tool '{func_name}'."
    
    func = TOOL_REGISTRY[func_name]
    try:
        num1 = float(func_args.get("num1", 0))
        num2 = float(func_args.get("num2", 0))
        operation = str(func_args.get("operation", ""))
        return func(num1=num1, num2=num2, operation=operation)
    except Exception as exc:
        return f"Error executing {func_name}: {str(exc)}"


def run_agent(
    user_prompt: str,
    client: genai.Client,
    model: str = DEFAULT_MODEL,
    max_iterations: int = 5
) -> str:
    """
    Executes the Agentic Loop:
    1. Sends user input to LLM with the JSON calculator tool.
    2. Model decides to call the tool and produces JSON arguments: {num1, num2, operation}.
    3. Agent executes the Python calculator tool locally.
    4. Agent sends the JSON result back to the LLM.
    5. LLM generates the final answer.
    """
    print("\n" + "=" * 65)
    print(f"[AGENT STARTED] User Request: \"{user_prompt}\"")
    print("=" * 65)

    config = build_gemini_tools_config()
    
    # Initialize conversation history with user prompt
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt)]
        )
    ]

    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- [Iteration {iteration}/{max_iterations}] Calling LLM ---")

        # Step A: Generate content from LLM
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
        except Exception as err:
            print(f"\n[API ERROR]: {err}")
            return f"Agent Error: {err}"

        candidate = response.candidates[0] if response.candidates else None
        if not candidate or not candidate.content:
            print("[ERROR] No response candidate received from model.")
            return "Agent Error: No response received."

        # Append model response to conversation history
        contents.append(candidate.content)

        # Step B: Check if model decided to call tools
        tool_call_parts = [
            part for part in candidate.content.parts if part.function_call
        ]

        if not tool_call_parts:
            # No tool call means model produced the final answer
            final_text = response.text if response.text else "No output text provided."
            print(f"\n[FINAL ANSWER]:\n{final_text}")
            print("=" * 65)
            return final_text

        # Step C: Model requested the calculator tool call
        tool_response_parts = []
        for part in tool_call_parts:
            func_call = part.function_call
            tool_name = func_call.name
            tool_args = func_call.args or {}

            print(f"[TOOL CALL REQUESTED BY LLM]:")
            print(f"   Tool Name : {tool_name}")
            print(f"   Arguments : {json.dumps(tool_args)}")

            # Execute the calculator tool locally
            tool_result = execute_tool(tool_name, tool_args)
            print(f"[TOOL EXECUTED]:")
            print(f"   Result    : {tool_result}")

            # Send result back as JSON
            response_payload = {"result": tool_result}
            resp_part = types.Part.from_function_response(
                name=tool_name,
                response=response_payload
            )
            tool_response_parts.append(resp_part)

        # Step D: Append tool results to conversation history and loop back to LLM
        tool_content = types.Content(
            role="user",
            parts=tool_response_parts
        )
        contents.append(tool_content)
        print("[SENT TOOL RESULT BACK TO LLM]")

    print("[MAX ITERATIONS REACHED]: Agent stopped.")
    return "Agent stopped: Reached maximum reasoning iterations."


# ============================================================================
# 5. USER INPUT HANDLER & CLI
# ============================================================================
def prompt_user_for_operation() -> tuple[float, float, str] | None:
    """Gets 2 numbers and 1 operation directly from user input."""
    print("\n" + "-" * 50)
    print("  PLEASE PROVIDE 2 INPUT NUMBERS AND 1 OPERATION")
    print("-" * 50)
    try:
        raw_num1 = input("Enter first number (num1): ").strip()
        num1 = float(raw_num1)

        raw_num2 = input("Enter second number (num2): ").strip()
        num2 = float(raw_num2)

        print("\nAvailable operations: add (+), subtract (-), multiply (*), divide (/)")
        operation = input("Enter operation: ").strip()

        if not operation:
            print("[ERROR] Operation cannot be empty.")
            return None

        return num1, num2, operation
    except ValueError:
        print("[ERROR] Invalid number entered. Please enter numeric values.")
        return None


def main():
    api_key = get_api_key()
    if not api_key:
        print("\n" + "!" * 65)
        print("ERROR: Gemini API Key not found!")
        print("Please insert your API key in 'calculator_agent.py' (Line 30)")
        print("!" * 65 + "\n")
        return

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    print("\n" + "=" * 65)
    print("   ARITHMETIC CALCULATOR AGENT (2 INPUTS + 1 OPERATION)")
    print("=" * 65)
    print(f"Model: {DEFAULT_MODEL}")
    print("JSON Tool: 'calculator' (inputs: num1, num2, operation)")
    print("=" * 65)

    while True:
        print("\nOptions:")
        print("1. Perform Arithmetic Operation (Enter 2 numbers & 1 operation)")
        print("2. Enter Free-text Math Query (e.g., 'Multiply 15 by 8')")
        print("3. Exit")

        choice = input("\nEnter choice (1, 2, or 3): ").strip()

        if choice == "1":
            user_inputs = prompt_user_for_operation()
            if user_inputs:
                num1, num2, operation = user_inputs
                # Construct query for the LLM agent
                agent_prompt = f"Please perform the arithmetic operation '{operation}' on the two numbers: num1 = {num1} and num2 = {num2}."
                run_agent(agent_prompt, client=client)
        elif choice == "2":
            query = input("\nEnter math question: ").strip()
            if query:
                run_agent(query, client=client)
        elif choice == "3":
            print("Exiting calculator agent. Goodbye!")
            break
        else:
            print("Invalid option. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
