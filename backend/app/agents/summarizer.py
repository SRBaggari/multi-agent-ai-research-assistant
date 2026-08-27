from app.agents.supervisor import ask_llm


def summarize_paper(context: str):

    prompt = f"""
You are an academic research paper summarization agent.

Summarize the provided research paper content.

Create the following structure:

# Paper Summary

## 1. Research Problem

## 2. Objective

## 3. Methodology

## 4. Dataset

## 5. Model / Algorithm

## 6. Results

## 7. Limitations

## 8. Conclusion

## 9. Key Takeaways

IMPORTANT:

- Use only the provided research content.
- Do not invent information.
- Include citations for important claims.
- Use:

[Source: filename, Page X]

Research Content:

{context}
"""

    return ask_llm(prompt)