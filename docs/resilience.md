# Resilience & Error Recovery Architecture

## 1. Resilience Philosophy

The framework achieves resilience through structured feedback loops, validation gates, retry policies, and rollback mechanisms. It does not assume model self-learning or ungrounded training.

---

## 2. Failure Handling Strategies

### A. LLM & Inference Failure Recovery
- **Timeout Protection**: All Ollama calls enforce an explicit timeout (`OLLAMA_TIMEOUT`, default 120s).
- **Graceful Offline Degrade**: If Ollama is offline or crashes, the framework returns a clear connection diagnostic error rather than hallucinating fake responses.
- **Static Analysis Fallback**: The Code Reviewer gracefully falls back to deterministic AST & Ruff results if the LLM inference service is unreachable.

### B. Safe Code Execution Sandboxing
- Untrusted AI-generated code is **never** executed directly on the host machine.
- Isolated Docker containers are spun up with:
  - `network_disabled=True` (no unauthorized network exfiltration).
  - CPU quotas (`cpu_quota=50000`, limiting execution to 50% CPU capacity).
  - Memory caps (`mem_limit="256m"`).
  - Short timeouts (`EXECUTION_TIMEOUT=30s`).
  - Read-only volume bindings where possible.
- If Docker daemon is inactive, code execution is blocked with clear instructions to start Docker, preserving host security.

### C. Bounded Self-Debugging Loops
- Uncontrolled iterative debugging can produce infinite loops and token exhaustion.
- The `DebuggerAgent` and LangGraph routing enforce `MAX_DEBUG_ATTEMPTS` (default: 3).
- Each attempt is recorded in `debugging_history` with its syntax validity, root cause, and confidence score.
- If max attempts are reached, the system exits gracefully to the Explainer agent and logs the failure for human operator review.
