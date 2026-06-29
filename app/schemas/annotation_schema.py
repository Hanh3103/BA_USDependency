from pydantic import BaseModel
from typing import List, Any


class AnnotationSchema(BaseModel):
    Text: str
    Persona: List[str]
    GoalAction: List[str]
    GoalEntity: List[str]
    BenefitAction: List[str]
    BenefitEntity: List[str]
    triggers: List[List[str]] = []
    targets: List[List[str]] = []
    contains: List[List[str]] = []
