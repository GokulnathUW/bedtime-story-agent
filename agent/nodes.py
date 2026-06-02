import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from agent.state import PlotJudgeResult, StoryJudgeResult, StoryState
from bedtime_story_agent.llm import call_model
from prompts import templates

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _format_prompt(name: str, **kwargs: str) -> str:
    template: str = getattr(templates, name)
    if not template.strip():
        raise ValueError(f"Fill in prompts.templates.{name} before running the agent")
    return template.format(**kwargs)


def _call_judge(prompt: str, result_type: type[T]) -> T | None:
    """JSON mode + Pydantic validation; one retry on parse/validation failure."""
    for attempt in range(2):
        raw = call_model(prompt, json_mode=True)
        if raw is None:
            return None
        try:
            return result_type.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("Judge parse failed (%s, attempt %d): %s", result_type.__name__, attempt + 1, e)
    return None


def plot_writer(state: StoryState) -> dict[str, Any]:
    is_revision = state.plot is not None and state.plot_feedback is not None
    prompt = _format_prompt(
        "plot_writer",
        request=state.request,
        plot=state.plot or "",
        plot_feedback=state.plot_feedback or "",
    )
    outline = call_model(prompt)
    if outline is None:
        logger.error("plot_writer: model call failed")
        return {}

    updates: dict[str, Any] = {"plot": outline.strip()}
    if is_revision:
        updates["plot_revisions"] = state.plot_revisions + 1
    return updates


def plot_judge(state: StoryState) -> dict[str, Any]:
    if not state.plot:
        logger.error("plot_judge: no plot in state")
        return {"plot_passed": False}

    prompt = _format_prompt(
        "plot_judge",
        request=state.request,
        plot=state.plot,
    )
    result = _call_judge(prompt, PlotJudgeResult)
    if result is None:
        logger.error("plot_judge: could not parse judge response")
        return {"plot_passed": False}

    logger.info(
        "plot_judge: relevance=%s structure=%s passed=%s",
        result.relevance,
        result.structure,
        result.passed(),
    )
    return {
        "plot_feedback": result.feedback,
        "plot_passed": result.passed(),
    }


def story_writer(state: StoryState) -> dict[str, Any]:
    if not state.plot:
        logger.error("story_writer: no plot in state")
        return {}

    is_revision = state.story is not None and state.story_feedback is not None
    prompt = _format_prompt(
        "story_writer",
        request=state.request,
        plot=state.plot,
        story=state.story or "",
        story_feedback=state.story_feedback or "",
    )
    prose = call_model(prompt)
    if prose is None:
        logger.error("story_writer: model call failed")
        return {}

    updates: dict[str, Any] = {"story": prose.strip()}
    if is_revision:
        updates["story_revisions"] = state.story_revisions + 1
    return updates


def story_judge(state: StoryState) -> dict[str, Any]:
    if not state.story:
        logger.error("story_judge: no story in state")
        return {"story_passed": False}

    prompt = _format_prompt(
        "story_judge",
        request=state.request,
        plot=state.plot or "",
        story=state.story,
    )
    result = _call_judge(prompt, StoryJudgeResult)
    if result is None:
        logger.error("story_judge: could not parse judge response")
        return {"story_passed": False}

    logger.info(
        "story_judge: age_appropriate=%s engagement=%s passed=%s",
        result.age_appropriate,
        result.engagement,
        result.passed(),
    )
    return {
        "story_feedback": result.feedback,
        "story_passed": result.passed(),
    }
