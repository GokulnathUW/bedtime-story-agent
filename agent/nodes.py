from typing import Any

from agent.state import StoryState


def plot_writer(state: StoryState) -> dict[str, Any]:
    raise NotImplementedError


def plot_judge(state: StoryState) -> dict[str, Any]:
    raise NotImplementedError


def story_writer(state: StoryState) -> dict[str, Any]:
    raise NotImplementedError


def story_judge(state: StoryState) -> dict[str, Any]:
    raise NotImplementedError
