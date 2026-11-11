from utils.llm_client_helpers import _call_stage, _load_prompt
from schemas.dependency.dependency_schema import TextDependencyResult, TextDependencyLLMOutput
from config import settings
import json

TEXT_PROMPT_PATH = settings.prompt_path("dependency_analysis", variant="text")

def detect_dependency_text(story_a, story_b, model:str, max_retries: int = 2):
    """
    Detect dependencies between two user stories using a text-based prompt.

    Args:
        story_a: The first user story object.
        story_b: The second user story object.
        model: The name of the model to use.
        max_retries: The maximum number of retries for the LLM call in case of failure

    Returns:
        A tuple containing:
            - TextDependencyResult: The result of the dependency detection.
            - bool: A flag indicating whether the result was obtained after retries.
            - int: The number of attempts made to get the result.
    """
    prompt = _load_prompt(TEXT_PROMPT_PATH)
    payload = {
        "story_a": {"id": story_a.id, "text": story_a.Text, "benefit": story_a.benefit},
        "story_b": {"id": story_b.id, "text": story_b.Text, "benefit": story_b.benefit},
    }

    messages = [
        {"role": "system", "content": prompt},

        # Example 1 - single direction
        {"role": "user", "content": json.dumps({
            "story_a": {
                "id": "US-107",
                "text": "As a shopper, I want to add a product to my wishlist, so that I can find it easily later.",
                "benefit": "so that I can find it easily later",
            },
            "story_b": {
                "id": "US-142",
                "text": "As a shopper, I want to move a wishlist item into my cart, so that I can purchase it.",
                "benefit": "so that I can purchase it",
            },
        })},
        {"role": "assistant", "content": json.dumps({
            "story_a_id": "US-107", "story_b_id": "US-142", "dependencyFound": True,
            "dependencies": [{
                "prerequisite_id": "US-107", "dependent_id": "US-142",
                "explanationOfDependency": "In the main part of Story US-107, a 'wishlist item' is created. This acts as a prerequisite for the main part of Story US-142, which moves that wishlist item into the cart.",
                "matchingTextPairs": [["add a product to my wishlist", "move a wishlist item into my cart"]],
            }],
        })},

        # Example 2 - no dependency
        {"role": "user", "content": json.dumps({
            "story_a": {
                "id": "US-063",
                "text": "As a shopper, I want to view my order history, so that I can track past purchases.",
                "benefit": "so that I can track past purchases",
            },
            "story_b": {
                "id": "US-091",
                "text": "As a support agent, I want to browse the FAQ articles, so that I can answer customer questions.",
                "benefit": "so that I can answer customer questions",
            },
        })},
        {"role": "assistant", "content": json.dumps({
            "story_a_id": "US-063", "story_b_id": "US-091", "dependencyFound": False, "dependencies": [],
        })},

        # Example 3 - bidirectional dependency
        {"role": "user", "content": json.dumps({
            "story_a": {
                "id": "US-215",
                "text": "As a shopper, I want to create an order and view an existing saved payment method, so that I can complete checkout.",
                "benefit": "so that I can complete checkout",
            },
            "story_b": {
                "id": "US-228",
                "text": "As a shopper, I want to save a new payment method and view an existing order, so that I know which order to apply it to.",
                "benefit": "so that I know which order to apply it to",
            },
        })},
        {"role": "assistant", "content": json.dumps({
            "story_a_id": "US-215", "story_b_id": "US-228", "dependencyFound": True,
            "dependencies": [
                {
                    "prerequisite_id": "US-215", "dependent_id": "US-228",
                    "explanationOfDependency": "Story US-215 creates an 'order', which Story US-228 views as an existing order.",
                    "matchingTextPairs": [["create an order", "view an existing order"]],
                },
                {
                    "prerequisite_id": "US-228", "dependent_id": "US-215",
                    "explanationOfDependency": "Story US-228 saves a new 'payment method', which Story US-215 views as an existing saved payment method.",
                    "matchingTextPairs": [["save a new payment method", "view an existing saved payment method"]],
                },
            ],
        })},

        {"role": "user", "content": json.dumps(payload, indent=2)},
    ]
    
    last_error = None
    for attempt in range(max_retries):
        try:
            llm_result = _call_stage(messages=messages, schema_model=TextDependencyLLMOutput, model=model)
            result = TextDependencyResult(
                story_a_text=story_a.Text,
                story_b_text=story_b.Text,
                **llm_result.model_dump()
            )
            return result, False, attempt + 1
        except Exception as err:
            last_error = err
            print(f"Warning: attempt {attempt + 1} failed for pair ({story_a.id}, {story_b.id}): {err}")

    print(f"Skipping pair ({story_a.id}, {story_b.id}) after {max_retries} attempts — last error: {last_error}")
    result = TextDependencyResult(
        story_a_text=story_a.Text,
        story_b_text=story_b.Text,
        story_a_id=story_a.id,
        story_b_id=story_b.id,
        dependencyFound=False,
        dependencies=[]
    )
    return result, True, max_retries
