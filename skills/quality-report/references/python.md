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

Run: `ruff check --isolated --select C901,PLR0913,PLR0915,PLR1702,E722,F401 --preview --config 'lint.pylint.max-nested-blocks=4' --output-format json <paths>`

- `C901` complexity > 10 (backup if radon missing)
- `PLR0913` more than 5 arguments
- `PLR0915` more than 50 statements — treat as the function-length metric.
  PLR0915 counts statements, not physical lines, so it can under-report
  against our bar; ALSO apply the skill threshold (> 50 physical lines)
  during the reading pass.
- `PLR1702` too many nested blocks — treat as nesting > 4. Ruff's default
  `max-nested-blocks` is 5, so it only fires at 6+ nested blocks and misses
  a function at depth 5 (our "more than 4" bar); the `--config` flag above
  lowers the trigger to 5 nested blocks so it matches. `function_metrics.py`
  is the authoritative source for nesting counts — ruff is only the
  violation backstop.
- `E722` bare `except:`
- `F401` unused import → dead-code finding. The vulture fallback grep below
  only covers functions, so this is what gives import coverage.

JSON rows have `filename`, `location.row`, `code`, `message`.

### vulture — dead code

Check: `vulture --version`

Run: `vulture <paths> --min-confidence 80`
Each output line `file:line: unused function 'name'` is a dead-code finding.

### function_metrics.py — length, nesting, args, comment presence

Run: `python3 <skill dir>/scripts/function_metrics.py <paths>`

Prints a JSON array, one entry per function/method (`file`, `name`,
`lineno`, `length`, `args`, `nesting`, `has_doc`), covering the whole
population — this is the compliance-count denominator for function
length, nesting depth, argument count, and comment presence.
`radon cc -s -j` already emits every function too, so it is the
denominator for the complexity counts.

## Fallbacks (tool missing)

- radon and ruff both missing: read each source file. Estimate complexity by
  counting branch keywords (`if`, `elif`, `for`, `while`, `except`, `and`,
  `or`, `case`) per function + 1; count function length and nesting depth
  directly. Mark these findings "estimated".
- radon missing, ruff present: `C901` still flags complexity VIOLATIONS but
  gives no per-function complexity value, so estimate the complexity
  compliance counts by counting branch keywords per function as above, and
  estimate file size with `wc -l`. Mark both "estimated".
- `function_metrics.py` needs only python3 (stdlib `ast`, no dependencies).
  If even python3 is unusable, count length/nesting/args/comment-presence
  during the reading pass instead, and mark those counts "estimated".
- vulture missing: grep each module-level function name across the repo
  (`grep -rn "name(" --include="*.py"`); a function whose name appears only
  at its own definition is likely dead. Mark "estimated"; skip names that
  look like framework entry points (`main`, `test_*`, dunder methods).

## Duplication (no tool assumed)

Read files with findings plus the largest files. Look for function bodies or
blocks of ≥ 5 similar lines appearing 2+ times. This is a judgment metric;
pair each duplication finding with a reusability recommendation naming the
shared function to extract.
