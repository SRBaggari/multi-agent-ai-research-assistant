from app.agents.supervisor import ask_llm


def answer_question(
    question: str,
    context: str
):

    prompt = f"""
You are an academic research assistant.

Answer the user's question using ONLY
the provided research paper sources.

IMPORTANT RULES:

1. Do not invent facts.
2. Do not use outside knowledge.
3. If the answer is not available,
   clearly say so.
4. Cite the source using the format:

   [Source: filename, Page X]

5. If multiple sources support an answer,
   cite all relevant sources.

Question:

{question}


Research Sources:

{context}


Provide a concise but informative answer.
"""

    return ask_llm(prompt)