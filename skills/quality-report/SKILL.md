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
   list.

3. **Offer to install missing tools.** For each tool from step 2 that is
   missing, tell the user the exact install command and ask whether to
   install it now:
   - `pip install radon ruff vulture`
   - `cargo install rust-code-analysis-cli`
   If the user declines, use the reference file's fallback for that tool
   and mark the affected counts "estimated".

4. **Measure everything, not just violations.** Run the tools per the
   reference files AND `scripts/function_metrics.py <paths>` to get
   per-function length, nesting, argument count, and comment-presence
   values for the whole code base. Classify each function/file 🟢/🟡/🔴
   against the thresholds table using the 10% rule: 🟡 = measured value
   within 10% below the threshold (e.g. complexity exactly 10, length
   46–50, nesting exactly 4, args exactly 5, file size 451–500). Binary
   metrics — dead code, error-handling smells, duplication, reusability,
   comment quality — have no yellow, only 🟢/🔴. Every threshold violation
   still becomes a finding exactly as before.

5. **Judgment pass.** Read every file that has a tool finding, plus up to 10
   of the largest remaining source files. Comment *presence* counts
   (from step 4) come from the script/tool for every function; only
   comment *quality* (WHAT vs HOW) is judged here, on this sample. Judge:
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

6. **Write `CODE_QUALITY.md`** in the target repo root using the template
   below. Rank findings worst first: order by (how far past the threshold,
   how many readers the file likely has — entry points and public APIs
   first). Give each finding an id Q1, Q2, ... in rank order. If a
   `CODE_QUALITY.md` already exists, carry forward its `[!]` blocked markers
   and their notes for findings that still apply; write everything else
   fresh as `[ ]`.

7. Tell the user: the report path, the top 3 findings in one line each, and
   that `/quality-improve` fixes them one at a time.

## Report template

```markdown
# Code Quality Report

Generated: <YYYY-MM-DD> by quality-report v0.2.0

## Summary

- Languages analyzed: <list>
- Files analyzed: <n>
- Tools used: <name and version, one per line>
- Tools missing: <name — metric estimated by reading code; or "none">
- Findings: <n> open

## Metrics

| Metric | Threshold | Status | Compliance | Source |
|---|---|---|---|---|
| Cyclomatic complexity | > 10 | 🟡 | 🟢 41 · 🟡 2 · 🔴 0 | tool |

Fill one row per metric from the thresholds table above. Status is the
worst item in that row: any 🔴 → 🔴; else any 🟡 → 🟡; else 🟢. Compliance
counts functions for function metrics (complexity, length, nesting, args,
comment quality), files for file size, occurrences for error-handling
smells, and duplicate-block groups for duplication/reusability. Binary
metrics (dead code, error-handling smells, duplication, reusability) have
no yellow: show `🔴 n` or `🟢 none`, with no denominator.

Comment counts are parsed from every function in the code base; comment
*quality* and the other judgment metrics (reusability, suppressed
problems) are judged on a sample only — the files with findings, plus up
to 10 of the largest remaining source files. "estimated" in the Source
column marks a count made by reading code instead of by a tool.

Comment-quality compliance is denominated over functions longer than 10
lines only, and is binary (🟢/🔴, no 🟡): does the function have a
WHAT-comment or not. The presence count comes from `function_metrics.py`'s
`has_doc` field for every such function in the code base; comment
*quality* (WHAT vs HOW) is judged only on the step 5 sample, per the
disclaimer above.

## Findings (worst first)

### [ ] 🔴 Q1: <metric> — <file>:<line> `<function>`

- Measured: <value> (threshold <value>)
- Recommendation: <one or two plain sentences saying what change to make>

### [ ] 🔴 Q2: ...

## Marginal (🟡) — close to the limit, no action required

- Cyclomatic complexity 10 (limit 10) — src/foo.py:12 `bar`

## Top recommendations

1. <the 3–5 changes with the biggest payoff, each one sentence>
```

Status markers on findings: `[ ]` open, `[x]` fixed, `[!]` blocked. The
marker always comes first, with the emoji after it — `quality-improve`
parses `[ ]`/`[x]`/`[!]` by position, so never move the marker. The
quality-improve skill updates these; this skill writes them all as `[ ]`.

The Marginal section lists every 🟡 function/file that has no threshold
violation, one line each, with no Q id and no `[ ]` marker — so
`quality-improve` never picks these up. A function's 🟡 listing is decided
solely by its own metric measurement, regardless of whether that same
function also appears in a judgment finding (e.g. duplication) elsewhere
in the report.

## Adding a language

Write `references/<lang>.md` (tools, exact commands, output parsing,
fallback) and add the language's marker files to step 1. Nothing else.
