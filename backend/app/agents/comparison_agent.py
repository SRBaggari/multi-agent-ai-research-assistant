from app.agents.supervisor import ask_llm


def compare_papers(context: str):

    prompt = f"""
You are a research paper comparison agent.

Compare ONLY the research papers provided
in the sources below.

Create the following table:

| Feature | Paper 1 | Paper 2 | Paper 3 |
|---------|---------|---------|---------|

Compare:

- Research problem
- Objective
- Methodology
- Dataset
- Model
- Evaluation metrics
- Results
- Limitations

After the table provide:

## Best Approach

## Major Differences

## Common Limitations

## Research Opportunity

IMPORTANT:

Do not invent information.

For every important claim include:

[Source: filename, Page X]

Research Sources:

{context}
"""

    return ask_llm(prompt)