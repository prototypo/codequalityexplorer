---
name: quality-report
description: Use when the user asks for a code quality report, code metrics, complexity analysis, or invokes /quality-report - measures complexity, function length, nesting, argument counts, duplication, dead code, error-handling smells, comment quality, and reusability, then writes a ranked CODE_QUALITY.md
---

# Quality Report

Measure the target code base and write a ranked report to `CODE_QUALITY.md`
in the repo root. This skill changes NO code. It only reads and reports.

## Thresholds

| Metric | Threshold | Source |
|---|---|---|
| Cyclomatic complexity | > 10 | tool |
| Function length | > 50 lines | tool |
| Nesting depth | > 4 levels | tool |
| Argument count | > 5 | tool |
| Code duplication | repeated blocks ≥ 5 lines | tool + judgment |
| Dead code (uncalled functions) | any | tool |
| Error-handling smells | Rust: `unwrap()`/`expect()` outside `#[cfg(test)]`; Python: bare `except:` | tool |
| File size | > 500 lines | tool |
| Comment quality | for functions longer than 10 lines, comment/docstring must say WHAT, not HOW | judgment |
| Reusability | duplicated logic that should be one shared function | judgment |

## Steps

1. **Detect languages.** In the target repo root, check for:
   - Python: `pyproject.toml`, `setup.py`, `requirements.txt`, or any `*.py` files.
   - Rust: `Cargo.toml` or any `*.rs` files.
   If no supported language is found, tell the user and STOP. Write no report.
   If a language is present but has no reference file in `references/`, name it
   in the report summary as detected-but-unsupported.

2. **Load the reference file** for each detected language:
   `references/python.md`, `references/rust.md`. Follow its tool commands.
   For every tool that is not installed, record it in the "Tools missing"
   list and use the reference file's fallback (read the code and estimate).

3. **Run the tools** per the reference files. Collect every threshold
   violation as a finding.

4. **Judgment pass.** Read every file that has a tool finding, plus up to 10
   of the largest remaining source files. Judge:
   - **Comment quality:** for each function longer than 10 lines, does its
     docstring/comment state WHAT the function does? A comment narrating the
     implementation steps ("loop over X, then append to Y") is a HOW comment:
     flag it. A missing docstring on a public function longer than 10 lines:
     flag it.
   - **Reusability:** blocks of ≥ 5 similar lines appearing in 2+ places,
     or 2+ functions with near-identical bodies. Flag as one finding naming
     all copies and the shared function that should replace them.
   - Suppressed problems (Python `# noqa`, Rust `#[allow(...)]`) still count:
     report them, note the suppression.

5. **Write `CODE_QUALITY.md`** in the target repo root using the template
   below. Rank findings worst first: order by (how far past the threshold,
   how many readers the file likely has — entry points and public APIs
   first). Give each finding an id Q1, Q2, ... in rank order. If a
   `CODE_QUALITY.md` already exists, carry forward its `[!]` blocked markers
   and their notes for findings that still apply; write everything else
   fresh as `[ ]`.

6. Tell the user: the report path, the top 3 findings in one line each, and
   that `/quality-improve` fixes them one at a time.

## Report template

```markdown
# Code Quality Report

Generated: <YYYY-MM-DD> by quality-report v0.1.0

## Summary

- Languages analyzed: <list>
- Files analyzed: <n>
- Tools used: <name and version, one per line>
- Tools missing: <name — metric estimated by reading code; or "none">
- Findings: <n> open

## Thresholds

<copy the thresholds table from this skill verbatim>

## Findings (worst first)

### [ ] Q1: <metric> — <file>:<line> `<function>`

- Measured: <value> (threshold <value>)
- Recommendation: <one or two plain sentences saying what change to make>

### [ ] Q2: ...

## Top recommendations

1. <the 3–5 changes with the biggest payoff, each one sentence>
```

Status markers on findings: `[ ]` open, `[x]` fixed, `[!]` blocked.
The quality-improve skill updates these; this skill writes them all as `[ ]`.

## Adding a language

Write `references/<lang>.md` (tools, exact commands, output parsing,
fallback) and add the language's marker files to step 1. Nothing else.
