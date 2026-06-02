import logging
import sys

from bedtime_story_agent.llm import call_model

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

"""


def main() -> None:
    user_input = input("What kind of story do you want to hear? ")
    response = call_model(user_input)
    if response is None:
        print("Sorry, something went wrong generating your story. Please try again.", file=sys.stderr)
        sys.exit(1)
    print(response)


if __name__ == "__main__":
    main()
