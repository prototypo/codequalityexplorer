# Rust analysis

Run from the directory containing the target `Cargo.toml`.

## Tools, in order

### cargo clippy — complexity, length, arguments, unwrap

Note: clippy and `cargo check` compile the target crate, which executes its
`build.rs` and any proc-macros — this is not a purely read-only scan, so only
point this skill at code you trust.

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
- `excessive_nesting` requires a `clippy.toml` with `excessive-nesting-threshold = 4`.
  NEVER create, overwrite, or delete a `clippy.toml` inside the target repo —
  it may already have one with the maintainer's real lint config. Instead
  write the temporary `clippy.toml` into a scratch directory outside the
  target repo and point clippy at it via `CLIPPY_CONF_DIR`, e.g.
  `CLIPPY_CONF_DIR=<scratch dir> cargo clippy ...`. If that is not possible,
  measure nesting during the reading pass instead.
- `unwrap_used` / `expect_used` → error-handling smell, EXCEPT hits inside
  `#[cfg(test)]` modules or `#[test]` functions — ignore those.

Some of these lints are nursery/restriction lints; if a `-W` flag is
rejected by the installed clippy, drop that flag and cover the metric in
the reading pass.

### rust-code-analysis-cli — complexity, length, arguments (needed for compliance counts)

Check: `rust-code-analysis-cli --version`

This tool feeds the ask-to-install step (`cargo install rust-code-analysis-cli`):
it is what supplies the full-population compliance counts (🟢/🟡/🔴 per
function) for complexity, length, and argument count. If the user declines
to install it, those counts are made during the reading pass instead and
marked "estimated".

If installed, run: `rust-code-analysis-cli -m -p <src dir> -O json`
Read the per-function metrics against the skill's thresholds: `cyclomatic`
(complexity > 10), `loc.sloc` (function length > 50), `nargs` (argument
count > 5).

### Comment presence

No full Rust parser is shipped, so comment presence is always a grep
heuristic done during the reading pass: count `fn` items and whether each
is immediately preceded by a `///` doc comment (or a `//` comment directly
above, mirroring the Python has-comment-above rule). Always mark this
count "estimated".

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
