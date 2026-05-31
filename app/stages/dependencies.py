from stages.ollama_connection import create_chat_completion

SYSTEM_PROMPT = """You are a technical dependency analyser.
Based on the annotations provided, identify:
- Technical dependencies (APIs, databases, services)
- Risks
- Suggested implementation order
Be concise and structured."""

def run(annotation: str) -> str:
    response = create_chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": annotation}
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content
