"""Basic tests for agentctl."""

import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentctl.cli"] + list(args),
        capture_output=True, text=True, timeout=10,
    )


def test_help():
    r = run_cli("--help")
    assert r.returncode == 0
    assert "agentctl" in r.stdout


def test_version():
    r = run_cli("--version")
    assert r.returncode == 0
    assert "0.1.0" in r.stdout


def test_config_show():
    r = run_cli("config", "show")
    assert r.returncode == 0


def test_models_help():
    r = run_cli("models", "--help")
    assert r.returncode == 0


def test_costs_no_crash():
    r = run_cli("costs")
    assert r.returncode == 0


def test_session_help():
    r = run_cli("session", "--help")
    assert r.returncode == 0


def test_compare_help():
    r = run_cli("compare", "--help")
    assert r.returncode == 0
    assert "--models" in r.stdout
