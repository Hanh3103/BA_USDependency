from stages.ollama_connection import create_chat_completion

SYSTEM_PROMPT = """You are a reporting engine.
Given the user story, annotations, and dependencies,
generate a concise final summary report including:
- Summary of the user story
- Key findings from annotation
- Technical dependencies and risks
- Recommended next steps"""

def run(user_story: str, annotation: str, dependencies: str) -> str:
    content = f"""
User Story: {user_story}

Annotations: {annotation}

Dependencies: {dependencies}
"""
    response = create_chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content
