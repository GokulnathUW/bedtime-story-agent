from langgraph.graph import END, START, StateGraph
from langsmith import traceable

from agent.nodes import plot_judge, plot_writer, request_safety, story_judge, story_writer
from agent.state import StoryState
from bedtime_story_agent.settings import MAX_PLOT_REVISIONS, MAX_STORY_REVISIONS
from bedtime_story_agent.tracing import configure_langsmith


def route_after_request_safety(state: StoryState) -> str:
    if state.request_appropriate:
        return "plot_writer"
    return END


def route_after_plot_judge(state: StoryState) -> str:
    # Cap revisions, then advance even if the judge still wants edits
    if state.plot_passed or state.plot_revisions >= MAX_PLOT_REVISIONS:
        return "story_writer"
    return "plot_writer"


def route_after_story_judge(state: StoryState) -> str:
    if state.story_passed or state.story_revisions >= MAX_STORY_REVISIONS:
        return END
    return "story_writer"


def build_graph() -> StateGraph:
    builder = StateGraph(StoryState)

    builder.add_node("request_safety", request_safety)
    builder.add_node("plot_writer", plot_writer)
    builder.add_node("plot_judge", plot_judge)
    builder.add_node("story_writer", story_writer)
    builder.add_node("story_judge", story_judge)

    builder.add_edge(START, "request_safety")
    builder.add_conditional_edges(
        "request_safety",
        route_after_request_safety,
        ["plot_writer", END],
    )
    builder.add_edge("plot_writer", "plot_judge")
    builder.add_conditional_edges(
        "plot_judge",
        route_after_plot_judge,
        ["plot_writer", "story_writer"],
    )
    builder.add_edge("story_writer", "story_judge")
    builder.add_conditional_edges(
        "story_judge",
        route_after_story_judge,
        ["story_writer", END],
    )

    return builder


def compile_graph():
    return build_graph().compile()


@traceable(name="bedtime_story_agent", run_type="chain")
def run_story(request: str) -> StoryState:
    configure_langsmith()
    graph = compile_graph()
    final = graph.invoke(StoryState(request=request))
    return StoryState.model_validate(final)
