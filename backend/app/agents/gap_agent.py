from app.agents.supervisor import ask_llm


def identify_research_gaps(
    context: str
):

    prompt = f"""
You are an academic research gap detection agent.

Analyze the provided research papers.

Identify:

1. Common limitations
2. Dataset gaps
3. Methodological gaps
4. Performance gaps
5. Real-world deployment gaps
6. Evaluation gaps
7. Contradictions between papers

For every identified gap:

- Explain the evidence
- Mention the paper
- Mention the page
- Suggest a possible research direction

Use this format:

## Research Gap 1

Description:
...

Evidence:
[Source: filename, Page X]

Potential Research Direction:
...

IMPORTANT:

Do not create unsupported research gaps.

Research Sources:

{context}
"""

    return ask_llm(prompt)