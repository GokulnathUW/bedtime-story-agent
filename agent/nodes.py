import json
import logging
from typing import Any, TypeVar

from langsmith import traceable
from pydantic import BaseModel, ValidationError

from agent.state import PlotJudgeResult, StoryJudgeResult, StoryState
from bedtime_story_agent.llm import call_model
from prompts import templates

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _call_judge(
    user_prompt: str,
    result_type: type[T],
    *,
    system: str | None = None,
) -> T | None:
    """JSON mode + Pydantic validation; one retry on parse/validation failure."""
    for attempt in range(2):
        raw = call_model(user_prompt, system=system, json_mode=True)
        if raw is None:
            return None
        try:
            return result_type.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("Judge parse failed (%s, attempt %d): %s", result_type.__name__, attempt + 1, e)
    return None


@traceable(name="plot_writer", run_type="chain", metadata={"system_prompt": "plot_writer_system"})
def plot_writer(state: StoryState) -> dict[str, Any]:
    is_revision = state.plot is not None and state.plot_feedback is not None
    user_prompt = templates.format_plot_writer_user(
        state.request,
        plot=state.plot,
        plot_feedback=state.plot_feedback,
    )
    outline = call_model(user_prompt, system=templates.plot_writer_system)
    if outline is None:
        logger.error("plot_writer: model call failed")
        return {}

    updates: dict[str, Any] = {"plot": outline.strip()}
    if is_revision:
        updates["plot_revisions"] = state.plot_revisions + 1
    return updates


@traceable(name="plot_judge", run_type="chain", metadata={"system_prompt": "plot_judge_system"})
def plot_judge(state: StoryState) -> dict[str, Any]:
    if not state.plot:
        logger.error("plot_judge: no plot in state")
        return {"plot_passed": False}

    user_prompt = templates.format_plot_judge_user(state.request, state.plot)
    result = _call_judge(user_prompt, PlotJudgeResult, system=templates.plot_judge_system)
    if result is None:
        logger.error("plot_judge: could not parse judge response")
        return {"plot_passed": False}

    logger.info(
        "plot_judge: relevance=%s structure=%s passed=%s",
        result.scores.relevance,
        result.scores.structure,
        result.passed(),
    )
    return {
        "plot_feedback": result.feedback,
        "plot_passed": result.passed(),
    }


@traceable(name="story_writer", run_type="chain", metadata={"system_prompt": "story_writer_system"})
def story_writer(state: StoryState) -> dict[str, Any]:
    if not state.plot:
        logger.error("story_writer: no plot in state")
        return {}

    is_revision = state.story is not None and state.story_feedback is not None
    user_prompt = templates.format_story_writer_user(
        state.request,
        state.plot,
        story=state.story,
        story_feedback=state.story_feedback,
    )
    prose = call_model(user_prompt, system=templates.story_writer_system)
    if prose is None:
        logger.error("story_writer: model call failed")
        return {}

    updates: dict[str, Any] = {"story": prose.strip()}
    if is_revision:
        updates["story_revisions"] = state.story_revisions + 1
    return updates


@traceable(name="story_judge", run_type="chain", metadata={"system_prompt": "story_judge_system"})
def story_judge(state: StoryState) -> dict[str, Any]:
    if not state.story:
        logger.error("story_judge: no story in state")
        return {"story_passed": False}

    user_prompt = templates.format_story_judge_user(
        state.request,
        state.plot or "",
        state.story,
    )
    result = _call_judge(user_prompt, StoryJudgeResult, system=templates.story_judge_system)
    if result is None:
        logger.error("story_judge: could not parse judge response")
        return {"story_passed": False}

    logger.info(
        "story_judge: age_appropriate=%s engagement=%s passed=%s",
        result.scores.age_appropriate,
        result.scores.engagement,
        result.passed(),
    )
    return {
        "story_feedback": result.feedback,
        "story_passed": result.passed(),
    }
