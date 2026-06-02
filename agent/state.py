from typing import Literal

from pydantic import BaseModel, Field

Rating = Literal["good", "borderline", "bad"]


def dimensions_pass(*ratings: Rating) -> bool:
    """Pass when no dimension is bad (borderline is OK)."""
    return all(r != "bad" for r in ratings)


class PlotJudgeResult(BaseModel):
    reasoning: str
    relevance: Rating
    structure: Rating
    feedback: str

    def passed(self) -> bool:
        return dimensions_pass(self.relevance, self.structure)


class StoryJudgeResult(BaseModel):
    reasoning: str
    age_appropriate: Rating
    engagement: Rating
    feedback: str

    def passed(self) -> bool:
        return dimensions_pass(self.age_appropriate, self.engagement)


class StoryState(BaseModel):
    request: str
    plot: str | None = None
    plot_feedback: str | None = None
    plot_passed: bool = False
    plot_revisions: int = Field(default=0, ge=0)
    story: str | None = None
    story_feedback: str | None = None
    story_passed: bool = False
    story_revisions: int = Field(default=0, ge=0)
