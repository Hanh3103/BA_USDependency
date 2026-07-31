from typing import Literal
from pydantic import BaseModel, Field

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


# Step 1
VerbClass = Literal["PROVISIONS", "REQUIRES", "AMBIGUOUS"]

class TaxonomyEntry(BaseModel):
    verb: str
    class_: VerbClass = Field(..., alias="class")
    reason: str

class Taxonomy(BaseModel):
    taxonomy: list[TaxonomyEntry]

# Step 2

ClassifiedVerbClass= Literal["PROVISIONS", "REQUIRES", "AMBIGUOUS", "UNKNOWN"]
class VerbClassifiedActivity(BaseModel):
    action: str
    entity: str
    class_: ClassifiedVerbClass = Field(..., alias="class")

class VerbClassifyResult(BaseModel):
    story_a_id: str
    story_b_id: str
    verb_classification: dict[str, list[VerbClassifiedActivity]]  # keys are "story_a" and "story_b"

# Step 3
EntityMatchType = Literal["EQUIVALENT", "SIMILAR"]

class EntityMatch(BaseModel):
    activity_a: VerbClassifiedActivity
    activity_b: VerbClassifiedActivity
    shared_entity: str
    match_type: EntityMatchType

class EntityMatchResult(BaseModel):
    entity_matches: list[EntityMatch]

# Step 4
class DependencyResult(BaseModel):
    OBD_dependency: bool
    prerequisite_id: str
    dependent_id: str
    prerequisite_action: str
    dependent_action: str
    shared_entity: str


# result for each pair
class PairResult(BaseModel):
    story_a:str
    story_b:str
    step_2_classify: VerbClassifyResult
    step_3_match: EntityMatchResult
    final: DependencyResult






