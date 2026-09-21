from app.agents.llm import ask_llm


def generate_literature_review(context: str):

    prompt = f"""
You are an academic literature review agent.

Analyze the research papers provided below and
generate a structured literature review.

Use ONLY the information provided in the sources.

Structure your response as:

# Literature Review

## 1. Introduction

Briefly introduce the research area.

## 2. Existing Research

Summarize the major approaches used in the papers.

## 3. Methodology Comparison

Compare the methodologies used by different papers.

## 4. Major Findings

Explain the important findings and results.

## 5. Limitations

Identify limitations mentioned or clearly supported
by the papers.

## 6. Research Gaps

Identify gaps that are supported by the papers.

## 7. Future Research Directions

Suggest reasonable research directions based on
the identified gaps.

## 8. Conclusion

Provide a concise conclusion.

IMPORTANT RULES:

- Do not invent information.
- Do not use unsupported facts.
- Cite important claims.
- Use this citation format:

[Source: filename, Page X]

Research Sources:

{context}
"""

    return ask_llm(prompt)