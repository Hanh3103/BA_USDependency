from schemas.dependency.dependency_schema import AnnotatedStory, ActionEntityPair, IsStoryWellformed

def _extract_activity_reason(story: AnnotatedStory) -> IsStoryWellformed:
    # 1. Access nested Pydantic schema attributes
    goal_actions = set(story.Action.GoalAction)
    goal_entities = set(story.Entity.GoalEntity)
    benefit_actions = set(story.Action.BenefitAction)
    benefit_entities = set(story.Entity.BenefitEntity)
    benefit_text = story.benefit

    activities: list[ActionEntityPair] = []
    reasons: list[ActionEntityPair] = []

    # 2. Iterate through targets tuples: ["action", "entity"]
    for action, entity in story.targets:
        if action in goal_actions and entity in goal_entities:
            activities.append(ActionEntityPair(action=action, entity=entity))
        elif action in benefit_actions and entity in benefit_entities:
            reasons.append(ActionEntityPair(action=action, entity=entity))

    # 3. Check well-formedness rules
    well_formed, reason = _check_well_formed(
        has_persona=bool(story.Persona),
        claims_benefit=bool(benefit_text),
        has_activity=bool(activities),
        has_reason=bool(reasons),
    )

    return IsStoryWellformed(
        id=story.id,
        Text=story.Text,
        well_formed=well_formed,
        well_formed_reason=reason,
        Persona=story.Persona,
        activity=activities,
        reason=reasons,
    )


def _check_well_formed(
    has_persona: bool, claims_benefit: bool, has_activity: bool, has_reason: bool
) -> tuple[bool, str]:
    if not has_persona:
        return False, "Persona is empty"
    if not has_activity:
        return False, "no targets pair connects a GoalAction to a GoalEntity"
    if claims_benefit and not has_reason:
        return False, "BenefitAction/BenefitEntity present but no targets pair connects them"
    return True, ""


def filter_well_formed(
    stories: list[AnnotatedStory],
) -> tuple[list[IsStoryWellformed], list[IsStoryWellformed]]:
    kept, dropped = [], []
    for story in stories:
        result = _extract_activity_reason(story)
        (kept if result.well_formed else dropped).append(result)
    return kept, dropped


# if __name__ == '__main__':
#     from stages.input_reader import load_dataset
#
#     input_path = "C:\\Users\\daoha\\Downloads\\IT_Tasks\\BA_USDependency\\app\\test\\baseline\\annotation\\train_baseline_test_1.json"
#
#     dataset = load_dataset(input_path)
#     print(extract(dataset[0]))
#     print(extract(dataset[1]))
#     print(extract(dataset[2]))

