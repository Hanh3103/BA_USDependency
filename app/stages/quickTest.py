from stages.annotation import annotate

if __name__ == '__main__':

    user_story = (
        "As a traveler, I want to import a location from a saved TikTok or Instagram video with a single tap, so that I can quickly capture travel inspiration without manually typing details."
    )

    result = annotate(user_story, "US-001")
    print(result)