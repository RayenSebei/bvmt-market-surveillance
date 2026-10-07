from types import SimpleNamespace

import run_all


def test_argument_selection_defaults_to_analysis_only():
    args = run_all.build_parser().parse_args([])
    assert not args.with_scrape
    assert all("scraping/" not in step for step in run_all.selected_steps())
    assert run_all.selected_steps()[0] == "src/evaluation/build_full_universe.py"


def test_argument_selection_supports_scrape_and_skip_ai():
    steps = run_all.selected_steps(with_scrape=True, skip_ai=True)
    assert run_all.SCRAPE_STEPS[0] in steps
    assert steps.index(run_all.BUILD_STEPS[0]) > steps.index(run_all.SCRAPE_STEPS[-1])
    assert "src/triage/ai_triage_free.py" not in steps


def test_runner_stops_on_first_failure(monkeypatch):
    calls = []
    def fake_run(command, **_kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=7)
    monkeypatch.setattr(run_all.subprocess, "run", fake_run)
    assert run_all.main(["--skip-ai"]) == 1
    assert len(calls) == 1
