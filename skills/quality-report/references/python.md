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
- `PLR0915` more than 50 statements — treat as the function-length metric.
  PLR0915 counts statements, not physical lines, so it can under-report
  against our bar; ALSO apply the skill threshold (> 50 physical lines)
  during the reading pass.
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
