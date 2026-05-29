# CEO Mind — C-Suite Decision Framework

The CEO node of a planned multi-role (CEO, CFO, COO, CMO, CTO…) decision framework. This CEO thinks like a composite of **Warren Buffett** (capital & judgment), **Tim Cook** (operations & focus), and **Vladislav Doronin** (vision & brand).

## Files

| File | Purpose |
|---|---|
| `CEO_MIND_BACKGROUND.md` | Long-form persona doc. Read this first. |
| `ceo_persona.json` | Machine-readable persona: principles, rubric, red flags, system prompt. Loaded by the graph. |
| `ceo_graph.py` | LangGraph skeleton: `problem_extractor → option_generator → option_evaluator → best_solution_selector`. |
| `requirements.txt` | Python deps. |

## Pipeline

```
situation
   │
   ▼
problem_extractor      ── extracts surface_ask + actual_decision
   │
   ▼
option_generator       ── produces ≥3 distinct options (incl. "do nothing")
   │
   ▼
option_evaluator       ── scores each option on 9 dimensions × 3 archetypes, flags vetoes
   │
   ▼
best_solution_selector ── returns highest weighted score with no veto
```

## Run

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=...     # or swap the LLM in ceo_graph.py
python ceo_graph.py
```

Without an API key, `python ceo_graph.py` still compiles the graph and prints the node list — useful as a smoke test.

## Next steps

1. Add a web UI (FastAPI + a single-page React or HTMX front end).
2. Add the other C-suite nodes (CFO, COO, CMO, CTO), each with its own persona JSON and rubric.
3. Add a **boardroom node** that runs all C-suite minds in parallel on the same situation and resolves disagreements.
4. Persist runs to a DB so decisions are auditable and learn-from-able over time.
