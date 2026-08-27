from typing import Literal, Optional
from pydantic import BaseModel, computed_field

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
EntityMatchType = Literal["exact", "semantic", "other"]

class PairMatchVerdict(BaseModel):
    match_type: EntityMatchType
    explanation: str

class EntityMatch(BaseModel):
    activity_a: ActionEntityPair
    activity_b: ActionEntityPair
    match_type: EntityMatchType
    explanation: str

class EntityMatchResult(BaseModel):
    story_a_id: str
    story_b_id: str
    entity_matches: list[EntityMatch]


# Step 2 - CRUD verb classification
OperationType = Literal["CREATE", "READ", "UPDATE", "DELETE", "NON_CRUD"]

class ActivityPairInput(BaseModel):
    activity_a: ActionEntityPair
    activity_b: ActionEntityPair

class ClassifiedActivity(BaseModel):
    action: str
    entity: str
    operation_type: OperationType

class ClassifiedActivityPair(BaseModel):
    activity_a: ClassifiedActivity
    activity_b: ClassifiedActivity

class ClassifiedMatch(BaseModel):
    activity_a: ClassifiedActivity
    activity_b: ClassifiedActivity
    match_type: EntityMatchType

class ClassifiedMatchResult(BaseModel):
    story_a_id: str
    story_b_id: str
    classified_matches: list[ClassifiedMatch]


# Step 3 - final dependency decision
class ClassifiedActivityPairInput(BaseModel):
    story_a_id: str
    story_b_id: str
    activity_a: ClassifiedActivity
    activity_b: ClassifiedActivity

class DependencyEntryAnnotated(BaseModel):
    prerequisite_id: str
    dependent_id: str
    prerequisite_activity: ClassifiedActivity
    dependent_activity: ClassifiedActivity
    match_type: EntityMatchType

class FoundedDependencyUsingAnnotated(BaseModel):
    dependencies: list[DependencyEntryAnnotated]

class DependencyVerdict(BaseModel):
    qualifies: bool
    prerequisite_id: Optional[str] = None
    dependent_id: Optional[str] = None

# annotated based dependency analysis result
class AnnotatedDependencyResult(BaseModel):
    story_a: str
    story_b: str
    step_1_match: EntityMatchResult
    step_2_classify: ClassifiedMatchResult
    final_llm: FoundedDependencyUsingAnnotated
    final_nlp: FoundedDependencyUsingAnnotated

    @computed_field
    @property
    def dependencyFoundLLM(self) -> bool:
        return len(self.final_llm.dependencies) > 0

    @computed_field
    @property
    def dependencyFoundNLP(self) -> bool:
        return len(self.final_nlp.dependencies) > 0


# text-based dependency analysis result
class DependencyEntryText(BaseModel):
    prerequisite_id: str
    dependent_id: str
    explanationOfDependency: str
    matchingTextPairs: list[tuple[str, str]]

class TextDependencyResult(BaseModel):
    story_a_id: str
    story_b_id: str
    dependencyFound: bool
    dependencies: list[DependencyEntryText]