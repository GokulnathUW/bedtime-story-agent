from prompts.scaffold import strip_story_scaffolds
from prompts.templates import (
    format_plot_judge_user,
    format_plot_writer_user,
    format_request_safety_user,
    format_story_judge_user,
    format_story_writer_user,
    plot_judge_system,
    plot_writer_system,
    request_safety_system,
    story_judge_system,
    story_writer_system,
)

__all__ = [
    "format_plot_judge_user",
    "format_plot_writer_user",
    "format_request_safety_user",
    "format_story_judge_user",
    "format_story_writer_user",
    "plot_judge_system",
    "plot_writer_system",
    "request_safety_system",
    "story_judge_system",
    "story_writer_system",
    "strip_story_scaffolds",
]
