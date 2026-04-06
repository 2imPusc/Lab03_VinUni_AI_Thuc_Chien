# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đỗ Minh Phúc
- **Student ID**: 2A2026000339
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| Module                                                     | Mô tả đóng góp                                                                                      |
| :--------------------------------------------------------- | :-------------------------------------------------------------------------------------------------- |
| `src/agent/agent.py`                                       | Xây dựng `ReActAgent` class: vòng lặp ReAct, parse Action/Final Answer, tích hợp telemetry          |
| `src/core/llm_provider.py` + `src/core/openai_provider.py` | Thêm tham số `stop` xuyên suốt interface → implementation để agent kiểm soát được điểm dừng của LLM |
| `chat.py`                                                  | Xây dựng chat interface                                                                             |

### Code Highlights

**Fix Bug #1 — Stop Sequences (commit `8d3bdb5`, `4b48473`)**

Thêm tham số `stop` xuyên suốt 3 lớp: agent → abstract interface → OpenAI API.

```python
# src/agent/agent.py
result = self.llm.generate(
    current_prompt,
    system_prompt=self.get_system_prompt(),
    stop=["\nObservation:"],   # ← buộc LLM dừng, agent tự inject Observation thật
)

# src/core/llm_provider.py — cập nhật abstract method
def generate(self, prompt: str, system_prompt: Optional[str] = None,
             stop: Optional[List[str]] = None) -> Dict[str, Any]: ...

# src/core/openai_provider.py — truyền xuống OpenAI API
response = self.client.chat.completions.create(
    model=self.model_name,
    messages=messages,
    stop=stop,
)
```

**Fix `__main__` guard (commit `ed39806`)**

Teammate thêm `main()` ở cuối `agent.py` khiến mọi `import agent` đều tự chạy agent — `chat.py` bị trigger ngay khi import:

```python
# Trước (bug):
main()

# Sau (fix):
if __name__ == "__main__":
    main()
```

**Chat Interface (`chat.py`)**

```python
agent = ReActAgent(llm, tools=tool_defs, max_steps=7)
agent.tool_executor = execute_tool   # ← dependency injection, tách tool khỏi agent

while True:
    user_input = input("\n[BẠN] ").strip()
    if user_input.lower() in ("quit", "exit", "thoát"):
        break
    answer = agent.run(user_input)
    print(f"[AGENT]\n{answer}")
```

### Cách code tương tác với ReAct loop

Mỗi iteration của vòng lặp `while steps < self.max_steps`, agent gọi `llm.generate()` với `stop=["\nObservation:"]`. LLM sinh `Thought` + `Action`, dừng ngay trước `\nObservation:`. Agent parse `Action`, gọi tool thật, nhận kết quả, rồi tự inject `Observation: <kết quả>` vào prompt trước khi gọi LLM lần tiếp theo — đảm bảo mọi Observation đều đến từ tool thực, không phải từ model.

---

## II. Debugging Case Study (10 Points)

### Bug Hallucinated ReAct Loop

**Problem Description**: Agent trả lời đầy đủ, trông có vẻ hợp lý, nhưng thực tế toàn bộ dữ liệu là bịa. Không có exception, không có error message — rất khó phát hiện nếu không có telemetry.

**Log Source** — Quá trình phát hiện qua `logs/2026-04-06.log`:

**Bước 1**: Chạy agent nhiều lần, một số câu trả lời cho thông tin sai (thời tiết, giá vé không thực tế). Kiểm tra log, lọc theo `event`:

```json
{"event": "AGENT_START", "data": {"input": "Thời tiết Đà Nẵng cuối tuần này thế nào?", "model": "gpt-4o"}}
{"event": "AGENT_END",   "data": {"steps": 0, "has_answer": true}}
```

Dấu hiệu bất thường: `steps: 0`. Agent "hoàn thành" mà không có bước nào. Scan tiếp — không có `TOOL_CALL` hay `TOOL_RESULT` nào giữa hai dòng trên.

**Bước 2**: Thêm print để in raw output từ `llm.generate()` trước khi parse — lộ ra toàn bộ vấn đề:

```
Thought: Tôi cần tìm thời tiết Đà Nẵng.
Action: web_search[thời tiết Đà Nẵng cuối tuần]
Observation: Thời tiết Đà Nẵng cuối tuần: 30°C, nắng đẹp...  ← LLM tự bịa
Thought: Tôi đã có đủ thông tin.
Final Answer: Cuối tuần này Đà Nẵng nắng đẹp, nhiệt độ 30°C...
```

LLM sinh toàn bộ trace trong **một lần generate duy nhất**. Agent parse thấy `Final Answer`, kết thúc với `steps: 0` — chưa bao giờ có cơ hội intercept để gọi tool thật.

**Diagnosis**: Đây là đặc tính của LLM được train trên ReAct traces — model học cách "hoàn thành" format `Observation:` sau `Action:` như một pattern tự nhiên. Không có constraint nào trong code ngăn điều này.

**Solution**: Dùng `stop=["\nObservation:"]` — tham số native của OpenAI API. Chi tiết implementation ở Part I.

Kết quả sau fix — log xác nhận agent gọi tool thực tế:

```json
{"event": "TOOL_CALL",   "data": {"tool": "get_system_time", "args": ""}}
{"event": "TOOL_RESULT", "data": {"tool": "get_system_time", "result": "Sunday, April 06, 2026"}}
{"event": "TOOL_CALL",   "data": {"tool": "web_search", "args": "thời tiết Đà Nẵng 11 12 tháng 4 2026"}}
{"event": "TOOL_RESULT", "data": {"tool": "web_search", "result": "- Dự báo thời tiết Đà Nẵng..."}}
{"event": "AGENT_END",   "data": {"steps": 2, "has_answer": true}}
```

`steps: 0` → `steps: 2`. Bài học: **structured logs với event type là công cụ debug thiết yếu** — không có `steps: 0` trong log, bug này gần như không thể phát hiện tự động.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

**1. Reasoning — `Thought` block giúp gì so với Chatbot?**

Chatbot trả lời thẳng từ câu hỏi → output phụ thuộc hoàn toàn vào parametric memory. ReAct agent có `Thought` block buộc LLM phải "lập kế hoạch" trước khi hành động — xác định cần thông tin gì, tool nào phù hợp, argument ra sao. Khi người dùng hỏi "thời tiết cuối tuần", chatbot đoán mù, còn agent suy luận: _"cần biết hôm nay là ngày mấy trước → dùng `get_system_time` → rồi mới search"_. Đây là sự khác biệt giữa **retrieval** (lấy thông tin thực) và **recall** (nhớ từ training).

**2. Reliability — Agent thực sự tệ hơn Chatbot khi nào?**

Agent tốn gấp ~5.7× chi phí và ~6× thời gian với cùng một câu hỏi đơn giản. Với câu như _"thủ đô của Việt Nam là gì?"_, chatbot trả lời trong ~1,200ms với ~$0.0035, agent mất ~7,100ms và ~$0.020 chỉ để quyết định không cần dùng tool rồi trả lời y chang. Agent cũng có thể thất bại do phụ thuộc external service (Brave API timeout, DuckDuckGo rate limit) — chatbot không có điểm thất bại này.

**3. Observation — Feedback từ tool ảnh hưởng như thế nào?**

Observation là "grounding signal" — nó kéo LLM ra khỏi parametric memory về thực tế hiện tại. Ví dụ rõ nhất: sau khi nhận `Observation: Sunday, April 06, 2026` từ `get_system_time`, LLM ở bước tiếp theo sinh query `thời tiết Đà Nẵng tháng 4 2026` thay vì `tháng 10 2023` như trước fix. Một observation sai do tool lỗi sẽ lan truyền sai lệch qua toàn bộ các bước còn lại reliability của tool quan trọng hơn accuracy của LLM trong một hệ thống agentic.

---

## IV. Future Improvements (5 Points)

**Scalability — Async tool execution**

Hiện tại tool calls là sequential: agent gọi `web_search`, chờ kết quả, rồi mới tiếp tục. Với multi-tool queries, có thể parallelize các tool calls độc lập bằng `asyncio.gather()`. Ví dụ: search thời tiết và search giá vé là hai queries độc lập — chạy song song giảm latency từ ~6,000ms xuống ~3,000ms.

**Safety — Supervisor LLM**

Thêm một LLM thứ hai ("supervisor") audit tool arguments trước khi execute — phát hiện prompt injection qua tool results (ví dụ: Brave trả về trang web chứa `Ignore previous instructions...`)

**Performance — Routing layer**

Thêm intent classifier nhẹ phân loại câu hỏi: `simple` (factual, no real-time needed) → route sang chatbot baseline; `complex` (real-time, multi-step) → route sang ReAct agent. Giảm chi phí cho các câu hỏi đơn giản mà không giảm chất lượng với câu hỏi phức tạp.
