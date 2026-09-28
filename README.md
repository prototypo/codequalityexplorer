# Code Quality Explorer

A Claude Code plugin that measures code quality in Python, Rust, JavaScript and TypeScript codebases and helps fix the problems it finds, one at a time.

## Installation

**Try it once** (loads for that session only) — start Claude Code in your target repo with:

```bash
claude --plugin-dir </path/to/>codequalityexplorer
```

**Install it permanently** — inside any Claude Code session:

```
/plugin marketplace add prototypo/codequalityexplorer
/plugin install codequalityexplorer@codequalityexplorer
```

The skills are then available in every session as `/quality-report` and `/quality-improve`.

## Usage

Run `/quality-report` first to measure your target codebase. It reads the code and writes a ranked `CODE_QUALITY.md` in the target repo root, listing every finding from worst to best. Then run `/quality-improve` repeatedly. It will address one finding per invocation. Each invocation fixes exactly one finding, runs the project's tests to prove it works, and marks the finding `[x]` on success or `[!]` blocked and reverts on failure.

The supported languages so far are:

- Rust
- Python
- JavaScript
- TypeScript

Please add an issue if you want additional language support.

### /quality-report

Measures the target codebase against thresholds for cyclomatic complexity (> 10), function length (> 50 lines), nesting depth (> 4), argument count (> 5), code duplication (blocks ≥ 5 lines), dead code (uncalled functions), error-handling smells (Rust: `unwrap()`/`expect()` outside tests; Python: bare `except:`; JavaScript/TypeScript: empty or swallowing `catch`), file size (> 500 lines), comment quality (docstrings must say WHAT, not HOW), and reusability (duplicated logic that should be one shared function). Writes a ranked `CODE_QUALITY.md` in the target repo root. Never modifies code.

### /quality-improve

The plugin ships eight agents (developer, developer-heavy, code-reviewer, security-reviewer, security-reviewer-heavy, tester, documenter, project-manager); `/quality-improve` reads `CODE_QUALITY.md` and fixes exactly ONE finding — the top open one, using four of them (developer, code-reviewer, security-reviewer, tester) to fix through review gates. Requires the Agent tool. Marks the finding `[x]` on success or `[!]` blocked and reverts on failure. Stops for review after each finding. On the first fix of a report it asks whether to create a branch (default `quality-improvements`) and remembers the answer — yes or no — for the rest of that report.

## Tools

The skills use `radon`, `ruff`, and `vulture` for Python; `rust-code-analysis-cli`, `cargo clippy`, and `cargo check` for Rust; `eslint` and `jscpd` for JavaScript and TypeScript. When a tool is missing, the skill tells you the install command and asks whether to install it now; only on decline does it fall back to reading and estimating the metric by hand. `rust-code-analysis-cli` is needed for Rust compliance counts (the per-metric 🟢/🟡/🔴 breakdowns), so declining it leaves those counts estimated. The report lists which tools were used and which were missing, so you always know what "measured" means.

For Python, `scripts/function_metrics.py` (stdlib-only, no install needed) measures every function's length, nesting depth, argument count, and comment presence directly via the AST, giving the compliance-count denominator for those metrics.

For JavaScript and TypeScript, `scripts/function_metrics.mjs` does the same — plus complexity — for both languages. It needs Node.js and the `typescript` package as a parser (pinned to `typescript@6`; version 7 dropped the parser API it uses).

The npm tools install beside the skill, never in the target repo: `npm install --prefix "<skill dir>" --no-save --ignore-scripts eslint@9 typescript@6 typescript-eslint@8 jscpd@5`, and are then invoked by absolute path. Installing into the target repo would run that repo's own install scripts, and `npx` would let it substitute its own binaries.

For Rust, `cargo clippy` and `cargo check` compile the target crate, so point the plugin at code you trust.

The report's Metrics table shows a Status and Compliance column per metric (e.g. `🟢 95% pass` status with `🟢 39 · 🟡 2 · 🔴 2` compliance counts — 🟡 items count as passing, so 41/43 pass), a Marginal section listing functions/files close to a threshold with no finding, and a disclaimer paragraph noting which counts are measured versus estimated. Status reflects the whole row's compliance ratio and worst value against fixed bands, not just the single worst item, and each Status cell carries a short reason.

## What 🟢 🟡 🔴 mean

Two different things carry a colour, and conflating them is the usual
confusion:

- **An item** — one function, one file — is 🔴 if it is over the threshold,
  🟡 if it is within 10% below it, 🟢 otherwise. These are what the
  Compliance column counts and what the findings list.
- **A row** is scored on the whole distribution, using the bands below. A
  row can read 🟢 while still containing 🔴 items: the row says the spread
  is healthy, not that there is nothing to fix.

"Ratio" below means the share of items that pass — and **a 🟡 item counts
as passing**, so only 🔴 items reduce it.

### Row bands

| Metric | 🟢 | 🟡 | 🔴 |
|---|---|---|---|
| Cyclomatic complexity, function length, nesting depth, file size | ratio ≥ 95% | ratio ≥ 80% | ratio < 80%, **or** worst ≥ 5× threshold |
| Argument count | ratio ≥ 95% | ratio ≥ 90% | ratio < 90%, **or** worst > 12 args (2.5× threshold) |
| Comment quality | ≥ 95% | ≥ 80% | < 80% |
| Dead code (used functions ÷ all functions) | ≥ 98% | ≥ 95% | < 95% |
| Error-handling smells (per 1,000 lines) | ≤ 0.5 | ≤ 2 | > 2 |
| Code duplication (% of lines duplicated) | < 3% | < 5% | ≥ 5% |
| Reusability | same as duplication | | |

Argument count has its own band because the metric's natural scale is
smaller: 5× the complexity threshold is 50 branches, but 5× the argument
threshold would be 25 parameters, which no real function reaches. Without a
separate band the row could never go red on its worst value.

**🔴 is checked first.** A row reads 🔴 if either trigger fires — the ratio
below its floor, or the worst value at or past its multiple — even when the
other would have said 🟢. Then 🟢 (ratio ≥ 95%), then 🟡.

### Item bands (the 10% rule)

🟡 means a measured value within 10% below its threshold:

| Metric | 🟢 | 🟡 | 🔴 |
|---|---|---|---|
| Cyclomatic complexity | ≤ 9 | exactly 10 | > 10 |
| Function length | ≤ 45 | 46–50 | > 50 |
| Nesting depth | ≤ 3 | exactly 4 | > 4 |
| Argument count | ≤ 4 | exactly 5 | > 5 |
| File size | ≤ 450 | 451–500 | > 500 |

Dead code, error-handling smells, duplication, reusability and comment
quality have no per-item 🟡 — an item either is or is not.

### Worked examples

200 functions measured for complexity, threshold 10:

| Situation | Ratio | Worst | Row |
|---|---|---|---|
| one function at complexity 25 | 99.5% | 2.5× | 🟢 99.5% pass |
| one function at complexity 50 | 99.5% | **5×** | 🔴 worst 5× limit |
| thirty functions at complexity 11 | **85%** | 1.1× | 🟡 85% pass |

And for argument count, threshold 5: 15 of 200 functions at 6 arguments
gives 92.5% — between that row's 90% and 95% bands → 🟡 92.5% pass.

Subagents come from [Claude Dev Pipeline](https://github.com/prototypo/claude-dev-pipeline).

The agents are generic and need adjusting for your own project — its test commands, conventions, and security-critical paths. You can ask Claude to do that for you. For this plugin to work well, give your project a `CLAUDE.md` that follows the sample in [Claude Dev Pipeline](https://github.com/prototypo/claude-dev-pipeline); it tells the agents how to route work (for example, when to use the heavy developer and security-reviewer variants).

## Test fixtures

`test-fixtures/` holds deliberately bad files per language (JavaScript and TypeScript have one each) with planted problems (high complexity, long functions, deep nesting, many arguments, duplication, dead code, error-handling smells, and poor comments). These files are **intentionally bad** to verify the skills find what they should. Do not use them as examples of good style.

Verify the skills work: run `python3 test-fixtures/python/bad_code.py` or `cd test-fixtures/rust && cargo test` to confirm the fixtures self-check (the JavaScript/TypeScript fixtures are checked by `python3 -m pytest skills/quality-report/scripts/`), then run `/quality-report` against the fixtures and verify every planted problem appears in the report.

## Adding a language

Write `skills/quality-report/references/<lang>.md` naming the tools, exact commands, how to parse their output, and the fallback when each tool is absent. Add the language's marker files and extensions to the detection list in `skills/quality-report/SKILL.md`. If no tool measures every function in that language, add a `scripts/function_metrics.<ext>` that does — the compliance counts need a denominator covering the whole codebase, not just the violations. Then add a deliberately bad fixture under `test-fixtures/<lang>/` with a planted problem for each per-function metric the script measures (file size is not planted in any existing fixture), and a test that asserts the script finds each one. See `docs/superpowers/specs/2026-08-31-codequalityexplorer-design.md` for the full design rationale.

`.claude/agents` is a symlink to `agents/`, so the plugin and this repo's own local workflow share one copy of the agent files.
