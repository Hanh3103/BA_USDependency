from stages.ollama_connection import create_chat_completion

SYSTEM_PROMPT = """You are an annotation engine for user stories.
Extract and return:
- Actors (who is involved)
- Actions (what they want to do)
- Requirements (what the system needs)
Be concise and structured."""

def run(user_story: str) -> str:
    response = create_chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_story}
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content
