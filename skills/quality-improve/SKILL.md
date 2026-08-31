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
