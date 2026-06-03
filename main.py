import logging
import sys

from agent.agent import run_story

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

"""


def main() -> None:
    user_input = input("What kind of story do you want to hear? ")
    # user_input = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."
    final = run_story(user_input)

    if not final.story:
        print("Sorry, something went wrong generating your story. Please try again.", file=sys.stderr)
        sys.exit(1)

    print("Your story:")
    print(final.story)
    print("--------------------------------")


if __name__ == "__main__":
    main()
