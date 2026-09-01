# codequalityexplorer Implementation Plan

> **Note:** The report template described in Task 4 was superseded in v0.2.0; see `skills/quality-report/SKILL.md` for the current format (Metrics table with Status/Compliance columns, Marginal section, disclaimer).

> **Note:** The test-command discovery described in Task 5's quality-improve step 3 was extended in v0.4.1 to JavaScript/TypeScript repos (package.json `"test"` script, run via pnpm/yarn/npm per lockfile); see `skills/quality-improve/SKILL.md` step 4 for the current order.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code plugin with two skills — `/quality-report` (measure a code base, write a ranked `CODE_QUALITY.md`) and `/quality-improve` (fix the top open finding, one per invocation).

**Architecture:** A plugin whose skills are instruction files. `quality-report` detects languages, runs installed analysis tools per language (described in per-language reference files), adds Claude judgment for comment quality and reusability, and writes a ranked report. `quality-improve` reads that report and fixes one finding, guarded by the target project's tests. Test fixtures with planted problems verify both skills.

**Tech Stack:** Claude Code plugin format (plugin.json + SKILL.md files). Analysis tools invoked at runtime if installed: `radon`, `ruff`, `vulture` (Python); `cargo clippy` (Rust). No build step in this repo itself except `cargo check` for the Rust fixture.

**Spec:** `docs/superpowers/specs/2026-08-31-codequalityexplorer-design.md`

## Global Constraints

- Thresholds (from spec, repeat verbatim in the report): cyclomatic complexity > 10, function > 50 lines, nesting > 4 levels, > 5 arguments, duplicated blocks ≥ 5 lines, file > 500 lines.
- Error-handling smells: Rust `unwrap()`/`expect()` outside `#[cfg(test)]`; Python bare `except:`.
- `/quality-report` never modifies target code. `/quality-improve` fixes exactly one finding per invocation.
- Adding a language later must require only a new `references/<lang>.md` plus one line in the detection list.
- Report file is always `CODE_QUALITY.md` in the target repo root.

---

### Task 1: Plugin scaffold

**Files:**
- Create: `.claude-plugin/plugin.json`

**Interfaces:**
- Produces: plugin named `codequalityexplorer`; later tasks add skills under `skills/`.

- [ ] **Step 1: Write plugin.json**

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "codequalityexplorer",
  "description": "Code quality reporting and guided improvement for Python and Rust",
  "version": "0.1.0",
  "author": {
    "name": "David Hyland-Wood"
  }
}
```

- [ ] **Step 2: Verify it is valid JSON**

Run: `python3 -m json.tool .claude-plugin/plugin.json`
Expected: the JSON echoed back, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: plugin scaffold"
```

---

### Task 2: Python test fixture

**Files:**
- Create: `test-fixtures/python/bad_code.py`

**Interfaces:**
- Produces: a syntactically valid Python file containing every planted problem Task 6 checks for: complexity > 10, function > 50 lines, nesting > 4, 7 arguments, duplicated ≥5-line block pair, dead function, bare `except:`, a "how not what" comment.

- [ ] **Step 1: Write the fixture**

Create `test-fixtures/python/bad_code.py` exactly:

```python
"""Deliberately bad code. Fixture for testing the quality-report skill.

Planted problems:
- process_data: complexity > 10, length > 50 lines, nesting > 4,
  and a comment that describes HOW instead of WHAT.
- build_report: 7 arguments.
- summarize_sales / summarize_refunds: duplicated >= 5-line block.
- legacy_export: dead (never called) and uses a bare except.
"""


def process_data(data):
    # Loop through the items, use nested ifs to inspect each field,
    # and append the transformed value to the results list.
    results = []
    for item in data:
        if item is not None:
            if isinstance(item, dict):
                if "value" in item:
                    if item["value"] > 0:
                        if item["value"] < 100:
                            results.append(item["value"] * 2)
                        else:
                            results.append(100)
                    else:
                        results.append(0)
                elif "name" in item:
                    if item["name"]:
                        results.append(len(item["name"]))
                    else:
                        results.append(-1)
                elif "flag" in item:
                    if item["flag"] is True:
                        results.append(1)
                    else:
                        results.append(0)
                else:
                    results.append(None)
            elif isinstance(item, list):
                if len(item) > 10:
                    results.append(sum(item[:10]))
                elif len(item) > 5:
                    results.append(sum(item[:5]))
                elif len(item) > 0:
                    results.append(item[0])
                else:
                    results.append(0)
            elif isinstance(item, str):
                if item.startswith("A"):
                    results.append(1)
                elif item.startswith("B"):
                    results.append(2)
                elif item.startswith("C"):
                    results.append(3)
                else:
                    results.append(0)
            elif isinstance(item, int):
                if item % 2 == 0:
                    results.append(item // 2)
                else:
                    results.append(item * 3 + 1)
            else:
                results.append(None)
    return results


def build_report(name, date, author, title, status, priority, category):
    """Build a report dictionary from its parts."""
    return {
        "name": name,
        "date": date,
        "author": author,
        "title": title,
        "status": status,
        "priority": priority,
        "category": category,
    }


def summarize_sales(records):
    """Return the average positive sale amount."""
    total = 0
    count = 0
    for record in records:
        if record["amount"] > 0:
            total += record["amount"]
            count += 1
    return total / count if count else 0


def summarize_refunds(records):
    """Return the average positive refund amount."""
    total = 0
    count = 0
    for record in records:
        if record["amount"] > 0:
            total += record["amount"]
            count += 1
    return total / count if count else 0


def legacy_export(records):
    """Export records as strings."""
    try:
        return [str(record) for record in records]
    except:
        return []


if __name__ == "__main__":
    sample = [{"value": 5}, [1, 2, 3], "Apple", 7, None]
    assert process_data(sample) == [10, 1, 1, 22]
    assert summarize_sales([{"amount": 10}, {"amount": -2}]) == 10
    assert summarize_refunds([{"amount": 4}, {"amount": 6}]) == 5
    print("fixture self-check ok")
```

- [ ] **Step 2: Verify it compiles and the self-check passes**

Run: `python3 test-fixtures/python/bad_code.py`
Expected: `fixture self-check ok`, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add test-fixtures/python/bad_code.py
git commit -m "feat: Python fixture with planted quality problems"
```

---

### Task 3: Rust test fixture

**Files:**
- Create: `test-fixtures/rust/Cargo.toml`
- Create: `test-fixtures/rust/src/lib.rs`

**Interfaces:**
- Produces: a compiling Rust crate containing every planted problem Task 6 checks for: complexity > 10, function > 50 lines, nesting > 4, 8 arguments, duplicated ≥5-line block pair, dead function, `unwrap()` outside tests, a "how not what" comment.

- [ ] **Step 1: Write Cargo.toml**

Create `test-fixtures/rust/Cargo.toml`:

```toml
[package]
name = "bad_code"
version = "0.1.0"
edition = "2021"

[lib]
```

- [ ] **Step 2: Write the fixture**

Create `test-fixtures/rust/src/lib.rs` exactly:

```rust
//! Deliberately bad code. Fixture for testing the quality-report skill.
//!
//! Planted problems:
//! - process_values: complexity > 10, length > 50 lines, nesting > 4,
//!   and a comment that describes HOW instead of WHAT.
//! - build_label: 8 arguments.
//! - average_sales / average_refunds: duplicated >= 5-line block.
//! - legacy_parse: dead (never called) and calls unwrap().
//! - first_value: calls unwrap() outside test code.

/// Iterate the slice, use nested ifs on each value, and push the
/// transformed number into the output vector.
pub fn process_values(values: &[i64]) -> Vec<i64> {
    let mut results = Vec::new();
    for v in values {
        if *v > 0 {
            if *v < 100 {
                if v % 2 == 0 {
                    if v % 4 == 0 {
                        if v % 8 == 0 {
                            results.push(v / 8);
                        } else {
                            results.push(v / 4);
                        }
                    } else {
                        results.push(v / 2);
                    }
                } else if v % 3 == 0 {
                    results.push(v / 3);
                } else if v % 5 == 0 {
                    results.push(v / 5);
                } else {
                    results.push(*v);
                }
            } else if *v < 1000 {
                if v % 10 == 0 {
                    results.push(v / 10);
                } else {
                    results.push(v % 100);
                }
            } else if *v < 10000 {
                results.push(v / 100);
            } else {
                results.push(9999);
            }
        } else if *v < 0 {
            if *v > -100 {
                results.push(-v);
            } else if *v > -1000 {
                results.push(-v / 10);
            } else {
                results.push(0);
            }
        } else {
            results.push(0);
        }
    }
    results
}

/// Build a display label for an item.
#[allow(clippy::too_many_arguments)]
pub fn build_label(
    name: &str,
    code: u32,
    region: &str,
    tier: u8,
    active: bool,
    priority: u8,
    owner: &str,
    notes: &str,
) -> String {
    format!("{name}-{code}-{region}-{tier}-{active}-{priority}-{owner}-{notes}")
}

/// Return the average positive sale amount.
pub fn average_sales(amounts: &[f64]) -> f64 {
    let mut total = 0.0;
    let mut count = 0u32;
    for a in amounts {
        if *a > 0.0 {
            total += a;
            count += 1;
        }
    }
    if count == 0 {
        0.0
    } else {
        total / f64::from(count)
    }
}

/// Return the average positive refund amount.
pub fn average_refunds(amounts: &[f64]) -> f64 {
    let mut total = 0.0;
    let mut count = 0u32;
    for a in amounts {
        if *a > 0.0 {
            total += a;
            count += 1;
        }
    }
    if count == 0 {
        0.0
    } else {
        total / f64::from(count)
    }
}

/// Parse a number from text.
#[allow(dead_code)]
fn legacy_parse(input: &str) -> i64 {
    input.trim().parse::<i64>().unwrap()
}

/// Return the first value in the slice.
pub fn first_value(values: &[i64]) -> i64 {
    *values.first().unwrap()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixture_self_check() {
        assert_eq!(process_values(&[8, 3, 150, -50]), vec![1, 1, 15, 50]);
        assert_eq!(average_sales(&[10.0, -2.0]), 10.0);
        assert_eq!(average_refunds(&[4.0, 6.0]), 5.0);
        assert_eq!(first_value(&[7]), 7);
    }
}
```

Note: `#[allow(dead_code)]` and `#[allow(clippy::too_many_arguments)]` keep the fixture compiling without warnings-as-noise, while the problems stay visibly present in the source for the skill to find by reading and by grep. The skill's Rust reference tells it to treat `#[allow(...)]` markers as suppressed-but-present problems.

- [ ] **Step 3: Verify it compiles and the self-check passes**

Run: `cd test-fixtures/rust && cargo test && cd ../..`
Expected: `fixture_self_check ... ok`, exit code 0. If `cargo` is not installed, run nothing, note it, and continue — Task 6 handles the no-cargo case.

- [ ] **Step 4: Commit**

```bash
git add test-fixtures/rust
git commit -m "feat: Rust fixture with planted quality problems"
```

---

### Task 4: quality-report skill

**Files:**
- Create: `skills/quality-report/SKILL.md`
- Create: `skills/quality-report/references/python.md`
- Create: `skills/quality-report/references/rust.md`

**Interfaces:**
- Consumes: nothing from earlier tasks (fixtures are used by Task 6).
- Produces: the `/quality-report` skill. Its output contract, which Task 5 depends on: `CODE_QUALITY.md` in the target repo root, findings formatted as `### [ ] Q<n>: <metric> — <file>:<line> \`<function>\`` ranked worst first, `[ ]` open / `[x]` fixed / `[!]` blocked.

- [ ] **Step 1: Write SKILL.md**

Create `skills/quality-report/SKILL.md` exactly:

````markdown
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
| Comment quality | function comment/docstring must say WHAT, not HOW | judgment |
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
   first). Give each finding an id Q1, Q2, ... in rank order.

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
````

- [ ] **Step 2: Write references/python.md**

Create `skills/quality-report/references/python.md` exactly:

````markdown
# Python analysis

Run from the target repo root. `<paths>` = the Python source directories
(skip `.venv`, `venv`, `build`, `dist`, `.tox`).

## Tools, in order

### radon — complexity and raw metrics

Check: `radon --version`

- Complexity per function: `radon cc -s -j <paths>`
  JSON: each entry has `name`, `lineno`, `complexity`. Finding when
  `complexity > 10`.
- File sizes: `radon raw -j <paths>` — `loc` per file. Finding when > 500.

### ruff — argument count, statement count, nesting, bare except

Check: `ruff --version`

Run: `ruff check --isolated --select C901,PLR0913,PLR0915,PLR1702,E722 --preview --output-format json <paths>`

- `C901` complexity > 10 (backup if radon missing)
- `PLR0913` more than 5 arguments
- `PLR0915` more than 50 statements — treat as the function-length metric
- `PLR1702` too many nested blocks — treat as nesting > 4 (ruff's default
  trigger is 5 nested blocks, which matches "more than 4")
- `E722` bare `except:`

JSON rows have `filename`, `location.row`, `code`, `message`.

### vulture — dead code

Check: `vulture --version`

Run: `vulture <paths> --min-confidence 80`
Each output line `file:line: unused function 'name'` is a dead-code finding.

## Fallbacks (tool missing)

- radon and ruff both missing: read each source file. Estimate complexity by
  counting branch keywords (`if`, `elif`, `for`, `while`, `except`, `and`,
  `or`, `case`) per function + 1; count function length and nesting depth
  directly. Mark these findings "estimated".
- vulture missing: grep each module-level function name across the repo
  (`grep -rn "name(" --include="*.py"`); a function whose name appears only
  at its own definition is likely dead. Mark "estimated"; skip names that
  look like framework entry points (`main`, `test_*`, dunder methods).

## Duplication (no tool assumed)

Read files with findings plus the largest files. Look for function bodies or
blocks of ≥ 5 similar lines appearing 2+ times. This is a judgment metric;
pair each duplication finding with a reusability recommendation naming the
shared function to extract.
````

- [ ] **Step 3: Write references/rust.md**

Create `skills/quality-report/references/rust.md` exactly:

````markdown
# Rust analysis

Run from the directory containing the target `Cargo.toml`.

## Tools, in order

### cargo clippy — complexity, length, arguments, unwrap

Check: `cargo clippy --version`

Run:

```bash
cargo clippy --message-format short -- \
  -W clippy::cognitive_complexity \
  -W clippy::too_many_lines \
  -W clippy::too_many_arguments \
  -W clippy::excessive_nesting \
  -W clippy::unwrap_used \
  -W clippy::expect_used 2>&1
```

- `cognitive_complexity` → complexity finding. Clippy's threshold is 25;
  ALSO apply the skill threshold (> 10) during the reading pass, since
  clippy under-reports against our bar.
- `too_many_lines` → function length (clippy default 100; also apply > 50
  during the reading pass).
- `too_many_arguments` → argument count (clippy default 7; also apply > 5
  during the reading pass).
- `excessive_nesting` requires clippy.toml (`excessive-nesting-threshold = 4`);
  if you cannot write one, measure nesting during the reading pass instead.
  Never leave config files behind in the target repo.
- `unwrap_used` / `expect_used` → error-handling smell, EXCEPT hits inside
  `#[cfg(test)]` modules or `#[test]` functions — ignore those.

Some of these lints are nursery/restriction lints; if a `-W` flag is
rejected by the installed clippy, drop that flag and cover the metric in
the reading pass.

### grep — unwrap/expect backup

If clippy is missing:

```bash
grep -rn '\.unwrap()\|\.expect(' src --include='*.rs'
```

Then open each hit and discard those inside `#[cfg(test)]` modules or
`#[test]` functions.

### rustc dead code

`cargo check 2>&1` — `dead_code` warnings are dead-code findings. A
`#[allow(dead_code)]` attribute suppresses the warning but the finding still
counts: check for that attribute while reading.

## Fallbacks (cargo missing entirely)

Read each `.rs` file. Estimate complexity by counting branch keywords
(`if`, `else if`, `match` arms, `for`, `while`, `&&`, `||`, `?`) per
function + 1; count function length and nesting depth directly; grep for
`unwrap()`/`expect(` as above. Mark these findings "estimated".

## Suppressions

`#[allow(clippy::...)]` and `#[allow(dead_code)]` hide problems from tools
but not from this skill: while reading flagged files, report suppressed
problems and note the suppression in the finding.

## Duplication (no tool assumed)

Read files with findings plus the largest files. Look for function bodies or
blocks of ≥ 5 similar lines appearing 2+ times. Pair each duplication
finding with the shared function that should replace the copies.
````

- [ ] **Step 4: Verify frontmatter and file presence**

Run: `head -5 skills/quality-report/SKILL.md && ls skills/quality-report/references/`
Expected: frontmatter opens with `---` and a `name: quality-report` line; listing shows `python.md rust.md`.

- [ ] **Step 5: Commit**

```bash
git add skills/quality-report
git commit -m "feat: quality-report skill with Python and Rust references"
```

---

### Task 5: quality-improve skill

**Files:**
- Create: `skills/quality-improve/SKILL.md`

**Interfaces:**
- Consumes: `CODE_QUALITY.md` in the format Task 4 defines (findings `### [ ] Q<n>: ...`, markers `[ ]`/`[x]`/`[!]`).
- Produces: the `/quality-improve` skill.

- [ ] **Step 1: Write SKILL.md**

Create `skills/quality-improve/SKILL.md` exactly:

````markdown
---
name: quality-improve
description: Use when the user asks to fix code quality findings, act on a code quality report, or invokes /quality-improve - fixes the single top open finding from CODE_QUALITY.md, runs the tests, and stops for review
---

# Quality Improve

Fix exactly ONE finding from `CODE_QUALITY.md`, prove the tests still pass,
and stop. Never batch findings. The user re-invokes this skill for the next
one.

## Steps

1. **Read `CODE_QUALITY.md`** in the target repo root. If it does not
   exist, tell the user to run `/quality-report` first and STOP.

2. **Pick the finding.** The first finding whose marker is `[ ]` (open).
   Skip `[x]` (fixed) and `[!]` (blocked). If none are open, say the report
   is complete and suggest re-running `/quality-report` to re-measure. STOP.

3. **Find the test command.** In order: a project-specific command in the
   repo's CLAUDE.md; `pytest` if pyproject.toml/tests/ exist; `cargo test`
   if Cargo.toml exists. If the repo has NO tests, warn the user that you
   would be changing code with no safety net, and ask for explicit
   confirmation before continuing.

4. **Ensure a clean revert point.** If the working tree has uncommitted
   changes in files you will touch, stop and ask the user to commit or
   stash first. Otherwise note the current state (`git status`) so the fix
   can be reverted with `git checkout -- <files>`.

5. **Fix the finding.** The smallest change that brings the metric under
   its threshold without pushing any other metric over its threshold:
   - Complexity / length / nesting: extract coherent branches into named
     helper functions with docstrings saying WHAT each does.
   - Argument count: group related parameters into a small struct /
     dataclass, or split the function.
   - Duplication / reusability: extract ONE shared function; make all
     copies call it.
   - Dead code: delete the function. If it looks like a public API other
     repos might call, mark the finding `[!]` blocked with a note instead,
     and STOP (report this to the user).
   - Error-handling smells: replace `unwrap()`/`expect()` with `?` or an
     explicit match returning a sensible error; replace bare `except:` with
     the narrowest exception type the body can actually raise.
   - Comment quality: rewrite the comment/docstring to state WHAT the
     function does and why a caller would use it. Delete step-by-step HOW
     narration.

6. **Run the tests.**
   - PASS: mark the finding `[x]` in `CODE_QUALITY.md`.
   - FAIL: revert the change (`git checkout -- <files>` on the files you
     touched, but never revert `CODE_QUALITY.md` bookkeeping), mark the
     finding `[!]` with a one-line reason appended to the finding, and
     report the test output.

7. **Stop and show the user:** the finding fixed (or blocked and why), the
   diff (`git diff` output for the touched files), and how many open
   findings remain. Do not start the next finding.
````

- [ ] **Step 2: Verify frontmatter**

Run: `head -5 skills/quality-improve/SKILL.md`
Expected: frontmatter opens with `---` and a `name: quality-improve` line.

- [ ] **Step 3: Commit**

```bash
git add skills/quality-improve
git commit -m "feat: quality-improve skill"
```

---

### Task 6: End-to-end verification against fixtures

**Files:**
- Create: none in the repo (work happens on a scratch copy)

**Interfaces:**
- Consumes: fixtures (Tasks 2–3), both skills (Tasks 4–5).

- [ ] **Step 1: Make a scratch copy of the fixtures**

```bash
SCRATCH=$(mktemp -d)
cp -r test-fixtures "$SCRATCH/target"
cd "$SCRATCH/target"
git init -q && git add -A && git commit -qm "fixture baseline"
```

- [ ] **Step 2: Execute the quality-report skill on the scratch copy**

Open `skills/quality-report/SKILL.md` (in the plugin repo) and follow its
steps with `$SCRATCH/target` as the target repo, exactly as the skill would
run: detect languages, run the reference-file tool commands for whichever of
radon/ruff/vulture/cargo are installed, use the documented fallbacks for the
rest, do the judgment pass, and write `$SCRATCH/target/CODE_QUALITY.md`.

- [ ] **Step 3: Check every planted problem was found**

Verify `CODE_QUALITY.md` contains a finding for each row. Any missed row is
a bug in the skill or reference file: fix the skill text, re-run Step 2.

| Planted problem | Expected finding |
|---|---|
| `bad_code.py` `process_data` | complexity > 10 |
| `bad_code.py` `process_data` | length > 50 lines |
| `bad_code.py` `process_data` | nesting > 4 |
| `bad_code.py` `process_data` comment | HOW-comment (comment quality) |
| `bad_code.py` `build_report` | 7 arguments |
| `bad_code.py` `summarize_sales`/`summarize_refunds` | duplication/reusability |
| `bad_code.py` `legacy_export` | dead code |
| `bad_code.py` `legacy_export` | bare except |
| `lib.rs` `process_values` | complexity > 10 |
| `lib.rs` `process_values` | length > 50 lines |
| `lib.rs` `process_values` | nesting > 4 |
| `lib.rs` `process_values` doc comment | HOW-comment (comment quality) |
| `lib.rs` `build_label` | 8 arguments (suppression noted) |
| `lib.rs` `average_sales`/`average_refunds` | duplication/reusability |
| `lib.rs` `legacy_parse` | dead code (suppression noted) |
| `lib.rs` `legacy_parse`, `first_value` | unwrap outside tests |

Also verify: findings are ranked with ids Q1..Qn, every marker is `[ ]`, the
summary lists tools used and tools missing, and the thresholds table is
present.

- [ ] **Step 4: Execute the quality-improve skill once**

Follow `skills/quality-improve/SKILL.md` against the scratch copy. Expected:
it fixes exactly finding Q1, runs the fixture tests
(`python3 test-fixtures/python/bad_code.py` self-check and/or `cargo test`),
marks Q1 `[x]`, shows a diff, and stops without touching Q2.

- [ ] **Step 5: Check the improve contract held**

Verify in the scratch copy: only files named in Q1 changed (plus
`CODE_QUALITY.md`); Q1 is `[x]`; all other findings still `[ ]`; the
fixture self-checks still pass.

- [ ] **Step 6: Record the verification and clean up**

```bash
cd /Users/davidhyland-wood/Documents/GitHub/codequalityexplorer
rm -rf "$SCRATCH"
```

Fix any skill-text bugs found during Steps 2–5, then:

```bash
git add -A
git commit -m "test: verify skills end-to-end against fixtures"
```

(If no skill text changed, skip the commit.)

---

## Self-review notes

- Spec coverage: metrics table → Task 4 thresholds table; tools-first →
  reference files; report format → Task 4 template; one-finding-at-a-time,
  test guard, revert, no-tests warning → Task 5; language detection and
  stop-on-none → Task 4 step 1; add-a-language path → Task 4 SKILL.md;
  fixtures and verification → Tasks 2, 3, 6.
- The spec's "> 5 arguments" is planted as 7 args (Python) and 8 args
  (Rust) so both our threshold and the tools' looser defaults fire.
