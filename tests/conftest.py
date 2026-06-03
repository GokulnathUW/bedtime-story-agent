import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from tests.eval.report import EVAL_RESULTS_PATH, write_eval_results

# Load .env from repo root so OPENAI_API_KEY is visible to pytest (same as the app).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

eval_meta_key = pytest.StashKey[dict[str, Any]]()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: runs the full LangGraph pipeline against OpenAI",
    )


def _terminal_reporter(config: pytest.Config) -> pytest.TerminalReporter | None:
    return config.pluginmanager.get_plugin("terminalreporter")


def pytest_collection_finish(session: pytest.Session) -> None:
    eval_items = [item for item in session.items if "test_eval" in item.nodeid]
    if not eval_items:
        return

    session.config.stash.setdefault(eval_meta_key, {})["eval_session"] = True
    tr = _terminal_reporter(session.config)
    if tr is None:
        return

    tr.write_sep("=", "Bedtime story eval (not interactive)")
    tr.write_line(
        f"Running {len(eval_items)} fixed prompts from tests/eval/prompts.py — "
        "not stdin."
    )
    tr.write_line(
        "Each case runs the full LangGraph pipeline against OpenAI "
        "(plot + judges + story; often 1–3 min per case)."
    )
    tr.write_line("Do not type at the terminal; wait for the lines below.")
    tr.write_line(f"Results JSON: {EVAL_RESULTS_PATH}")
    tr.write_line("Add -s to see per-case plot/story summary lines as they finish.")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    if "test_eval_prompt" not in item.nodeid:
        return

    tr = _terminal_reporter(item.config)
    if tr is None:
        return

    case_id = item.callspec.id if item.callspec is not None else item.name
    tr.write_line(f"→ [{case_id}] Calling OpenAI pipeline…", bold=True)


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item: pytest.Item) -> None:
    """Print done/skipped/failed after each eval case (TestReport has no .config)."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or "test_eval_prompt" not in report.nodeid:
        return

    tr = _terminal_reporter(item.config)
    if tr is None:
        return

    case_id = item.callspec.id if item.callspec is not None else item.name
    if report.passed:
        tr.write_line(f"  ✓ [{case_id}] done", green=True)
    elif report.skipped:
        tr.write_line(f"  ⊘ [{case_id}] skipped", yellow=True)
    else:
        tr.write_line(f"  ✗ [{case_id}] failed", red=True)


@pytest.fixture
def require_openai_api_key(request: pytest.FixtureRequest) -> None:
    if not os.getenv("OPENAI_API_KEY"):
        meta = request.config.stash.setdefault(eval_meta_key, {})
        meta["skip_reason"] = "OPENAI_API_KEY is not set (check .env in repo root)"
        pytest.skip("OPENAI_API_KEY is not set")


@pytest.fixture(scope="session")
def eval_json_records(request: pytest.FixtureRequest) -> list[dict[str, Any]]:
    """Collect eval rows across parametrized tests; flush to JSON at session end."""
    meta = request.config.stash.setdefault(eval_meta_key, {})
    meta["results_path"] = str(EVAL_RESULTS_PATH)
    records: list[dict[str, Any]] = []
    yield records
    if records:
        path = write_eval_results(EVAL_RESULTS_PATH, records)
        meta["written_path"] = str(path)
        meta["count"] = len(records)
    else:
        meta["count"] = 0


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    meta = config.stash.get(eval_meta_key, None)
    if not meta:
        return

    terminalreporter.write_sep("=", "Eval harness")
    path = meta.get("results_path", str(EVAL_RESULTS_PATH))
    written = meta.get("written_path")
    count = meta.get("count")

    if written:
        terminalreporter.write_line(f"Wrote {count} result(s) to {written}")
    elif skip := meta.get("skip_reason"):
        terminalreporter.write_line(skip)
        terminalreporter.write_line(f"No JSON written. Results path when run: {path}")
    elif count == 0:
        terminalreporter.write_line("No eval results collected (tests did not run?).")
        terminalreporter.write_line(f"Expected JSON path: {path}")
    terminalreporter.write_line(
        "Tip: use  pytest tests/test_eval.py -m integration -s  for live lines + JSON"
    )
