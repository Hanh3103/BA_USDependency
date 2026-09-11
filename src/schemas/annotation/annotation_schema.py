from typing import List
from pydantic import BaseModel

# Step 1
class Step1Schema(BaseModel):
    Persona: List[str] = []
    Actions: List[str] = []
    Entities: List[str] = []
    benefit: str = ""

# Step 2
class ActionSchema(BaseModel):
    GoalAction: List[str] = []
    BenefitAction: List[str] = []

class EntitySchema(BaseModel):
    GoalEntity: List[str] = []
    BenefitEntity: List[str] = []

class Step2Schema(BaseModel):
    Action: ActionSchema
    Entity: EntitySchema

# Step 3
class Step3Schema(BaseModel):
    triggers: List[List[str]] = []
    targets: List[List[str]] = []
    contains: List[List[str]] = []


class AnnotationSchema(BaseModel):
    Persona: List[str] = []
    Action: ActionSchema
    Entity: EntitySchema
    benefit: str = ""
    triggers: List[List[str]] = []
    targets: List[List[str]] = []
    contains: List[List[str]] = []