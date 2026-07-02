from stages.annotation import annotate

if __name__ == '__main__':

    user_story = (
        "As a customer, I want to reset my password via email "
        "so that I can regain access to my account."
    )

    result = annotate(user_story, "US-001")
    print(result)