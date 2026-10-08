"""
Unit & Integration Test for Unified Calculator Tool (2 Inputs + 1 Operation)
----------------------------------------------------------------------------
Verifies:
1. Python calculator tool execution with all operations (add, subtract, multiply, divide).
2. JSON tool schema validation with Gemini SDK types.
3. Dispatcher execution with simulated LLM tool calls.
"""

from calculator_agent import (
    calculator,
    execute_tool,
    build_gemini_tools_config,
    CALCULATOR_TOOL_JSON,
    TOOL_REGISTRY
)

def run_tests():
    print("Testing Calculator Agent Components (2 Inputs + 1 Operation)...\n")

    # 1. Test basic Python function
    assert calculator(10, 5, "add") == 15, "add failed"
    assert calculator(10, 5, "+") == 15, "add symbol failed"
    assert calculator(10, 5, "subtract") == 5, "subtract failed"
    assert calculator(10, 5, "-") == 5, "subtract symbol failed"
    assert calculator(10, 5, "multiply") == 50, "multiply failed"
    assert calculator(10, 5, "*") == 50, "multiply symbol failed"
    assert calculator(10, 5, "divide") == 2.0, "divide failed"
    assert calculator(10, 5, "/") == 2.0, "divide symbol failed"
    assert "Error" in str(calculator(10, 0, "divide")), "divide by zero failed"
    print("[PASS] Python calculator function verified for all operations (+, -, *, /).")

    # 2. Test JSON Schema and Gemini SDK config
    config = build_gemini_tools_config()
    assert config.tools is not None, "tools config failed"
    print("[PASS] JSON tool schema successfully compiled into Gemini SDK configuration.")

    # 3. Test tool dispatcher with simulated LLM JSON calls (2 inputs + 1 operation)
    simulated_calls = [
        ("calculator", {"num1": 42.5, "num2": 17.5, "operation": "add"}, 60.0),
        ("calculator", {"num1": 100, "num2": 35, "operation": "subtract"}, 65.0),
        ("calculator", {"num1": 8, "num2": 9, "operation": "multiply"}, 72.0),
        ("calculator", {"num1": 100, "num2": 4, "operation": "divide"}, 25.0),
    ]

    for tool_name, args, expected in simulated_calls:
        res = execute_tool(tool_name, args)
        assert res == expected, f"Tool call failed: expected {expected}, got {res}"
        print(f"[PASS] Simulated LLM JSON call: {tool_name}(num1={args['num1']}, num2={args['num2']}, op='{args['operation']}') -> {res}")

    print("\n[SUCCESS] All local tests passed! 2 inputs + 1 operation tool is 100% verified.")

if __name__ == "__main__":
    run_tests()
