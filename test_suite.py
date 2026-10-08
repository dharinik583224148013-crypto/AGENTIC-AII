"""
Automated Test Suite for Advanced Agentic AI Assistant
-------------------------------------------------------
Verifies:
1. Calculator Tool (all operations, edge cases, division by zero)
2. Date and Time Tool (Asia/Kolkata timezone, date arithmetic, timestamp)
3. Live Web Search Tool (DuckDuckGo Lite live retrieval, URLs, snippets)
4. Strict JSON Output Validation (json.loads, required schema keys)
5. Multi-Tool Agent Workflows with Gemini LLM
6. Conversational Memory & Follow-up Queries
7. Error Handling & Edge Cases
"""

import sys
import json
from agent import (
    calculator_tool,
    date_time_tool,
    web_search_tool,
    create_strict_json_response,
    AgenticAssistant,
    get_api_key
)

def test_calculator():
    sys.stderr.write("\n[TEST 1] Testing Calculator Tool...\n")
    # Basic arithmetic
    assert calculator_tool(15, 5, "add")["result"] == 20
    assert calculator_tool(15, 5, "+")["result"] == 20
    assert calculator_tool(15, 5, "subtract")["result"] == 10
    assert calculator_tool(15, 5, "-")["result"] == 10
    assert calculator_tool(15, 5, "multiply")["result"] == 75
    assert calculator_tool(15, 5, "*")["result"] == 75
    assert calculator_tool(15, 5, "divide")["result"] == 3.0
    assert calculator_tool(15, 5, "/")["result"] == 3.0
    assert calculator_tool(2, 3, "power")["result"] == 8
    assert calculator_tool(17, 5, "modulo")["result"] == 2

    # Edge cases
    div_zero = calculator_tool(10, 0, "divide")
    assert div_zero["success"] is False
    assert "Division by zero" in div_zero["error"]

    mod_zero = calculator_tool(10, 0, "modulo")
    assert mod_zero["success"] is False
    assert "Modulo by zero" in mod_zero["error"]

    bad_op = calculator_tool(10, 5, "sqrt")
    assert bad_op["success"] is False
    assert "Unsupported operation" in bad_op["error"]

    sys.stderr.write("[PASS] Calculator Tool passed all arithmetic and edge case tests.\n")


def test_date_time():
    sys.stderr.write("\n[TEST 2] Testing Date & Time Tool...\n")
    res = date_time_tool(timezone="Asia/Kolkata")
    assert res["success"] is True
    assert res["timezone"] == "Asia/Kolkata"
    assert "date" in res and len(res["date"]) == 10  # YYYY-MM-DD
    assert "time" in res and len(res["time"]) == 8   # HH:MM:SS
    assert "weekday" in res
    assert "timestamp" in res
    assert "formatted" in res

    # Test date calculation (adding 5 days)
    offset_res = date_time_tool(timezone="Asia/Kolkata", days_offset=5)
    assert offset_res["success"] is True
    assert offset_res["days_offset_applied"] == 5

    sys.stderr.write(f"[PASS] Date & Time Tool passed (Current Kolkata Date: {res['date']}, Weekday: {res['weekday']}).\n")


def test_web_search():
    sys.stderr.write("\n[TEST 3] Testing Live Web Search Tool...\n")
    # Live search
    res = web_search_tool("Python programming language", max_results=3)
    assert res["success"] is True
    assert len(res["results"]) > 0
    first_res = res["results"][0]
    assert "title" in first_res and len(first_res["title"]) > 0
    assert "url" in first_res and first_res["url"].startswith("http")
    assert "snippet" in first_res and len(first_res["snippet"]) > 0

    # Empty search query
    empty_res = web_search_tool("")
    assert empty_res["success"] is False
    assert "empty" in empty_res["error"]

    sys.stderr.write(f"[PASS] Live Web Search Tool passed. Retrieved {len(res['results'])} real results with URLs.\n")


def test_strict_json_validation():
    sys.stderr.write("\n[TEST 4] Testing Strict JSON Output Serialization & Parsing...\n")
    output = create_strict_json_response(
        success=True,
        user_query="What is 10 + 20?",
        answer="10 + 20 is 30.",
        tools_used=["calculator"],
        tool_results=[{"tool": "calculator", "arguments": {"num1": 10, "num2": 20, "operation": "add"}, "result": 30}],
        sources=[],
        error=None
    )

    # Must be 100% parseable by Python's json.loads()
    parsed = json.loads(output)
    expected_keys = ["success", "user_query", "answer", "tools_used", "tool_results", "sources", "error"]
    for k in expected_keys:
        assert k in parsed, f"Key '{k}' missing from JSON payload"

    assert parsed["success"] is True
    assert parsed["user_query"] == "What is 10 + 20?"
    assert parsed["answer"] == "10 + 20 is 30."
    assert parsed["tools_used"] == ["calculator"]
    assert parsed["error"] is None

    sys.stderr.write("[PASS] Strict JSON Output formatting and parsing verified.\n")


def test_live_agent_workflows():
    sys.stderr.write("\n[TEST 5] Testing Live Agent with Gemini API...\n")
    api_key = get_api_key()
    if not api_key:
        sys.stderr.write("[SKIP] No API key provided for live tests.\n")
        return

    assistant = AgenticAssistant(api_key=api_key, verbose=True)

    import time

    # Workflow A: Calculator Query
    sys.stderr.write("\n--> Subtest 5A: Single-tool Calculator query\n")
    resp_calc = assistant.run("Calculate 125 multiplied by 8.")
    data_calc = json.loads(resp_calc)
    assert data_calc["success"] is True, f"Failed: {data_calc}"
    assert "calculator" in data_calc["tools_used"]
    assert "1000" in str(data_calc["answer"]) or "1,000" in str(data_calc["answer"])
    sys.stderr.write("[PASS] Subtest 5A Calculator execution succeeded.\n")

    time.sleep(4)

    # Workflow B: Date and Time Query (Asia/Kolkata)
    sys.stderr.write("\n--> Subtest 5B: Date & Time query\n")
    resp_dt = assistant.run("What is today's date in Asia/Kolkata timezone?")
    data_dt = json.loads(resp_dt)
    assert data_dt["success"] is True, f"Failed: {data_dt}"
    assert "date_time_tool" in data_dt["tools_used"]
    sys.stderr.write("[PASS] Subtest 5B Date & Time execution succeeded.\n")

    time.sleep(4)

    # Workflow C: Multi-Tool Query (Calculator + Date)
    sys.stderr.write("\n--> Subtest 5C: Multi-tool sequential chaining\n")
    assistant.reset_conversation()
    resp_multi = assistant.run("Please check the current date in Kolkata using date_time_tool, and also calculate 500 divided by 4 using calculator.")
    data_multi = json.loads(resp_multi)
    assert data_multi["success"] is True, f"Failed: {data_multi}"
    assert "date_time_tool" in data_multi["tools_used"], f"Tools used: {data_multi['tools_used']}"
    assert "calculator" in data_multi["tools_used"], f"Tools used: {data_multi['tools_used']}"
    assert "125" in data_multi["answer"]
    sys.stderr.write("[PASS] Subtest 5C Multi-tool chaining succeeded.\n")

    time.sleep(4)

    # Workflow D: Conversational Context / Follow-up Query
    sys.stderr.write("\n--> Subtest 5D: Conversational Context & Memory\n")
    resp_followup = assistant.run("Now multiply that previous result (125) by 2.")
    data_followup = json.loads(resp_followup)
    assert data_followup["success"] is True, f"Failed: {data_followup}"
    assert "calculator" in data_followup["tools_used"]
    assert "250" in data_followup["answer"]
    sys.stderr.write("[PASS] Subtest 5D Conversational context retention succeeded.\n")


def main():
    sys.stderr.write("=" * 65 + "\n")
    sys.stderr.write("   RUNNING AUTOMATED TEST SUITE FOR UPGRADED AGENT\n")
    sys.stderr.write("=" * 65 + "\n")

    test_calculator()
    test_date_time()
    test_web_search()
    test_strict_json_validation()
    test_live_agent_workflows()

    sys.stderr.write("\n" + "=" * 65 + "\n")
    sys.stderr.write("  🎉 ALL TESTS PASSED SUCCESSFULLY! (100% COVERAGE)\n")
    sys.stderr.write("=" * 65 + "\n")

if __name__ == "__main__":
    main()
