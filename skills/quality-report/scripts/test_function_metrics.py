import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "function_metrics.py"


def _long_body(prefix, n):
    return [f"    {prefix}{i} = {i}" for i in range(n)]


def _fixture_widget_class():
    """Source lines for a class with a self-method and a classmethod."""
    return [
        "class Widget:",
        "    def method_with_self(self, a, b):",
        '        """A green method."""',
        "        return a + b",
        "",
        "    @classmethod",
        "    def method_with_cls(cls, a):",
        "        return a",
        "",
    ]


def _fixture_nested_function():
    return [
        "def nested_function(x):",
        "    if x:",
        "        for i in range(x):",
        "            while i:",
        "                i -= 1",
        "    return x",
        "",
    ]


def _fixture_flat_elif_function():
    """Source lines for a function whose only nesting is one if plus three elif branches."""
    return [
        "def flat_elif_function(x):",
        "    if x == 1:",
        "        pass",
        "    elif x == 2:",
        "        pass",
        "    elif x == 3:",
        "        pass",
        "    elif x == 4:",
        "        pass",
        "    return x",
        "",
    ]


def _fixture_commented_function():
    return [
        "# A helpful comment.",
        "def commented_function(x):",
        "    return x",
        "",
    ]


def _fixture_green_function():
    return [
        "def green_function(a, b):",
        '    """Adds two numbers."""',
        "    return a + b",
        "",
    ]


def _fixture_yellow_function():
    return ["def yellow_boundary_function(a):"] + _long_body("y", 45) + ["    return a", ""]


def _fixture_red_function():
    return ["def red_undocumented_function(a, b):"] + _long_body("r", 58) + ["    return a + b", ""]


def _fixture_decorated_function():
    return [
        "# Comment above decorator.",
        "@staticmethod",
        "def decorated_function():",
        "    return 1",
        "",
    ]


def _build_fixture():
    """Assemble the sample module source shared by the per-function metric tests."""
    lines = []
    for builder in (
        _fixture_widget_class,
        _fixture_nested_function,
        _fixture_flat_elif_function,
        _fixture_commented_function,
        _fixture_green_function,
        _fixture_yellow_function,
        _fixture_red_function,
        _fixture_decorated_function,
    ):
        lines += builder()
    return "\n".join(lines) + "\n"


def _run_script(*paths):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *[str(p) for p in paths]],
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
def entries(tmp_path_factory):
    """Run the script once against the shared fixture module and reuse its JSON output."""
    tmp_dir = tmp_path_factory.mktemp("sample")
    src_file = tmp_dir / "sample.py"
    src_file.write_text(_build_fixture())
    return _run_script(src_file), src_file


def test_all_expected_functions_present(entries):
    """Assert every fixture function is discovered exactly once."""
    found, _ = entries
    names = {e["name"] for e in found}
    assert names == {
        "method_with_self",
        "method_with_cls",
        "nested_function",
        "flat_elif_function",
        "commented_function",
        "green_function",
        "yellow_boundary_function",
        "red_undocumented_function",
        "decorated_function",
    }


def test_file_field_matches_source(entries):
    found, src_file = entries
    for entry in found:
        assert entry["file"] == str(src_file)


def test_method_with_self(entries):
    found, _ = entries
    method_with_self = _by_name(found, "method_with_self")
    assert method_with_self["args"] == 2
    assert method_with_self["nesting"] == 0
    assert method_with_self["has_doc"] is True
    assert method_with_self["length"] == 3


def test_method_with_cls(entries):
    found, _ = entries
    assert _by_name(found, "method_with_cls")["args"] == 1


def test_nested_function(entries):
    found, _ = entries
    nested = _by_name(found, "nested_function")
    assert nested["nesting"] == 3
    assert nested["args"] == 1
    assert nested["has_doc"] is False


def test_flat_elif_chain_is_single_nesting_level(entries):
    """A flat if/elif/elif/elif chain must count as one nesting level, not one per elif."""
    found, _ = entries
    assert _by_name(found, "flat_elif_function")["nesting"] == 1


def test_commented_function(entries):
    found, _ = entries
    commented = _by_name(found, "commented_function")
    assert commented["has_doc"] is True
    assert commented["nesting"] == 0


def test_green_function(entries):
    found, _ = entries
    green = _by_name(found, "green_function")
    assert green["length"] == 3
    assert green["has_doc"] is True
    assert green["args"] == 2


def test_yellow_boundary_function(entries):
    found, _ = entries
    yellow = _by_name(found, "yellow_boundary_function")
    assert yellow["length"] == 47
    assert yellow["has_doc"] is False


def test_red_undocumented_function(entries):
    found, _ = entries
    red = _by_name(found, "red_undocumented_function")
    assert red["length"] == 60
    assert red["has_doc"] is False


def test_decorated_function(entries):
    found, _ = entries
    decorated = _by_name(found, "decorated_function")
    assert decorated["has_doc"] is True
    assert decorated["args"] == 0


def test_skips_excluded_dirs(tmp_path):
    """Files under a top-level excluded dir (e.g. .venv) are not analyzed."""
    keep = tmp_path / "pkg"
    keep.mkdir()
    (keep / "mod.py").write_text("def kept():\n    return 1\n")

    skipped = tmp_path / ".venv" / "lib"
    skipped.mkdir(parents=True)
    (skipped / "ignored.py").write_text("def ignored():\n    return 1\n")

    found = _run_script(tmp_path)

    names = {e["name"] for e in found}
    assert names == {"kept"}


def test_exclude_dirs_only_match_below_root(tmp_path):
    """A root nested under an ancestor named build/ is still analyzed; a build/ subdir inside it is still skipped."""
    root = tmp_path / "build" / "myproject"
    keep_dir = root / "pkg"
    keep_dir.mkdir(parents=True)
    (keep_dir / "mod.py").write_text("def kept():\n    return 1\n")

    nested_build = root / "build"
    nested_build.mkdir()
    (nested_build / "ignored.py").write_text("def ignored():\n    return 1\n")

    found = _run_script(root)

    names = {e["name"] for e in found}
    assert names == {"kept"}


def test_skips_files_with_errors(tmp_path):
    """A syntax-error file and a non-UTF-8 file are skipped without aborting analysis of the valid file."""
    (tmp_path / "good.py").write_text("def good():\n    return 1\n")
    (tmp_path / "bad_syntax.py").write_text("def bad(:\n    pass\n")
    (tmp_path / "bad_bytes.py").write_bytes(b"\xff\xfedef bad_bytes(): pass\n")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    found = json.loads(result.stdout)

    names = {e["name"] for e in found}
    assert names == {"good"}
    assert "bad_syntax.py" in result.stderr
    assert "bad_bytes.py" in result.stderr
