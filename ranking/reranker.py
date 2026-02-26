import json
import re
from parser.groq_client import ask_groq
from parser.prompts import RERANK_PROMPT   # <-- IMPORTANT

def rerank_with_groq(jd, candidates):
    # Fill formatted prompt
    prompt = RERANK_PROMPT.format(
        jd=json.dumps(jd, indent=2),
        candidates=json.dumps(candidates, indent=2)
    )

    # Fast, cheap model for sorting
    raw = ask_groq(prompt, model="llama-3.1-8b-instant")

    cleaned = re.sub(r"```json|```", "", raw).strip()

    try:
        parsed = json.loads(cleaned)
        ordered = parsed.get("ordered_ids", [])
        
        id_map = {c["id"]: c for c in candidates}
        reranked = [id_map[i] for i in ordered if i in id_map]

        # Add missing candidates if model skipped any
        for c in candidates:
            if c["id"] not in ordered:
                reranked.append(c)

        return reranked

    except Exception:
        # Fallback to score-based sorting if Groq JSON fails
        return sorted(candidates, key=lambda x: x["score"], reverse=True)
