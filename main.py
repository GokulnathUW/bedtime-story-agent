import logging
import sys

from agent.agent import run_story
from bedtime_story_agent.tracing import configure_langsmith

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

"""


def main() -> None:
    configure_langsmith()
    user_input = input("What kind of story do you want to hear? ")
    final = run_story(user_input)
    if not final.story:
        print("Sorry, something went wrong generating your story. Please try again.", file=sys.stderr)
        sys.exit(1)
    print(final.story)


if __name__ == "__main__":
    main()
