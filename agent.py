"""
Advanced Agentic AI Assistant
------------------------------
A premium-quality, framework-free Agentic AI Assistant built with standard Python
and the official Google GenAI SDK (google-genai).

Features:
1. Calculator Tool: Precision arithmetic operations (+, -, *, /, power, modulo).
2. Live Web Search Tool: Real web search via DuckDuckGo Lite returning titles, snippets, and URLs.
3. Date & Time Tool: Real-time timezone-aware date, time, weekday, timestamp, and date calculations (Asia/Kolkata default).
4. Autonomous Multi-Step Reasoning: Gemini LLM function-calling with sequential tool chaining.
5. Strict JSON Output: Every final response is guaranteed valid JSON parseable by json.loads().
6. Conversational Memory: Retains multi-turn conversation history for contextual follow-ups.
7. Clean Separation: Tool logs and debug traces are directed to stderr; stdout contains ONLY valid JSON.
"""

import os
import sys
import json
import re
import time
import datetime
import zoneinfo
from typing import Any, Dict, List, Optional, Tuple
from html.parser import HTMLParser
from urllib.parse import unquote

# Optional requests library for live web search
import requests

from google import genai
from google.genai import types

# Configure UTF-8 on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ============================================================================
# 1. CONFIGURATION & API KEY
# ============================================================================
GEMINI_API_KEY: str = "AQ.Ab8RN6Kl3Acf4RJWcs8ynDBdbgmB_t4N_FFQ17pWshbu0_vqFQ"
DEFAULT_MODEL: str = "gemini-3.8-flash"
FALLBACK_MODELS: List[str] = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-flash-latest"
]
DEFAULT_TIMEZONE: str = "Asia/Kolkata"
MAX_AGENT_ITERATIONS: int = 8

def get_api_key() -> str:
    """Retrieve Gemini API key from variable or environment."""
    if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("PASTE_YOUR"):
        return GEMINI_API_KEY.strip()
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    return ""


# ============================================================================
# 2. TOOL 1: CALCULATOR TOOL
# ============================================================================
def calculator_tool(num1: float, num2: float, operation: str) -> Dict[str, Any]:
    """
    Performs arithmetic operations on two numbers.
    Supported operations: add (+), subtract (-), multiply (*), divide (/), power (^), modulo (%).
    """
    op = str(operation).strip().lower()
    try:
        n1 = float(num1)
        n2 = float(num2)
    except (ValueError, TypeError) as exc:
        return {
            "success": False,
            "error": f"Invalid numerical arguments: num1='{num1}', num2='{num2}'. {str(exc)}"
        }

    try:
        if op in ["add", "+", "plus", "addition"]:
            result = n1 + n2
            symbol = "+"
        elif op in ["subtract", "-", "minus", "subtraction"]:
            result = n1 - n2
            symbol = "-"
        elif op in ["multiply", "*", "into", "times", "multiplication"]:
            result = n1 * n2
            symbol = "*"
        elif op in ["divide", "/", "division", "by"]:
            if n2 == 0:
                return {
                    "success": False,
                    "error": "Division by zero is undefined."
                }
            result = n1 / n2
            symbol = "/"
        elif op in ["power", "**", "^", "pow", "exponent"]:
            result = n1 ** n2
            symbol = "^"
        elif op in ["modulo", "%", "mod", "remainder"]:
            if n2 == 0:
                return {
                    "success": False,
                    "error": "Modulo by zero is undefined."
                }
            result = n1 % n2
            symbol = "%"
        else:
            return {
                "success": False,
                "error": f"Unsupported operation '{operation}'. Supported: add (+), subtract (-), multiply (*), divide (/), power (^), modulo (%)."
            }

        return {
            "success": True,
            "operation": op,
            "symbol": symbol,
            "num1": n1,
            "num2": n2,
            "result": result
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Calculation error: {str(exc)}"
        }


# ============================================================================
# 3. TOOL 2: DATE AND TIME TOOL (Asia/Kolkata default)
# ============================================================================
def date_time_tool(
    action: str = "current_time",
    timezone: str = DEFAULT_TIMEZONE,
    days_offset: int = 0
) -> Dict[str, Any]:
    """
    Provides real-time date and time details, timezone conversions,
    and basic date arithmetic (adding/subtracting days).
    """
    tz_str = timezone.strip() if timezone else DEFAULT_TIMEZONE
    try:
        tz = zoneinfo.ZoneInfo(tz_str)
    except Exception:
        # Fallback to default timezone if unrecognized
        tz = zoneinfo.ZoneInfo(DEFAULT_TIMEZONE)
        tz_str = DEFAULT_TIMEZONE

    try:
        now = datetime.datetime.now(tz)
        offset = int(days_offset) if days_offset else 0
        target = now + datetime.timedelta(days=offset)

        return {
            "success": True,
            "action": action,
            "timezone": tz_str,
            "date": target.strftime("%Y-%m-%d"),
            "time": target.strftime("%H:%M:%S"),
            "weekday": target.strftime("%A"),
            "iso_format": target.isoformat(),
            "timestamp": target.timestamp(),
            "days_offset_applied": offset,
            "formatted": target.strftime("%A, %d %B %Y, %I:%M:%S %p %Z")
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Date/time resolution error: {str(exc)}"
        }


# ============================================================================
# 4. TOOL 3: LIVE WEB SEARCH TOOL (DuckDuckGo Lite)
# ============================================================================
class _DDGLiteParser(HTMLParser):
    """HTML parser to extract clean titles, urls, and snippets from DuckDuckGo Lite."""
    def __init__(self):
        super().__init__()
        self.results: List[Dict[str, str]] = []
        self.current_result: Optional[Dict[str, str]] = None
        self.in_link: bool = False
        self.in_snippet: bool = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        attrs_dict = dict(attrs)
        if tag == "a" and "result-link" in attrs_dict.get("class", ""):
            href = attrs_dict.get("href", "")
            # Decode DuckDuckGo redirected URL
            if "uddg=" in href:
                match = re.search(r"uddg=([^&]+)", href)
                if match:
                    href = unquote(match.group(1))
            self.current_result = {"title": "", "url": href, "snippet": ""}
            self.in_link = True
        elif tag == "td" and "result-snippet" in attrs_dict.get("class", ""):
            self.in_snippet = True

    def handle_endtag(self, tag: str):
        if tag == "a" and self.in_link:
            self.in_link = False
        elif tag == "td" and self.in_snippet:
            self.in_snippet = False
            if self.current_result:
                title = self.current_result["title"].strip()
                url = self.current_result["url"].strip()
                snippet = re.sub(r"\s+", " ", self.current_result["snippet"]).strip()
                if title and url:
                    self.results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
                self.current_result = None

    def handle_data(self, data: str):
        if self.in_link and self.current_result:
            self.current_result["title"] += data
        elif self.in_snippet and self.current_result:
            self.current_result["snippet"] += data + " "


def web_search_tool(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Searches the live web for real, current information using DuckDuckGo Lite.
    Returns titles, snippets, and source URLs. Never fabricates results.
    """
    clean_query = str(query).strip()
    if not clean_query:
        return {
            "success": False,
            "error": "Search query cannot be empty.",
            "results": []
        }

    limit = max(1, min(int(max_results) if max_results else 5, 10))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    extracted = []
    # Primary: DuckDuckGo Lite Search
    try:
        resp = requests.post(
            "https://lite.duckduckgo.com/lite/",
            data={"q": clean_query},
            headers=headers,
            timeout=8
        )
        if resp.status_code == 200:
            parser = _DDGLiteParser()
            parser.feed(resp.text)
            extracted = parser.results[:limit]
    except Exception:
        pass

    # Reliable Fallback: Live Wikipedia Knowledge API (guaranteed real information, titles, URLs, snippets)
    if not extracted:
        try:
            wiki_headers = {"User-Agent": "AgenticAssistant/1.0 (academic-ai-practice)"}
            w_resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": clean_query,
                    "format": "json",
                    "utf8": 1
                },
                headers=wiki_headers,
                timeout=8
            )
            if w_resp.status_code == 200:
                wiki_data = w_resp.json()
                for item in wiki_data.get("query", {}).get("search", [])[:limit]:
                    raw_snippet = item.get("snippet", "")
                    clean_snip = re.sub(r"<[^>]+>", "", raw_snippet).strip()
                    title = item.get("title", "")
                    page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                    extracted.append({
                        "title": title,
                        "url": page_url,
                        "snippet": clean_snip
                    })
        except Exception:
            pass

    if not extracted:
        return {
            "success": True,
            "query": clean_query,
            "results": [],
            "message": "No search results found for the specified query."
        }

    return {
        "success": True,
        "query": clean_query,
        "results": extracted
    }


# ============================================================================
# 5. TOOL REGISTRY & JSON SCHEMAS
# ============================================================================
TOOL_REGISTRY = {
    "calculator": calculator_tool,
    "date_time_tool": date_time_tool,
    "web_search": web_search_tool
}

ALL_TOOLS_JSON_SCHEMA = [
    {
        "name": "calculator",
        "description": "Performs mathematical arithmetic operations on two numbers: add, subtract, multiply, divide, power, modulo.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "num1": {
                    "type": "NUMBER",
                    "description": "The first number (first operand)."
                },
                "num2": {
                    "type": "NUMBER",
                    "description": "The second number (second operand)."
                },
                "operation": {
                    "type": "STRING",
                    "description": "The operation to perform: 'add', 'subtract', 'multiply', 'divide', 'power', or 'modulo'.",
                    "enum": ["add", "subtract", "multiply", "divide", "power", "modulo"]
                }
            },
            "required": ["num1", "num2", "operation"]
        }
    },
    {
        "name": "date_time_tool",
        "description": "Provides current date, time, weekday, timezone, timestamp, and basic date calculations (e.g. adding or subtracting days). Default timezone is Asia/Kolkata.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "The action: 'current_time' (get current date/time) or 'calculate_date' (perform date calculation).",
                    "enum": ["current_time", "calculate_date"]
                },
                "timezone": {
                    "type": "STRING",
                    "description": "Timezone name (e.g., 'Asia/Kolkata', 'UTC', 'America/New_York'). Defaults to 'Asia/Kolkata'."
                },
                "days_offset": {
                    "type": "INTEGER",
                    "description": "Number of days to add (positive number) or subtract (negative number) from current date."
                }
            }
        }
    },
    {
        "name": "web_search",
        "description": "Retrieves real, current information from the live internet. Returns titles, snippets, and source URLs. Never fabricates search results.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "The precise web search query."
                },
                "max_results": {
                    "type": "INTEGER",
                    "description": "Maximum number of search results to retrieve (default: 5)."
                }
            },
            "required": ["query"]
        }
    }
]

def build_gemini_config() -> types.GenerateContentConfig:
    """Creates Gemini SDK config with all 3 function declarations."""
    function_declarations = [
        types.FunctionDeclaration(**tool_def) for tool_def in ALL_TOOLS_JSON_SCHEMA
    ]
    tool = types.Tool(function_declarations=function_declarations)
    return types.GenerateContentConfig(
        tools=[tool],
        temperature=0.0
    )


# ============================================================================
# 6. RESPONSE FORMATTER & VALIDATOR (STRICT JSON OUTPUT)
# ============================================================================
def create_strict_json_response(
    success: bool,
    user_query: str,
    answer: Optional[str],
    tools_used: List[str],
    tool_results: List[Dict[str, Any]],
    sources: List[Dict[str, str]],
    error: Optional[str] = None
) -> str:
    """
    Constructs, validates, and serializes the strictly structured JSON response.
    Guarantees that json.loads() succeeds without markdown code fences or raw text.
    """
    response_payload = {
        "success": bool(success),
        "user_query": user_query,
        "answer": answer if answer is not None else "",
        "tools_used": list(dict.fromkeys(tools_used)),  # Unique ordered list
        "tool_results": tool_results,
        "sources": sources,
        "error": error
    }

    # Serialize to JSON
    serialized = json.dumps(response_payload, indent=2, ensure_ascii=False)

    # Double validation: Ensure it parses cleanly with json.loads
    try:
        parsed = json.loads(serialized)
        for req_field in ["success", "user_query", "answer", "tools_used", "tool_results", "sources", "error"]:
            if req_field not in parsed:
                raise ValueError(f"Missing required response field: '{req_field}'")
    except Exception as val_err:
        fallback = {
            "success": False,
            "user_query": user_query,
            "answer": None,
            "tools_used": tools_used,
            "tool_results": tool_results,
            "sources": sources,
            "error": f"JSON output validation failed: {str(val_err)}"
        }
        return json.dumps(fallback, indent=2, ensure_ascii=False)

    return serialized


# ============================================================================
# 7. AGENTIC AI ASSISTANT CORE CLASS
# ============================================================================
class AgenticAssistant:
    """
    Autonomous Agentic AI Assistant with conversational memory,
    multi-step tool orchestration, and strict JSON output formatting.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        verbose: bool = False
    ):
        self.api_key = api_key or get_api_key()
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY or configure in code.")
        
        self.model = model
        self.verbose = verbose
        self.client = genai.Client(api_key=self.api_key)
        self.config = build_gemini_config()
        self.history: List[types.Content] = []

    def _log(self, message: str):
        """Logs debugging info strictly to stderr to keep stdout clean JSON."""
        if self.verbose:
            sys.stderr.write(f"[AGENT] {message}\n")
            sys.stderr.flush()

    def reset_conversation(self):
        """Clears conversational memory."""
        self.history.clear()
        self._log("Conversational memory cleared.")

    def execute_local_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Invokes a local tool safely with error containment."""
        if tool_name not in TOOL_REGISTRY:
            return {"success": False, "error": f"Tool '{tool_name}' is not recognized."}

        func = TOOL_REGISTRY[tool_name]
        try:
            return func(**args)
        except Exception as exc:
            return {"success": False, "error": f"Exception executing {tool_name}: {str(exc)}"}

    def run(self, user_query: str) -> str:
        """
        Executes the autonomous agentic loop:
        1. Appends user query to conversation history.
        2. Queries LLM with JSON tool declarations.
        3. If model requests tool call(s), executes them locally.
        4. Appends results to history and repeats until final answer.
        5. Validates and returns strictly structured JSON.
        """
        clean_query = user_query.strip()
        if not clean_query:
            return create_strict_json_response(
                success=False,
                user_query=user_query,
                answer="",
                tools_used=[],
                tool_results=[],
                sources=[],
                error="Query cannot be empty."
            )

        self._log(f"Received query: '{clean_query}'")

        # Track tools and sources used in this specific turn
        turn_tools_used: List[str] = []
        turn_tool_results: List[Dict[str, Any]] = []
        turn_sources: List[Dict[str, str]] = []

        # Append new user message to ongoing conversational history
        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=clean_query)]
        )
        self.history.append(user_content)

        iteration = 0
        final_answer = ""

        while iteration < MAX_AGENT_ITERATIONS:
            iteration += 1
            self._log(f"Iteration {iteration}/{MAX_AGENT_ITERATIONS} calling Gemini LLM...")

            response = None
            for attempt in range(len(FALLBACK_MODELS)):
                current_model = FALLBACK_MODELS[attempt]
                try:
                    response = self.client.models.generate_content(
                        model=current_model,
                        contents=self.history,
                        config=self.config
                    )
                    self.model = current_model
                    break
                except Exception as api_err:
                    err_msg = str(api_err)
                    is_transient = any(k in err_msg for k in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500", "INTERNAL"])
                    if is_transient:
                        match = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s", err_msg)
                        if match and float(match.group(1)) <= 10:
                            wait_sec = float(match.group(1)) + 1.0
                            self._log(f"Rate limit. Waiting {wait_sec:.1f}s...")
                            time.sleep(wait_sec)
                            try:
                                response = self.client.models.generate_content(
                                    model=current_model,
                                    contents=self.history,
                                    config=self.config
                                )
                                self.model = current_model
                                break
                            except Exception:
                                pass
                        elif "503" in err_msg or "UNAVAILABLE" in err_msg:
                            self._log(f"Model '{current_model}' temporarily unavailable (503). Retrying after 2s...")
                            time.sleep(2)
                            try:
                                response = self.client.models.generate_content(
                                    model=current_model,
                                    contents=self.history,
                                    config=self.config
                                )
                                self.model = current_model
                                break
                            except Exception:
                                pass
                        if attempt + 1 < len(FALLBACK_MODELS):
                            next_model = FALLBACK_MODELS[attempt + 1]
                            self._log(f"Failing over from '{current_model}' to '{next_model}'...")
                            time.sleep(1)
                            continue
                    self._log(f"API Error: {err_msg}")
                    return create_strict_json_response(
                        success=False,
                        user_query=clean_query,
                        answer="",
                        tools_used=turn_tools_used,
                        tool_results=turn_tool_results,
                        sources=turn_sources,
                        error=f"Gemini API Error: {err_msg}"
                    )

            candidate = response.candidates[0] if response.candidates else None
            if not candidate or not candidate.content:
                return create_strict_json_response(
                    success=False,
                    user_query=clean_query,
                    answer="",
                    tools_used=turn_tools_used,
                    tool_results=turn_tool_results,
                    sources=turn_sources,
                    error="No response content returned by Gemini model."
                )

            # Record model output into conversation history
            self.history.append(candidate.content)

            # Check if model requested tool call(s)
            tool_calls = [
                part.function_call for part in candidate.content.parts if part.function_call
            ]

            if not tool_calls:
                # Model concluded reasoning and provided final text answer
                final_answer = response.text or ""
                self._log("Model generated final response.")
                break

            # Execute requested tool calls
            tool_response_parts: List[types.Part] = []
            for fc in tool_calls:
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}
                turn_tools_used.append(tool_name)

                self._log(f"Tool call requested: {tool_name}({tool_args})")
                execution_result = self.execute_local_tool(tool_name, tool_args)
                self._log(f"Tool executed. Result: {execution_result}")

                # Save execution record
                turn_tool_results.append({
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": execution_result
                })

                # Extract sources if web search was called
                if tool_name == "web_search" and isinstance(execution_result, dict):
                    for item in execution_result.get("results", []):
                        if isinstance(item, dict) and "url" in item:
                            turn_sources.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("snippet", "")
                            })

                # Create tool response part for the model
                part = types.Part.from_function_response(
                    name=tool_name,
                    response={"result": execution_result}
                )
                tool_response_parts.append(part)

            # Return tool output to LLM history
            tool_content = types.Content(role="user", parts=tool_response_parts)
            self.history.append(tool_content)

        if iteration >= MAX_AGENT_ITERATIONS and not final_answer:
            return create_strict_json_response(
                success=False,
                user_query=clean_query,
                answer="",
                tools_used=turn_tools_used,
                tool_results=turn_tool_results,
                sources=turn_sources,
                error="Agent reached maximum reasoning iteration limit without resolving query."
            )

        # Produce and validate final JSON output
        return create_strict_json_response(
            success=True,
            user_query=clean_query,
            answer=final_answer.strip(),
            tools_used=turn_tools_used,
            tool_results=turn_tool_results,
            sources=turn_sources,
            error=None
        )


# ============================================================================
# 8. INTERACTIVE CLI RUNNER
# ============================================================================
def run_cli():
    """Interactive Command Line Interface for the Agentic Assistant."""
    api_key = get_api_key()
    if not api_key:
        sys.stderr.write("ERROR: Gemini API Key not found! Please configure GEMINI_API_KEY.\n")
        sys.exit(1)

    # Initialize assistant with verbose logs enabled to stderr
    assistant = AgenticAssistant(api_key=api_key, verbose=True)

    sys.stderr.write("=" * 65 + "\n")
    sys.stderr.write("    ADVANCED AGENTIC AI ASSISTANT (STRICT JSON OUTPUT)\n")
    sys.stderr.write("=" * 65 + "\n")
    sys.stderr.write(f"Model: {DEFAULT_MODEL}\n")
    sys.stderr.write("Tools: [calculator, date_time_tool, web_search]\n")
    sys.stderr.write("Default Timezone: Asia/Kolkata\n")
    sys.stderr.write("Type 'exit' to quit, 'reset' to clear conversation memory.\n")
    sys.stderr.write("=" * 65 + "\n\n")

    while True:
        try:
            sys.stderr.write("\nEnter Query: ")
            sys.stderr.flush()
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            sys.stderr.write("\nExiting Assistant.\n")
            break

        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "q"]:
            sys.stderr.write("Exiting Assistant. Goodbye!\n")
            break
        if user_input.lower() == "reset":
            assistant.reset_conversation()
            sys.stderr.write("Conversation memory reset successfully.\n")
            continue

        # Run assistant and output STRICT JSON to stdout
        json_output = assistant.run(user_input)
        print(json_output)
        sys.stdout.flush()

if __name__ == "__main__":
    run_cli()
