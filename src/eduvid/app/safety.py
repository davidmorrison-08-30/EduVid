"""Static safety screening for LLM-generated Manim code.

The generated code is executed (rendered) in a subprocess, so before it ever
runs we statically scan its AST and reject anything that could perform
arbitrary code execution, OS command execution, network access, or destructive
file operations. See ref_docs/dangerous_python_commands.md for rationale.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

# Only these top-level imports are permitted in generated code.
ALLOWED_IMPORTS: frozenset[str] = frozenset(
    {"manim", "numpy", "np", "math", "random", "typing"}
)

# Names that must never be called.
FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "input",
        "open",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "memoryview",
    }
)

# Module-qualified calls that must never appear, e.g. os.system(...).
FORBIDDEN_ATTR_CALLS: frozenset[str] = frozenset(
    {
        "os.system",
        "os.popen",
        "os.remove",
        "os.unlink",
        "os.rmdir",
        "os.removedirs",
        "os.fork",
        "os.kill",
        "os.exec",
        "os.execv",
        "os.execve",
        "os.spawn",
        "os.spawnv",
        "subprocess.run",
        "subprocess.call",
        "subprocess.Popen",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.getoutput",
        "shutil.rmtree",
        "shutil.move",
        "shutil.copy",
        "pickle.load",
        "pickle.loads",
        "marshal.loads",
        "importlib.import_module",
    }
)

# Dunder attributes used for sandbox-escape traversal.
FORBIDDEN_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "__globals__",
        "__builtins__",
        "__subclasses__",
        "__bases__",
        "__mro__",
        "__code__",
        "__class__",
        "__dict__",
        "__getattribute__",
        "__reduce__",
        "__import__",
    }
)

# Modules whose import is never allowed even if referenced indirectly.
FORBIDDEN_MODULES: frozenset[str] = frozenset(
    {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "socket",
        "http",
        "urllib",
        "requests",
        "ftplib",
        "smtplib",
        "pickle",
        "marshal",
        "shelve",
        "ctypes",
        "cffi",
        "pty",
        "importlib",
        "builtins",
        "pathlib",
        "tempfile",
        "glob",
        "multiprocessing",
        "threading",
        "asyncio",
    }
)


@dataclass(frozen=True)
class SafetyResult:
    safe: bool
    violations: tuple[str, ...]

    @property
    def report(self) -> str:
        return "; ".join(self.violations)


def _attr_chain(node: ast.AST) -> str | None:
    """Return a dotted name for an attribute access chain, or None."""
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


class _SafetyVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in FORBIDDEN_MODULES:
                self.violations.append(f"forbidden import: {alias.name}")
            elif root not in ALLOWED_IMPORTS:
                self.violations.append(f"import not in allowlist: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        root = module.split(".")[0]
        if root in FORBIDDEN_MODULES:
            self.violations.append(f"forbidden import: from {module}")
        elif root and root not in ALLOWED_IMPORTS:
            self.violations.append(f"import not in allowlist: from {module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name) and func.id in FORBIDDEN_CALL_NAMES:
            self.violations.append(f"forbidden call: {func.id}()")
        elif isinstance(func, ast.Attribute):
            chain = _attr_chain(func)
            if chain is not None:
                if chain in FORBIDDEN_ATTR_CALLS:
                    self.violations.append(f"forbidden call: {chain}()")
                else:
                    root = chain.split(".")[0]
                    if root in FORBIDDEN_MODULES:
                        self.violations.append(f"forbidden module use: {chain}()")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in FORBIDDEN_ATTRIBUTES:
            self.violations.append(f"forbidden attribute access: {node.attr}")
        self.generic_visit(node)


def screen_code(source: str) -> SafetyResult:
    """Statically analyze ``source`` and report safety violations."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return SafetyResult(safe=False, violations=(f"syntax error: {exc}",))

    visitor = _SafetyVisitor()
    visitor.visit(tree)
    violations = tuple(dict.fromkeys(visitor.violations))  # dedupe, keep order
    return SafetyResult(safe=not violations, violations=violations)
