// Print per-function metrics (length, args, nesting, complexity, has_doc) as JSON.
//
// Usage: node function_metrics.mjs <paths...>
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, extname, join, relative, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const EXTENSIONS = new Set(['.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx']);
const EXCLUDE_DIRS = new Set(['node_modules', 'dist', 'build', 'out', 'coverage', '.next']);

// The script ships with the plugin but runs against a user-chosen repo, so the
// target repo's own typescript wins over the one installed beside the script.
async function loadTypescript() {
  const require = createRequire(import.meta.url);
  const scriptDir = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    () => require.resolve('typescript', { paths: [process.cwd()] }),
    () => require.resolve('typescript', { paths: [scriptDir] }),
    () => require.resolve('typescript'),
  ];
  for (const candidate of candidates) {
    try {
      // typescript 7 dropped the JavaScript parser API this script needs, so a
      // module without createSourceFile counts as not found.
      const mod = (await import(pathToFileURL(candidate()).href)).default;
      if (mod?.createSourceFile) return mod;
    } catch {
      // this candidate does not resolve here; try the next one
    }
  }
  console.error(`error: cannot find a usable 'typescript' package — run \`npm install --prefix ${join(scriptDir, '..')} --no-save --ignore-scripts typescript@6\``);
  process.exit(1);
}

const ts = await loadTypescript();

const FN_KINDS = new Set([
  ts.SyntaxKind.FunctionDeclaration, ts.SyntaxKind.FunctionExpression,
  ts.SyntaxKind.ArrowFunction, ts.SyntaxKind.MethodDeclaration,
  ts.SyntaxKind.Constructor, ts.SyntaxKind.GetAccessor, ts.SyntaxKind.SetAccessor,
]);
const NEST_KINDS = new Set([
  ts.SyntaxKind.IfStatement, ts.SyntaxKind.ForStatement, ts.SyntaxKind.ForInStatement,
  ts.SyntaxKind.ForOfStatement, ts.SyntaxKind.WhileStatement, ts.SyntaxKind.DoStatement,
  ts.SyntaxKind.SwitchStatement, ts.SyntaxKind.TryStatement,
]);
const BRANCH_KINDS = new Set([
  ts.SyntaxKind.IfStatement, ts.SyntaxKind.ForStatement, ts.SyntaxKind.ForInStatement,
  ts.SyntaxKind.ForOfStatement, ts.SyntaxKind.WhileStatement, ts.SyntaxKind.DoStatement,
  ts.SyntaxKind.CaseClause, ts.SyntaxKind.CatchClause, ts.SyntaxKind.ConditionalExpression,
]);
const NAME_PARENT_KINDS = new Set([
  ts.SyntaxKind.VariableDeclaration, ts.SyntaxKind.PropertyAssignment,
  ts.SyntaxKind.PropertyDeclaration,
]);

function warn(path, err) {
  console.error(`warning: skipping ${path}: ${err.message}`);
}

function* sourceFiles(paths) {
  for (const raw of paths) {
    let stats;
    try {
      stats = statSync(raw);
    } catch (err) {
      warn(raw, err);
      continue;
    }
    if (stats.isFile()) {
      if (EXTENSIONS.has(extname(raw))) yield raw;
      continue;
    }
    let entries;
    try {
      entries = readdirSync(raw, { recursive: true, withFileTypes: true });
    } catch (err) {
      warn(raw, err);
      continue;
    }
    const found = [];
    for (const entry of entries) {
      if (!entry.isFile() || !EXTENSIONS.has(extname(entry.name))) continue;
      const full = join(entry.parentPath, entry.name);
      if (relative(raw, full).split(sep).some((part) => EXCLUDE_DIRS.has(part))) continue;
      found.push(full);
    }
    yield* found.sort();
  }
}

function fnName(node) {
  if (node.name) return node.name.getText();
  if (node.kind === ts.SyntaxKind.Constructor) return 'constructor';
  const parent = node.parent;
  if (parent && NAME_PARENT_KINDS.has(parent.kind) && parent.name) return parent.name.getText();
  return '<anonymous>';
}

// A comment above `const f = () => {}` is trivia of the whole statement, not of
// the arrow function itself, so look for it on the node that carries the name.
function docAnchor(node) {
  const parent = node.parent;
  if (!parent || !NAME_PARENT_KINDS.has(parent.kind)) return node;
  if (parent.kind !== ts.SyntaxKind.VariableDeclaration) return parent;
  return parent.parent?.parent ?? parent;
}

// An `else if` is a nested IfStatement, but the whole if/else-if chain is one level.
function isElseIf(node) {
  return node.kind === ts.SyntaxKind.IfStatement
    && node.parent?.kind === ts.SyntaxKind.IfStatement
    && node.parent.elseStatement === node;
}

// Only a comment ending on the line directly above counts, mirroring
// function_metrics.py: a license header or section banner further up is not
// this function's documentation.
function hasDocAbove(fn, sf, text) {
  const anchor = docAnchor(fn);
  const ranges = ts.getLeadingCommentRanges(text, anchor.getFullStart());
  if (!ranges?.length) return false;
  const commentEnd = sf.getLineAndCharacterOfPosition(ranges[ranges.length - 1].end).line;
  return sf.getLineAndCharacterOfPosition(anchor.getStart(sf)).line - commentEnd === 1;
}

function measure(fn, sf, text) {
  let nesting = 0, complexity = 1;
  const walk = (node, depth) => {
    let d = depth;
    if (NEST_KINDS.has(node.kind) && !isElseIf(node)) { d = depth + 1; if (d > nesting) nesting = d; }
    if (BRANCH_KINDS.has(node.kind)) complexity++;
    if (node.kind === ts.SyntaxKind.BinaryExpression) {
      const op = node.operatorToken.kind;
      if (op === ts.SyntaxKind.AmpersandAmpersandToken || op === ts.SyntaxKind.BarBarToken || op === ts.SyntaxKind.QuestionQuestionToken) complexity++;
    }
    node.forEachChild(c => { if (!FN_KINDS.has(c.kind)) walk(c, d); });
  };
  walk(fn.body, 0);
  const start = sf.getLineAndCharacterOfPosition(fn.getStart(sf)).line + 1;
  const end = sf.getLineAndCharacterOfPosition(fn.getEnd()).line + 1;
  // A TypeScript `this` parameter is a type annotation, not an argument.
  const thisParam = fn.parameters[0]?.name.getText() === 'this' ? 1 : 0;
  return {
    name: fnName(fn), lineno: start, length: end - start + 1,
    args: fn.parameters.length - thisParam, nesting, complexity,
    has_doc: hasDocAbove(fn, sf, text),
  };
}

const results = [];
for (const file of sourceFiles(process.argv.slice(2))) {
  let text, sf;
  try {
    text = readFileSync(file, 'utf8');
    sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true,
      file.endsWith('.tsx') || file.endsWith('.jsx') ? ts.ScriptKind.TSX : undefined);
  } catch (err) {
    warn(file, err);
    continue;
  }
  const visit = (node) => {
    // No body = an overload signature, abstract method or ambient declaration:
    // nothing to measure, and counting it would inflate the compliance totals.
    if (FN_KINDS.has(node.kind) && node.body) results.push({ file, ...measure(node, sf, text) });
    node.forEachChild(visit);
  };
  visit(sf);
}
console.log(JSON.stringify(results, null, 2));
