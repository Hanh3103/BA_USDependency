from typing import Literal
from pydantic import BaseModel

from schemas.annotation.annotation_schema import AnnotationSchema

class AnnotatedStory(AnnotationSchema):
    id: str
    Text: str

class ActionEntityPair(BaseModel):
    action: str
    entity: str

class StoryActivity(BaseModel):
    id: str
    Text: str
    activity: list[ActionEntityPair]


# Step 0
class IsStoryWellformed(BaseModel):
    id: str
    Text: str
    well_formed: bool
    well_formed_reason: str
    Persona: list[str]
    activity: list[ActionEntityPair]
    reason: list[ActionEntityPair]


# Step 1 - entity matching
EntityMatchType = Literal["exact", "semantic"]

class EntityMatch(BaseModel):
    activity_a: ActionEntityPair
    activity_b: ActionEntityPair
    match_type: EntityMatchType

class EntityMatchResult(BaseModel):
    story_a_id: str
    story_b_id: str
    entity_matches: list[EntityMatch]


# Step 2 - CRUD verb classification
OperationType = Literal["CREATE", "READ", "UPDATE", "DELETE", "NON_CRUD"]

class ClassifiedActivity(BaseModel):
    action: str
    entity: str
    operation_type: OperationType

class ClassifiedMatch(BaseModel):
    activity_a: ClassifiedActivity
    activity_b: ClassifiedActivity
    match_type: EntityMatchType

class ClassifiedMatchResult(BaseModel):
    story_a_id: str
    story_b_id: str
    classified_matches: list[ClassifiedMatch]


# Step 3 - final dependency decision
class Dependency(BaseModel):
    prerequisite_id: str
    dependent_id: str
    prerequisite_activity: ClassifiedActivity
    dependent_activity: ClassifiedActivity
    match_type: EntityMatchType

class DependencyResult(BaseModel):
    dependencies: list[Dependency]


# result for each pair
class PairResult(BaseModel):
    story_a: str
    story_b: str
    step_1_match: EntityMatchResult
    step_2_classify: ClassifiedMatchResult
    final: DependencyResult