# JavaScript / TypeScript analysis

One reference for both languages: `.js`, `.jsx`, `.mjs`, `.cjs`, `.ts`,
`.tsx`. Run from the target repo root. `<paths>` = the source directories
(skip `node_modules`, `dist`, `build`, `out`, `coverage`, `.next`).

`<paths>` is repo-derived, so validate every entry before it reaches a
command, the same discipline `quality-improve` applies to branch names: it
must contain only letters, digits, `.`, `_`, `-`, `/`, must not start with
`-`, and must contain no shell metacharacters. Pass each path as a single
discrete argument, never interpolated into a shell string. Skip any path
that fails and name it in the report as not analysed.

## Where the tools live

Every tool below is invoked by ABSOLUTE PATH out of
`<skill dir>/node_modules/.bin/`, with the target repo's paths as
arguments. Install them there and nowhere else:

```bash
npm install --prefix "<skill dir>" --no-save --ignore-scripts \
  eslint@9 typescript@6 typescript-eslint@8 jscpd@5
```

Never install inside the target repo (`npm install` there runs that repo's own
`install`/`postinstall` scripts) and never reach these tools through `npx`:
`npx --yes eslint@9` prefers the repo's `node_modules/.bin/eslint` whenever the
repo declares a version satisfying the spec, so a repo that ships a hostile
ESLint binary wins — arbitrary code execution from a repo this skill only reads.

## Tools, in order

### function_metrics.mjs — complexity, length, nesting, args, comment presence

Check: `node --version`. The script needs the `typescript` npm package and
resolves it from the install beside the script ONLY — never from the target
repo's `node_modules`, which would import and execute code from the repo this
skill only reads. If nothing usable is found there (version 7 dropped the
JavaScript parser API this script uses, so it does not count) the script exits
with a one-line error naming a `typescript@6` install.

Run: `node "<skill dir>/scripts/function_metrics.mjs" <paths>`

Prints a JSON array, one entry per function, method, constructor, accessor
and arrow function (`file`, `name`, `lineno`, `length`, `args`, `nesting`,
`complexity`, `has_doc`), covering the whole population in both languages —
this is the compliance-count denominator for complexity, function length,
nesting depth, argument count, and comment presence.

- Anonymous functions take the name of the `const`/property they are
  assigned to; a callback that has no such name is reported as
  `<anonymous>`.
- A nested function is measured on its own and excluded from the enclosing
  function's nesting and complexity — but not from its length: the enclosing
  function's line span still contains it. `function_metrics.py` applies the
  same rule to Python nesting and length (it measures no complexity —
  radon does).
- A TypeScript explicit `this` parameter is a type annotation, not an
  argument, and is not counted in `args`.
- An `if`/`else if`/`else` chain counts as ONE nesting level.
- `has_doc` is a JSDoc block or comment ending on the line DIRECTLY above the
  function (for `const f = () => {}`, the comment above the whole statement
  counts). A license header or section banner separated by a blank line does
  not count, the same rule `function_metrics.py` applies to Python.
- Declarations with no body — TypeScript overload signatures, `abstract`
  methods, `declare`/`.d.ts` entries — are not reported: there is nothing to
  measure, so they belong in no compliance count. An overloaded function is
  reported once, at its implementation.

### ESLint — violations backstop

Check: `"<skill dir>/node_modules/.bin/eslint" --version`

ONE command covers all six extensions. The shipped flat config names them
explicitly and supplies the `typescript-eslint` parser, so every file is
linted exactly once — run it once over `<paths>`, not once per language:

```bash
"<skill dir>/node_modules/.bin/eslint" --no-config-lookup --format json \
  --config "<skill dir>/scripts/eslint-quality.config.mjs" \
  --rule '{"complexity":["error",10],"max-lines-per-function":["error",50],"max-params":["error",5],"max-depth":["error",4],"max-lines":["error",500],"no-empty":"error","no-unused-vars":"error"}' \
  <paths>
```

Both the absolute path and `--no-config-lookup` are security requirements,
not conveniences, and neither works without the other. Without
`--no-config-lookup` ESLint loads the SCANNED repo's own `eslint.config.*`,
a JavaScript file that ESLint executes along with every plugin it imports.
Without the absolute path the repo simply ships the ESLint BINARY instead of
the config and wins outright. Always pass both.

The config is read from the skill directory and its parser resolves from the
skill's own `node_modules`. ESLint's base path is the working directory, so
run from the target repo root.

JSON rows: `filePath`, then `messages[]` with `ruleId`, `line`, `message`
(the message carries the measured value, e.g. "has a complexity of 19").

- `complexity` > 10, `max-lines-per-function` > 50, `max-params` > 5,
  `max-depth` > 4, `max-lines` > 500 (file size).
- `no-empty` → the empty-`catch` error-handling smell. It also flags every
  other empty block (`if`, `for`, `while`, `try`) — discount those hits.
- `no-unused-vars` → file-local dead code. Unused *exports* are out of
  scope: an export may be a public API used by another repo.
- `max-depth` mis-counts `else if` chains and can under-report;
  `function_metrics.mjs` is the authoritative nesting source, ESLint is only
  the violation backstop.
- Core `no-unused-vars` also flags TypeScript constructor parameter
  properties (`constructor(public name: string)`) — discount those hits.

If `typescript-eslint` is missing and the user declines to install it, run the
same command without the `--config` line. That fallback lints `.js`, `.mjs`
and `.cjs` ONLY: with no config, ESLint 9 silently skips `.jsx`, `.ts` and
`.tsx` — no violations, no warning. `function_metrics.mjs` still supplies
every metric for those files, but their dead code, empty catches and file size
become estimated/judged from the reading pass; say which files that covers.

### jscpd — duplication

Check: `"<skill dir>/node_modules/.bin/jscpd" --version`

```bash
"<skill dir>/node_modules/.bin/jscpd" --min-lines 5 --reporters json --output <scratch dir> <paths>
```

The json reporter WRITES `jscpd-report.json` into `--output` (default
`./report/`), so always point `--output` at a scratch directory outside the
target repo.

jscpd 5 has no `--no-config` switch — unlike ruff's `--isolated` and
eslint's `--no-config-lookup` — so it reads the target repo's own
`.jscpd.json`/`.jscpdrc`, or a `"jscpd"` key in its `package.json`, and prints
`Using config from ...` when it finds one. That config's `ignore` list can
silently zero the duplication result. Check for all three before the run; if
any is present, note in the report that duplication may be suppressed by the
repo's own config.

Parse `duplicates[]`: each clone has `firstFile`/`secondFile` (`name`,
`start`, `end`) and `lines`. Each clone is one duplication finding;
`statistics.total.percentage` is the duplicated-lines percentage. Duplication
is measured here, but the judgment call — which shared function should
replace the copies — is still yours.

## Error-handling smells

A `catch` that swallows the error: an empty block, a block whose only
statement is a `console.log`/`return`/`null` with no rethrow and no
handling, and the promise form `.catch(() => {})`.

`no-empty` above catches the empty ones. For the swallowing ones, grep and
read the hits:

```bash
grep -rn 'catch' <paths> --include='*.js' --include='*.jsx' --include='*.mjs' \
  --include='*.cjs' --include='*.ts' --include='*.tsx'
```

## Suppressions

`// eslint-disable`, `// eslint-disable-next-line`, `// @ts-ignore` and
`// @ts-expect-error` hide problems from the tools but not from this skill:
report the suppressed problem and note the suppression in the finding, the
same way Python `# noqa` is treated. Reported, not nagged.

```bash
grep -rn 'eslint-disable\|@ts-ignore\|@ts-expect-error' <paths>
```

## Fallbacks (tool missing)

- `node` missing entirely: read each source file. Estimate complexity by
  counting branch keywords (`if`, `else if`, `for`, `while`, `case`,
  `catch`, `&&`, `||`, `??`, `?:`) per function + 1; count function length,
  nesting depth, argument count and comment presence directly. Mark all of
  these "estimated".
- `typescript` package missing and the user declines to install it: same as
  above — the script cannot run without it.
- ESLint missing: `function_metrics.mjs` still covers complexity, length,
  nesting and argument count exactly. Dead code and empty catches come from
  the grep above plus the reading pass; mark those "estimated".
- jscpd missing: read the files with findings plus the largest files and
  look for blocks of ≥ 5 similar lines appearing 2+ times, as in
  `python.md`. Mark "estimated".
