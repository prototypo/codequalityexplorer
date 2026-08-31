# codequalityexplorer

A Claude Code plugin that measures code quality in Python and Rust codebases and helps fix the problems it finds, one at a time.

## Installation

**Try it once** (loads for that session only) — start Claude Code in your target repo with:

```bash
claude --plugin-dir /path/to/codequalityexplorer
```

**Install it permanently** — inside any Claude Code session:

```
/plugin marketplace add /path/to/codequalityexplorer
/plugin install codequalityexplorer@codequalityexplorer
```

The skills are then available in every session as `/quality-report` and `/quality-improve`.

## Usage

Run `/quality-report` first to measure your target codebase. It reads the code and writes a ranked `CODE_QUALITY.md` in the target repo root, listing every finding from worst to best. Then run `/quality-improve` repeatedly — each invocation fixes exactly one finding (the top open one), runs the project's tests to prove it works, and marks the finding `[x]` on success or `[!]` blocked and reverts on failure. One finding per invocation, never batched.

### /quality-report

Measures the target codebase against thresholds for cyclomatic complexity (> 10), function length (> 50 lines), nesting depth (> 4), argument count (> 5), code duplication (blocks ≥ 5 lines), dead code (uncalled functions), error-handling smells (Rust: `unwrap()`/`expect()` outside tests; Python: bare `except:`), file size (> 500 lines), comment quality (docstrings must say WHAT, not HOW), and reusability (duplicated logic that should be one shared function). Writes a ranked `CODE_QUALITY.md` in the target repo root. Never modifies code.

### /quality-improve

Reads `CODE_QUALITY.md` and fixes exactly ONE finding — the top open one. Runs the project's tests; marks the finding `[x]` on success or `[!]` blocked and reverts on failure. Stops for review after each finding.

## Tools

The skills use `radon`, `ruff`, and `vulture` for Python; `cargo clippy` and `cargo check` for Rust when installed. Each tool is optional. When a tool is not installed, the skill falls back to reading and estimating the metric by hand. The report lists which tools were used and which were missing, so you always know what "measured" means.

For Rust, `cargo clippy` and `cargo check` compile the target crate, so point the plugin at code you trust.

## Test fixtures

`test-fixtures/` holds one deliberately bad file per language with planted problems (high complexity, long functions, deep nesting, many arguments, duplication, dead code, error-handling smells, and poor comments). These files are **intentionally bad** to verify the skills find what they should. Do not use them as examples of good style.

Verify the skills work: run `python3 test-fixtures/python/bad_code.py` or `cd test-fixtures/rust && cargo test` to confirm the fixtures self-check, then run `/quality-report` against the fixtures and verify every planted problem appears in the report.

## Adding a language

Write `skills/quality-report/references/<lang>.md` naming the tools, exact commands, how to parse their output, and the fallback when each tool is absent. Add the language's marker files to the detection list in `skills/quality-report/SKILL.md`. Nothing else. See `docs/superpowers/specs/2026-08-31-codequalityexplorer-design.md` for the full design rationale.
