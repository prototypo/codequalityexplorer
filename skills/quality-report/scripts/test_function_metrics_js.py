import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "function_metrics.mjs"
FIXTURES = Path(__file__).resolve().parents[3] / "test-fixtures" / "javascript"
BAD_JS = FIXTURES / "bad_code.js"
BAD_TS = FIXTURES / "bad_code.ts"

NODE = shutil.which("node")
SKIP_REASON = (
    "needs node and a usable typescript package: install Node.js, then run "
    "`npm install --prefix skills/quality-report --no-save --ignore-scripts "
    "typescript@6`"
)


def _typescript_available():
    """Run the script with no paths: it exits non-zero unless typescript is usable."""
    if NODE is None:
        return False
    probe = subprocess.run([NODE, str(SCRIPT)], capture_output=True)
    return probe.returncode == 0


pytestmark = pytest.mark.skipif(not _typescript_available(), reason=SKIP_REASON)


def _run_script(*paths):
    result = subprocess.run(
        [NODE, str(SCRIPT), *[str(p) for p in paths]],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def _by_name(entries, name):
    matches = [e for e in entries if e["name"] == name]
    assert len(matches) == 1, f"expected exactly one entry for {name!r}, got {matches}"
    return matches[0]


@pytest.fixture(scope="module")
def js_entries():
    return _run_script(BAD_JS)


@pytest.fixture(scope="module")
def ts_entries():
    return _run_script(BAD_TS)


def test_both_files_produce_one_json_array():
    """Several inputs print a single array, each record tagged with its own file."""
    found = _run_script(BAD_JS, BAD_TS)
    assert {e["file"] for e in found} == {str(BAD_JS), str(BAD_TS)}
    assert len(found) == 15


def test_js_functions_present(js_entries):
    names = {e["name"] for e in js_entries}
    assert names == {
        "processData",
        "buildReport",
        "summarizeSales",
        "summarizeRefunds",
        "legacyExport",
        "<anonymous>",
    }


def test_js_process_data(js_entries):
    process_data = _by_name(js_entries, "processData")
    assert process_data["lineno"] == 15
    assert process_data["length"] == 55
    assert process_data["args"] == 1
    assert process_data["nesting"] == 6
    assert process_data["complexity"] == 19
    assert process_data["has_doc"] is True


def test_js_build_report(js_entries):
    build_report = _by_name(js_entries, "buildReport")
    assert build_report["args"] == 7
    assert build_report["length"] == 3
    assert build_report["nesting"] == 0
    assert build_report["complexity"] == 1
    assert build_report["has_doc"] is True


def test_js_arrow_functions_named_from_their_variable(js_entries):
    """An arrow assigned to a const takes that name, and the comment above it counts."""
    sales = _by_name(js_entries, "summarizeSales")
    refunds = _by_name(js_entries, "summarizeRefunds")
    assert sales["lineno"] == 77
    assert refunds["lineno"] == 90
    for entry in (sales, refunds):
        assert entry["length"] == 11
        assert entry["args"] == 1
        assert entry["nesting"] == 2
        assert entry["complexity"] == 4
        assert entry["has_doc"] is True


def test_js_legacy_export(js_entries):
    """The empty-catch function has no comment, and the callback it passes is not counted in it."""
    legacy = _by_name(js_entries, "legacyExport")
    assert legacy["length"] == 8
    assert legacy["nesting"] == 1
    assert legacy["complexity"] == 2
    assert legacy["has_doc"] is False


def test_js_nested_callback_is_its_own_record(js_entries):
    callback = _by_name(js_entries, "<anonymous>")
    assert callback["lineno"] == 105
    assert callback["length"] == 1
    assert callback["args"] == 1
    assert callback["complexity"] == 1
    assert callback["has_doc"] is False


def test_ts_functions_present(ts_entries):
    names = {e["name"] for e in ts_entries}
    assert names == {
        "constructor",
        "classify",
        "totalSales",
        "totalRefunds",
        "swallow",
        "settlementReport",
        "fireAndForget",
        "<anonymous>",
    }


def test_ts_constructor(ts_entries):
    ctor = _by_name(ts_entries, "constructor")
    assert ctor["lineno"] == 21
    assert ctor["length"] == 8
    assert ctor["args"] == 6
    assert ctor["nesting"] == 0
    assert ctor["has_doc"] is True


def test_ts_classify(ts_entries):
    classify = _by_name(ts_entries, "classify")
    assert classify["lineno"] == 32
    assert classify["length"] == 24
    assert classify["args"] == 1
    assert classify["nesting"] == 5
    assert classify["complexity"] == 11
    assert classify["has_doc"] is True


def test_ts_duplicated_functions(ts_entries):
    for name in ("totalSales", "totalRefunds"):
        entry = _by_name(ts_entries, name)
        assert entry["length"] == 11
        assert entry["args"] == 1
        assert entry["nesting"] == 2
        assert entry["complexity"] == 4
        assert entry["has_doc"] is True


def test_ts_swallow(ts_entries):
    swallow = _by_name(ts_entries, "swallow")
    assert swallow["length"] == 8
    assert swallow["nesting"] == 1
    assert swallow["complexity"] == 2
    assert swallow["has_doc"] is False


def test_ts_long_function(ts_entries):
    """The TS fixture plants a function past the 50-line limit."""
    report = _by_name(ts_entries, "settlementReport")
    assert report["lineno"] == 95
    assert report["length"] == 53
    assert report["args"] == 2
    assert report["nesting"] == 1
    assert report["complexity"] == 2
    assert report["has_doc"] is True


def test_ts_promise_catch_swallow(ts_entries):
    """`.catch(() => {})` is the promise swallowing form; its arrow is its own record."""
    fire = _by_name(ts_entries, "fireAndForget")
    assert fire["lineno"] == 150
    assert fire["length"] == 3
    assert fire["complexity"] == 1
    arrows = [e for e in ts_entries if e["name"] == "<anonymous>" and e["lineno"] == 151]
    assert len(arrows) == 1
    assert arrows[0]["args"] == 0


def test_else_if_chain_is_a_single_nesting_level(tmp_path):
    """A flat if/else if/else if chain counts as one level, not one per branch."""
    src = tmp_path / "chain.js"
    src.write_text(
        "function chain(x) {\n"
        "  if (x === 1) {\n"
        "    return 1;\n"
        "  } else if (x === 2) {\n"
        "    return 2;\n"
        "  } else if (x === 3) {\n"
        "    return 3;\n"
        "  }\n"
        "  return 0;\n"
        "}\n"
    )
    chain = _by_name(_run_script(src), "chain")
    assert chain["nesting"] == 1
    assert chain["complexity"] == 4


def test_detached_comment_above_is_not_a_doc(tmp_path):
    """A license header or section banner separated by blank lines is not the function's doc."""
    src = tmp_path / "headers.js"
    src.write_text(
        "/* Copyright 2026 Someone. All rights reserved. */\n"
        "\n"
        "\n"
        "function undocumented(a) { return a; }\n"
        "\n"
        "// directly above\n"
        "function documented(b) { return b; }\n"
        "\n"
        "/** detached jsdoc */\n"
        "\n"
        "\n"
        "const detachedArrow = (c) => c;\n"
    )
    entries = _run_script(src)
    assert _by_name(entries, "undocumented")["has_doc"] is False
    assert _by_name(entries, "documented")["has_doc"] is True
    assert _by_name(entries, "detachedArrow")["has_doc"] is False


def test_bodyless_declarations_are_not_functions(tmp_path):
    """Overloads, abstract methods and ambient declarations have no body to measure."""
    src = tmp_path / "overload.ts"
    src.write_text(
        "export function pick(a: string): string;\n"
        "export function pick(a: number): number;\n"
        "export function pick(a: any): any {\n"
        "  return a;\n"
        "}\n"
        "export abstract class Base {\n"
        "  abstract run(x: number): void;\n"
        "  go(): void {\n"
        "    this.run(1);\n"
        "  }\n"
        "}\n"
        "declare function helper(x: number): void;\n"
    )
    entries = _run_script(src)
    assert [(e["name"], e["lineno"]) for e in entries] == [("pick", 3), ("go", 8)]


def test_explicit_this_parameter_is_not_an_argument(tmp_path):
    """TypeScript's explicit `this` parameter is a type annotation, like Python's self/cls."""
    src = tmp_path / "thisparam.ts"
    src.write_text(
        "export class C {\n"
        "  m(this: C, a: number, b: number): number {\n"
        "    return a + b;\n"
        "  }\n"
        "}\n"
    )
    assert _by_name(_run_script(src), "m")["args"] == 2


def test_directory_recursion_and_exclusions(tmp_path):
    """Directories are walked for every supported extension, minus the excluded dirs."""
    (tmp_path / "src").mkdir()
    for name in ("a.js", "b.jsx", "c.mjs", "d.cjs", "e.ts", "f.tsx"):
        (tmp_path / "src" / name).write_text(f"function fn_{name[0]}() {{ return 1; }}\n")
    (tmp_path / "src" / "notes.md").write_text("function ignored() {}\n")
    for excluded in ("node_modules", "dist", "build", "out", "coverage", ".next"):
        (tmp_path / excluded).mkdir()
        (tmp_path / excluded / "vendor.js").write_text("function ignored() { return 1; }\n")

    names = {e["name"] for e in _run_script(tmp_path)}
    assert names == {"fn_a", "fn_b", "fn_c", "fn_d", "fn_e", "fn_f"}


def test_skips_unreadable_files(tmp_path):
    """An unreadable file is reported on stderr and does not abort the run."""
    (tmp_path / "good.js").write_text("function good() { return 1; }\n")
    unreadable = tmp_path / "unreadable.js"
    unreadable.write_text("function nope() { return 1; }\n")
    unreadable.chmod(0o000)

    result = subprocess.run(
        [NODE, str(SCRIPT), str(tmp_path)],
        capture_output=True,
        text=True,
        check=True,
    )

    assert {e["name"] for e in json.loads(result.stdout)} == {"good"}
    assert "warning: skipping" in result.stderr
    assert "unreadable.js" in result.stderr
