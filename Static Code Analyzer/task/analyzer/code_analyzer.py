import ast
import re
import sys
import typing
from pathlib import Path


class Issue:
    def __init__(self, code, msg, line_nbr=None):
        self.code = code
        self.msg = msg
        self.line_nbr = line_nbr


def is_snake_case(text: str):
    return re.match(r"[a-z_].*", text)


def get_issue_001(line: str, line_nbr: int) -> typing.Optional[Issue]:
    if len(line) > 79:
        yield Issue("S001", "Too long", line_nbr)


def get_issue_002(line: str, line_nbr: int) -> typing.Optional[Issue]:
    match = re.search(r"^\s+", line)
    if not match:
        return
    nbr_spaces = len(match[0])
    if nbr_spaces % 4 == 0:
        return
    yield Issue("S002", "Indentation is not a multiple of four", line_nbr)


def get_issue_003(line: str, line_nbr: int) -> typing.Optional[Issue]:
    line = re.sub(r"'.*?'", "", line)
    line = re.sub(r'".*?"', "", line)
    line = re.sub(r'#.*$', "", line)
    if ";" in line:
        yield Issue("S003", "Unnecessary semicolon", line_nbr)


def get_issue_004(line: str, line_nbr: int) -> typing.Optional[Issue]:
    if line.startswith("#"):
        return
    match = re.search(r"(\s*)#", line)
    if not match:
        return
    nbr_spaces = len(match[1])
    if nbr_spaces < 2:
        yield Issue("S004", "Less than two spaces before inline comments", line_nbr)


def get_issue_005(line: str, line_nbr: int) -> typing.Optional[Issue]:
    match = re.search(r".*?(#.*$)", line)
    if not match:
        return
    line = match[0]
    if "todo" in line.lower():
        yield Issue("S005", "TODO found", line_nbr)


def get_issue_006(nbr_lines: int, line_nbr: int) -> typing.Optional[Issue]:
    if nbr_lines > 2:
        yield Issue("S006", "More than two blank lines preceding a code line", line_nbr)


def get_issue_007(line: str, line_nbr: int) -> typing.Optional[Issue]:
    match = re.search(r"(def|class)\s{2,}", line)
    if match:
        yield Issue("S007", f"Too many spaces after '{match[1]}'", line_nbr)


def get_issue_008(node: ast.ClassDef) -> typing.Optional[Issue]:
    name = node.name
    match = re.match(r"[A-Z].*", name)
    if not match:
        yield Issue("S008", f"Class name '{name}' should use CamelCase", node.lineno)


def get_issue_009(node: ast.FunctionDef) -> typing.Optional[Issue]:
    name = node.name
    if not is_snake_case(name):
        yield Issue("S009", f"Function name '{name}' should use snake_case", node.lineno)


def get_issue_010(node: ast.FunctionDef) -> typing.Optional[Issue]:
    for arg in node.args.args:
        name = arg.arg
        if not is_snake_case(name):
            yield Issue("S010", f"Argument name '{name}' should be snake case", arg.lineno)


def get_issue_011(node: ast.FunctionDef) -> typing.Optional[Issue]:
    for arg in node.body:
        if not isinstance(arg, ast.Assign):
            continue
        for target in arg.targets:
            if not hasattr(target, "id"):
                continue
            name = target.id
            if not is_snake_case(name):
                yield Issue("S011", f"Variable '{name}' should be snake case", arg.lineno)


def get_issue_012(node: ast.FunctionDef) -> typing.Optional[Issue]:
    for default in node.args.defaults:
        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
            yield Issue("S012", f"Default argument value is mutable", default.lineno)


def get_issues_by_line(text: str):
    lines = text.split('\n')
    preceding_empty_lines = 0
    for line_nbr, line in enumerate(lines, start=1):
        if line.strip() == "":
            preceding_empty_lines += 1
            continue

        yield from get_issue_001(line, line_nbr)
        yield from get_issue_002(line, line_nbr)
        yield from get_issue_003(line, line_nbr)
        yield from get_issue_004(line, line_nbr)
        yield from get_issue_005(line, line_nbr)
        yield from get_issue_006(preceding_empty_lines, line_nbr)
        yield from get_issue_007(line, line_nbr)

        preceding_empty_lines = 0


def get_issues_by_node(text: str):
    tree = ast.parse(text)
    nodes = ast.walk(tree)

    for node in nodes:
        if isinstance(node, ast.ClassDef):
            yield from get_issue_008(node)
        if isinstance(node, ast.FunctionDef):
            yield from get_issue_009(node)
            yield from get_issue_010(node)
            yield from get_issue_011(node)
            yield from get_issue_012(node)


def check_file(filepath: Path) -> None:
    with open(filepath, 'r') as f:
        text = f.read()
    issues = [*get_issues_by_line(text), *get_issues_by_node(text)]
    for issue in sorted(issues, key=lambda i: (i.line_nbr, i.code)):
        print(f"{filepath}: Line {issue.line_nbr}: {issue.code} {issue.msg}")


if __name__ == "__main__":
    path = Path(sys.argv[1])
    if path.is_file():
        check_file(path)
        exit()
    for filepath in sorted(path.glob('*.py')):
        if filepath.name == "tests.py":
            continue
        check_file(filepath)
