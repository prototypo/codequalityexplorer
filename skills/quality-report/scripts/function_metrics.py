"""Print per-function metrics (length, args, nesting, has_doc) as JSON.

Usage: python3 function_metrics.py <paths...>
"""
import ast
import json
import sys
from pathlib import Path

EXCLUDE_DIRS = {".venv", "venv", "build", "dist", ".tox"}

NESTING_TYPES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith)
if hasattr(ast, "Match"):
    NESTING_TYPES += (ast.Match,)

FUNC_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)


def iter_python_files(paths):
    """Yield .py files under each path, skipping EXCLUDE_DIRS found below that path's root."""
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file():
            if path.suffix == ".py":
                yield path
            continue
        for py_file in sorted(path.rglob("*.py")):
            relative_parts = py_file.relative_to(path).parts
            if not EXCLUDE_DIRS.intersection(relative_parts):
                yield py_file


def count_args(node):
    """Return the number of arguments a function takes, excluding a leading self/cls."""
    args = node.args
    positional = args.posonlyargs + args.args
    count = len(positional) + len(args.kwonlyargs)
    if args.vararg:
        count += 1
    if args.kwarg:
        count += 1
    if positional and positional[0].arg in ("self", "cls"):
        count -= 1
    return count


def compute_nesting(node):
    """Return the deepest block nesting inside node, counting an elif as the same level as its if."""
    def walk_if_chain(if_node, depth):
        """Return the deepest nesting reached inside an if/elif/.../else chain, all at one level."""
        # An elif is an If that is the sole statement in its parent If's orelse;
        # radon treats the whole if/elif/.../else chain as one nesting level.
        new_depth = depth + 1
        local_max = walk(if_node.body, new_depth)
        orelse = if_node.orelse
        if len(orelse) == 1 and isinstance(orelse[0], ast.If):
            local_max = max(local_max, walk_if_chain(orelse[0], depth))
        elif orelse:
            local_max = max(local_max, walk(orelse, new_depth))
        else:
            local_max = max(local_max, new_depth)
        return local_max

    def walk(stmts, depth):
        """Return the deepest nesting reached by any statement in stmts, starting at depth."""
        local_max = depth
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(stmt, ast.If):
                local_max = max(local_max, walk_if_chain(stmt, depth))
                continue
            new_depth = depth + 1 if isinstance(stmt, NESTING_TYPES) else depth
            local_max = max(local_max, new_depth)
            for field_name in ("body", "orelse", "finalbody"):
                block = getattr(stmt, field_name, None)
                if block:
                    local_max = max(local_max, walk(block, new_depth))
            for handler in getattr(stmt, "handlers", None) or []:
                local_max = max(local_max, walk(handler.body, new_depth))
            for case in getattr(stmt, "cases", None) or []:
                local_max = max(local_max, walk(case.body, new_depth))
        return local_max

    return walk(node.body, 0)


def has_comment_above(node, source_lines):
    outer_lineno = node.decorator_list[0].lineno if node.decorator_list else node.lineno
    above_index = outer_lineno - 2
    if above_index < 0:
        return False
    return source_lines[above_index].strip().startswith("#")


def analyze_file(path):
    """Return per-function metrics for path, or [] with a stderr warning if it can't be read or parsed."""
    try:
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError, OSError) as exc:
        print(f"warning: skipping {path}: {exc}", file=sys.stderr)
        return []
    source_lines = source.splitlines()

    entries = []
    for node in ast.walk(tree):
        if not isinstance(node, FUNC_TYPES):
            continue
        has_doc = ast.get_docstring(node) is not None or has_comment_above(node, source_lines)
        entries.append({
            "file": str(path),
            "name": node.name,
            "lineno": node.lineno,
            "length": node.end_lineno - node.lineno + 1,
            "args": count_args(node),
            "nesting": compute_nesting(node),
            "has_doc": has_doc,
        })
    return entries


def main(argv):
    results = []
    for py_file in iter_python_files(argv):
        results.extend(analyze_file(py_file))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
