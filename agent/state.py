from typing import Literal

from pydantic import BaseModel, Field

Rating = Literal["good", "borderline", "bad"]


def dimensions_pass(*ratings: Rating) -> bool:
    """Pass when no dimension is bad (borderline is OK)."""
    return all(r != "bad" for r in ratings)


class PlotReasoning(BaseModel):
    relevance: str
    structure: str


class PlotScores(BaseModel):
    relevance: Rating
    structure: Rating


class PlotJudgeResult(BaseModel):
    reasoning: PlotReasoning
    scores: PlotScores
    feedback: str

    def passed(self) -> bool:
        return dimensions_pass(self.scores.relevance, self.scores.structure)


class StoryReasoning(BaseModel):
    age_appropriate: str
    engagement: str


class StoryScores(BaseModel):
    age_appropriate: Rating
    engagement: Rating


class StoryJudgeResult(BaseModel):
    reasoning: StoryReasoning
    scores: StoryScores
    feedback: str

    def passed(self) -> bool:
        return dimensions_pass(self.scores.age_appropriate, self.scores.engagement)


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
