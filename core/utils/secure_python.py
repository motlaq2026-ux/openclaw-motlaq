"""Secure Python code execution with sandboxing."""

import ast
import resource
import signal
import sys
from io import StringIO
from typing import Any, Dict, Optional
import multiprocessing
import os


class SecureExecutionError(Exception):
    """Exception for secure execution errors."""

    pass


class SecurePythonExecutor:
    """Secure Python code executor with sandboxing."""

    # Allowed built-ins only
    SAFE_BUILTINS = {
        "abs",
        "all",
        "any",
        "ascii",
        "bin",
        "bool",
        "breakpoint",
        "bytearray",
        "bytes",
        "callable",
        "chr",
        "classmethod",
        "compile",
        "complex",
        "delattr",
        "dict",
        "dir",
        "divmod",
        "enumerate",
        "filter",
        "float",
        "format",
        "frozenset",
        "getattr",
        "globals",
        "hasattr",
        "hash",
        "help",
        "hex",
        "id",
        "input",
        "int",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "list",
        "locals",
        "map",
        "max",
        "memoryview",
        "min",
        "next",
        "object",
        "oct",
        "ord",
        "pow",
        "print",
        "property",
        "range",
        "repr",
        "reversed",
        "round",
        "set",
        "setattr",
        "slice",
        "sorted",
        "staticmethod",
        "str",
        "sum",
        "super",
        "tuple",
        "type",
        "vars",
        "zip",
        "__build_class__",
        "__name__",
        "None",
        "True",
        "False",
        "Ellipsis",
        "NotImplemented",
        "Exception",
        "BaseException",
        "ArithmeticError",
        "AssertionError",
        "AttributeError",
        "BlockingIOError",
        "BrokenPipeError",
        "BufferError",
        "BytesWarning",
        "ChildProcessError",
        "ConnectionAbortedError",
        "ConnectionError",
        "ConnectionRefusedError",
        "ConnectionResetError",
        "DeprecationWarning",
        "EOFError",
        "EnvironmentError",
        "FileExistsError",
        "FileNotFoundError",
        "FloatingPointError",
        "FutureWarning",
        "GeneratorExit",
        "IOError",
        "ImportError",
        "ImportWarning",
        "IndentationError",
        "IndexError",
        "InterruptedError",
        "IsADirectoryError",
        "KeyError",
        "KeyboardInterrupt",
        "LookupError",
        "MemoryError",
        "ModuleNotFoundError",
        "NameError",
        "NotADirectoryError",
        "NotImplementedError",
        "OSError",
        "OverflowError",
        "PendingDeprecationWarning",
        "PermissionError",
        "ProcessLookupError",
        "RecursionError",
        "ReferenceError",
        "ResourceWarning",
        "RuntimeError",
        "RuntimeWarning",
        "StopAsyncIteration",
        "StopIteration",
        "SyntaxError",
        "SyntaxWarning",
        "SystemError",
        "SystemExit",
        "TabError",
        "TimeoutError",
        "TypeError",
        "UnboundLocalError",
        "UnicodeDecodeError",
        "UnicodeEncodeError",
        "UnicodeError",
        "UnicodeTranslationError",
        "UnicodeWarning",
        "UserWarning",
        "ValueError",
        "Warning",
        "ZeroDivisionError",
    }

    # Forbidden AST nodes
    FORBIDDEN_NODES = (
        ast.Import,
        ast.ImportFrom,
        ast.With,
        ast.AsyncWith,
        ast.AsyncFor,
        ast.FunctionDef,
        ast.ClassDef,
        ast.Lambda,
    )

    def __init__(self, timeout: int = 5, memory_limit_mb: int = 50):
        self.timeout = timeout
        self.memory_limit = memory_limit_mb * 1024 * 1024  # Convert to bytes

    def _validate_ast(self, code: str) -> bool:
        """Validate AST for forbidden constructs."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SecureExecutionError(f"Syntax error: {e}")

        for node in ast.walk(tree):
            if isinstance(node, self.FORBIDDEN_NODES):
                node_type = type(node).__name__
                raise SecureExecutionError(f"Forbidden construct: {node_type}")

            # Check for attribute access that might be dangerous
            if isinstance(node, ast.Attribute):
                if node.attr in (
                    "__class__",
                    "__bases__",
                    "__subclasses__",
                    "__globals__",
                    "__code__",
                    "__closure__",
                ):
                    raise SecureExecutionError(
                        f"Forbidden attribute access: {node.attr}"
                    )

        return True

    def _execute_in_subprocess(self, code: str) -> Dict[str, Any]:
        """Execute code in isolated subprocess."""

        def target(queue, code):
            try:
                # Set resource limits
                resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
                resource.setrlimit(
                    resource.RLIMIT_AS, (self.memory_limit, self.memory_limit)
                )
                resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))

                # Redirect stdout/stderr
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = StringIO()
                sys.stderr = StringIO()

                # Create restricted globals
                safe_globals = {
                    "__builtins__": {
                        name: getattr(__builtins__, name)
                        for name in self.SAFE_BUILTINS
                        if hasattr(__builtins__, name)
                    },
                    "__name__": "__main__",
                }

                # Execute
                exec(code, safe_globals)

                # Get output
                output = sys.stdout.getvalue()
                error = sys.stderr.getvalue()

                # Restore
                sys.stdout = old_stdout
                sys.stderr = old_stderr

                queue.put(
                    {
                        "success": True,
                        "output": output,
                        "error": error if error else None,
                    }
                )
            except Exception as e:
                queue.put(
                    {
                        "success": False,
                        "error": str(e),
                    }
                )

        # Use multiprocessing for isolation
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=target, args=(queue, code))
        process.start()
        process.join(timeout=self.timeout + 1)

        if process.is_alive():
            process.terminate()
            process.join()
            raise SecureExecutionError("Execution timeout")

        if queue.empty():
            raise SecureExecutionError("Execution failed")

        result = queue.get()
        if not result["success"]:
            raise SecureExecutionError(result["error"])

        return result

    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Python code securely."""
        # Validate AST first
        self._validate_ast(code)

        # Execute in subprocess
        return self._execute_in_subprocess(code)


# Global executor instance
secure_executor = SecurePythonExecutor(timeout=5, memory_limit_mb=50)
