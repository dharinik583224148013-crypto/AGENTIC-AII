# 🤖 Advanced Agentic AI Assistant (Premium Edition)

A high-performance, framework-free **Agentic AI Assistant** built using standard Python and the official Google GenAI SDK (`google-genai`).

Reuses your existing Google AI Studio Gemini API integration and delivers autonomous multi-step reasoning across **Calculations**, **Live Web Searches**, and **Date/Time Arithmetic** — while **strictly guaranteeing valid JSON outputs** parseable by `json.loads()`.

---

## 🌟 Key Features

1. **Precision Calculator Tool**:
   - Arithmetic operations: `add` (`+`), `subtract` (`-`), `multiply` (`*`), `divide` (`/`), `power` (`^`), `modulo` (`%`).
   - Handles edge cases such as division and modulo by zero gracefully without crashing.

2. **Live Web Search Tool**:
   - Retrieves real, verifiable current information with `title`, `snippet`, and source `url`.
   - Never fabricates or hallucinates web search results.
   - Dual-engine fallback: DuckDuckGo Lite and live Wikipedia API.

3. **Date and Time Tool**:
   - Timezone-aware date and time resolution with **Asia/Kolkata** as the default timezone.
   - Reports date (`YYYY-MM-DD`), time (`HH:MM:SS`), weekday, timestamp, and ISO format.
   - Computes date arithmetic (e.g., adding or subtracting days).

4. **Autonomous Agentic Orchestration**:
   - The Gemini LLM acts as the intelligent reasoner, deciding when and which tools to call.
   - Supports **multi-tool sequential chaining** (e.g., query date, perform calculation, and search the web in a single turn).

5. **Strict JSON Output Guarantee**:
   - Standard output (`stdout`) produces **only valid, raw JSON** without Markdown code fences, raw text, or trailing messages.
   - All diagnostic logs and tool execution traces are cleanly directed to `stderr`.
   - Every response is validated using `json.loads()` and contains the required schema:
     ```json
     {
       "success": true,
       "user_query": "...",
       "answer": "...",
       "tools_used": ["..."],
       "tool_results": [...],
       "sources": [...],
       "error": null
     }
     ```

6. **Conversational Memory**:
   - Retains context across multi-turn interactions for follow-up questions.
   - Supports in-session memory reset (`reset` command).

---

## 📁 Project Directory Structure

Located in **`C:\Users\Admin\Downloads\vichu3`**:
- **`agent.py`**: The complete Agentic Assistant engine, tool registry, and CLI.
- **`test_suite.py`**: Comprehensive automated test suite verifying all tools and workflows.
- **`README.md`**: Architectural documentation and usage guide.

---

## 🚀 Running the Assistant

### Step 1: Open PowerShell
```powershell
cd C:\Users\Admin\Downloads\vichu3
```

### Step 2: Run the Assistant
```powershell
python agent.py
```

### Step 3: Example Queries to Try

- **Math Calculation**:
  > *"Calculate 1450 divided by 25, then multiply the result by 6."*

- **Date and Time**:
  > *"What is the current time and weekday in Kolkata, and what date will it be 14 days from now?"*

- **Live Web Search**:
  > *"Search the web for the latest developments in artificial intelligence."*

- **Multi-Tool Combined Workflow**:
  > *"What is today's date in Kolkata, and calculate 2 to the power of 10?"*

- **Contextual Follow-up**:
  > *"Now take that previous result and divide it by 4."*

---

## 🧪 Running the Test Suite

Run all automated unit and integration tests:
```powershell
python test_suite.py
```
