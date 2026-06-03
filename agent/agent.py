from langgraph.graph import END, START, StateGraph
from langsmith import traceable

from agent.nodes import plot_judge, plot_writer, story_judge, story_writer
from agent.state import StoryState
from bedtime_story_agent.settings import MAX_PLOT_REVISIONS, MAX_STORY_REVISIONS
from bedtime_story_agent.tracing import configure_langsmith


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

    builder.add_node("plot_writer", plot_writer)
    builder.add_node("plot_judge", plot_judge)
    builder.add_node("story_writer", story_writer)
    builder.add_node("story_judge", story_judge)

    builder.add_edge(START, "plot_writer")
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
    # LangGraph may return a dict; normalize to StoryState
    if isinstance(final, StoryState):
        return final
    return StoryState.model_validate(final)
