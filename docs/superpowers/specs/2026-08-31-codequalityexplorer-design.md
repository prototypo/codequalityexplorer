# codequalityexplorer — Design

Date: 2026-08-31
Status: Approved

## Purpose

A Claude Code plugin that measures code quality in a target code base and
helps fix the problems it finds. Two user-invocable skills:

- `/quality-report` — measure the code base and write a ranked report.
- `/quality-improve` — fix the top finding from the report, one at a time.

Initial languages: Python and Rust. The design must make adding a new
language cheap: one new reference file, no other changes.

## Metrics

Measured per function unless noted:

| Metric | Threshold | Source |
|---|---|---|
| Cyclomatic complexity | > 10 | tool |
| Function length | > 50 lines | tool |
| Nesting depth | > 4 levels | tool |
| Argument count | > 5 | tool |
| Code duplication | repeated blocks ≥ 5 lines | tool + Claude |
| Dead code (uncalled functions) | any | tool |
| Error-handling smells | Rust: `unwrap()`/`expect()` outside tests; Python: bare `except:` | tool |
| File size | > 500 lines | tool |
| Comment quality | function-level comment/docstring describes WHAT, not HOW | Claude judgment |
| Reusability | duplicated logic that should be one shared function | Claude judgment |

Thresholds are standard defaults. The report lists them so readers know the
rules being applied.

Deferred (not in v1): test coverage (needs a runnable test suite), coupling
metrics (hard to compute well across languages).

## Approach

Tools first, Claude judgment second:

1. Prefer installed analysis tools for the numeric metrics. Exact,
   fast, repeatable.
2. If a tool is missing, say so in the report and estimate that metric by
   reading the code.
3. Claude alone judges comment quality and reusability — tools cannot.

## Plugin layout

```
codequalityexplorer/
├── .claude-plugin/plugin.json
├── skills/
│   ├── quality-report/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── python.md
│   │       └── rust.md
│   └── quality-improve/
│       └── SKILL.md
└── test-fixtures/
    ├── python/bad_code.py
    └── rust/src/lib.rs (+ Cargo.toml)
```

## /quality-report

1. **Detect languages.** Look for `Cargo.toml`, `pyproject.toml`,
   `setup.py`, and `.rs`/`.py` files. Report every language found;
   analyze the ones with a reference file.
2. **Load reference files** for detected languages. Each reference file
   states: which tools to try, the exact commands, how to read their
   output, and the fallback when the tool is absent.
   - `python.md`: `radon cc` and `radon raw` (complexity, length),
     `ruff` (argument count, smells, dead imports), `vulture` (dead code)
     if present.
   - `rust.md`: `cargo clippy` with `cognitive_complexity`,
     `too_many_arguments`, `too_many_lines` lints; `rust-code-analysis-cli`
     if present; grep for `unwrap()`/`expect()` outside `#[cfg(test)]`.
3. **Claude judgment pass.** Read the flagged files plus a sample of the
   rest. Judge comment quality and reusability.
4. **Write `CODE_QUALITY.md`** in the target repo root. Contents:
   - Summary: languages, files analyzed, tools used, tools missing.
   - Thresholds table.
   - Findings, ranked worst first. Each finding: id, file:line, metric,
     measured value, threshold, one plain-language recommendation, and a
     status checkbox (`[ ]` open, `[x]` fixed).
   - Recommendations section: the 3–5 changes with the biggest payoff.

## /quality-improve

1. Read `CODE_QUALITY.md`. Missing? Stop and tell the user to run
   `/quality-report` first.
2. Take the top open finding.
3. Fix it with the smallest change that resolves the metric without
   making another metric worse.
4. Run the project's tests (`pytest`, `cargo test`, or whatever the
   project uses). Tests fail? Revert the change, record why in the
   report, mark the finding blocked, stop.
5. Tests pass? Mark the finding `[x]` in `CODE_QUALITY.md`, show the
   user the diff, stop. The user re-invokes for the next finding.

One finding per invocation. Never batch.

## Adding a language later

Write `skills/quality-report/references/<lang>.md` naming the tools,
commands, output parsing, and fallback. Add the language's marker files to
the detection list in `quality-report/SKILL.md`. Done.

## Testing

`test-fixtures/` holds one deliberately bad file per language with planted
problems: a function with complexity > 10, a > 50-line function, nesting
> 4, > 5 arguments, a duplicated block pair, a dead function, an
`unwrap()` (Rust) / bare `except:` (Python), and a "how not what" comment.

Verification: run `/quality-report` against the fixtures and check every
planted problem appears in `CODE_QUALITY.md`; run `/quality-improve` and
check it fixes the top finding and updates the report.

## Error handling

- No supported language detected: report says so and stops; no empty report.
- Tool not installed: named in the report's "tools missing" list; metric
  estimated by reading code.
- Target repo has no tests: `/quality-improve` warns, asks the user to
  confirm before changing code without a safety net.
