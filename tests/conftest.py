import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from tests.eval.report import EVAL_RESULTS_PATH, write_eval_results

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

    tr = _terminal_reporter(session.config)
    if tr is None:
        return

    tr.write_sep("=", "Bedtime story eval (not interactive)")
    tr.write_line(
        f"Running {len(eval_items)} fixed prompts from tests/eval/prompts.py — not stdin."
    )
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
        request.config.stash.setdefault(eval_meta_key, {})["skip_reason"] = (
            "OPENAI_API_KEY is not set (check .env in repo root)"
        )
        pytest.skip("OPENAI_API_KEY is not set")


@pytest.fixture(scope="session")
def eval_json_records(request: pytest.FixtureRequest) -> list[dict[str, Any]]:
    meta = request.config.stash.setdefault(eval_meta_key, {})
    meta["results_path"] = str(EVAL_RESULTS_PATH)
    records: list[dict[str, Any]] = []
    yield records
    if records:
        path = write_eval_results(EVAL_RESULTS_PATH, records)
        meta["written_path"] = str(path)
    meta["count"] = len(records)


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    meta = config.stash.get(eval_meta_key, None)
    if not meta:
        return

    terminalreporter.write_sep("=", "Eval harness")
    if written := meta.get("written_path"):
        terminalreporter.write_line(f"Wrote {meta.get('count', 0)} result(s) to {written}")
    elif skip := meta.get("skip_reason"):
        terminalreporter.write_line(skip)
        terminalreporter.write_line(f"No JSON written. Results path: {meta.get('results_path')}")
    elif meta.get("count", 0) == 0:
        terminalreporter.write_line(f"No results collected. Expected path: {meta.get('results_path')}")
