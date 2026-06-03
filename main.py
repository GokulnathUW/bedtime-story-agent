import logging
import sys

from agent.agent import run_story

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

The most exciting extension would be a choose-your-own-adventure mode inspired by the Goosebumps gamebook series I used to read as a kid: grow the plot-writer into a branching outliner that generates multiple decision paths with convergent safe endings, letting the child co-author the story beat by beat. Architecturally this is a natural next step — the plot-writer already produces a structured outline, so adding branching decision points is incremental rather than a rewrite, and the existing judge loops could validate each branch independently.
"""


def main() -> None:
    user_input = input("What kind of story do you want to hear? ")
    # user_input = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."
    final = run_story(user_input)

    if not final.request_appropriate:
        print(final.request_safety_reason or "That request isn't right for a children's bedtime story.", file=sys.stderr)
        sys.exit(1)

    if not final.story:
        print("Sorry, something went wrong generating your story. Please try again.", file=sys.stderr)
        sys.exit(1)

    print("Your story:")
    print(final.story)
    print("--------------------------------")


if __name__ == "__main__":
    main()
