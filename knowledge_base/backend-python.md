# Backend Troubleshooting — Python

This document covers Python-specific application errors. Adapt the patterns here to your project framework.

---

## ModuleNotFoundError

**Cause:** Python cannot find the module.

**Fix:**
1. Run from the project root directory.
2. Ensure the virtual environment is activated: `source venv/bin/activate` (Linux) or `venv\Scripts\activate` (Windows).
3. Install dependencies: `pip install -r requirements.txt`.
4. Check `sys.path` includes the project root.
5. Verify `__init__.py` is present in packages (or use namespace packages).

**Common scenarios:**
- `ModuleNotFoundError: No module named 'app'` — wrong working directory or missing install.
- `ModuleNotFoundError: No module named 'fastapi'` — dependencies not installed.
- `ModuleNotFoundError: No module named 'app.models'` — missing `__init__.py` or wrong package structure.

---

## ImportError: cannot import name

**Cause:** Circular import or name mismatch.

**Fix:**
1. Check spelling and that the symbol exists in the source module.
2. Avoid top-level imports that trigger circular dependencies.
3. Move imports inside functions or classes to break cycles.
4. Check that the module is installed (not just in `requirements.txt`).

---

## ImportError: attempted relative import with no known parent package

**Cause:** Running a module as a script instead of a package.

**Fix:**
1. Run as a module: `python -m mypackage.mymodule` instead of `python mypackage/mymodule.py`.
2. Install the package in development mode: `pip install -e .`.
3. Add the project root to `PYTHONPATH`.

---

## ImportError: missing optional dependency

**Cause:** A feature requires an optional package.

**Fix:**
1. Install the required package: `pip install <package>`.
2. Check `requirements.txt` or `pyproject.toml` for the dependency.
3. Use try/except for optional imports with a graceful fallback.

---

## TypeError: unsupported operand type(s)

**Cause:** Attempting an operation on incompatible types.

**Fix:**
1. Verify variable types with `type(variable)`.
2. Convert types explicitly (e.g., `int()`, `str()`, `float()`).
3. Check API response data types match expectations.
4. Use type hints and a linter (mypy) to catch type errors early.

---

## ValueError: invalid literal

**Cause:** Converting a string to a number fails, or a value is not valid.

**Fix:**
1. Check the string content (whitespace, special chars, encoding).
2. Verify the expected range/format.
3. Use `try/except ValueError` for graceful error handling.
4. Validate input before conversion.

---

## KeyError: 'key'

**Cause:** Accessing a dictionary key that doesn't exist.

**Fix:**
1. Check if the key exists: `key in dict` or `dict.get('key')`.
2. Use `try/except KeyError` for graceful handling.
3. Verify the data source (API response, JSON, environment variables).
4. Print the actual keys present: `print(list(my_dict.keys()))`.

---

## IndexError: list index out of range

**Cause:** Accessing an index beyond the list length.

**Fix:**
1. Check list length before accessing: `len(lst)` or `if i < len(lst)`.
2. Use safe list access helpers.
3. Verify API response data structure.
4. Add bounds checking in loops and range access.

---

## AttributeError: 'module' has no attribute 'name'

**Cause:** Accessing a non-existent attribute.

**Fix:**
1. Check the module or object has the attribute (use `dir()`).
2. Verify the import path (module vs. class vs. function).
3. Check for typos in attribute names.
4. Verify the installed version supports the attribute.

---

## FileNotFoundError

**Cause:** File does not exist at the expected path.

**Fix:**
1. Verify the path is correct (typos, relative-vs-absolute).
2. Check the file exists: `ls -la <path>` or `os.path.exists(path)`.
3. Use `os.path.join()` for cross-platform path construction.
4. For config files, allow environment variable override: `os.getenv("CONFIG_PATH", "default.json")`.

---

## PermissionError: [Errno 13] Permission denied

**Cause:** File or directory permissions prevent access.

**Fix:**
1. Check permissions: `ls -la <path>`.
2. Verify the running user has read/write access.
3. On external drives (exFAT/NTFS), be aware of filesystem limitations (no symlinks).
4. Run with appropriate user (not root in production).

---

## OSError: [Errno 98] Address already in use

**Cause:** Port already occupied.

**Fix:**
1. Find the process: `lsof -i :<port>` or `ss -tlnp | grep <port>`.
2. Kill the process or change the port.
3. Check for multiple instances of the app running.
4. For Docker, check port mapping conflicts.

---

## ConnectionRefusedError: [Errno 61] Connection refused

**Cause:** Target service is not running or not listening on the expected port.

**Fix:**
1. Verify the target service is running.
2. Check host/port in the connection string.
3. For Docker, use the container name as host.
4. Check firewall rules and security groups.

---

## TimeoutError / socket.timeout

**Cause:** Operation took longer than the timeout limit.

**Fix:**
1. Review timeout settings in config.
2. Check if the target service is slow or overloaded.
3. Increase timeout if the operation legitimately takes longer.
4. Add retry logic with exponential backoff.

---

## MemoryError

**Cause:** Exceeded available RAM.

**Fix:**
1. Reduce workload size or increase memory limits.
2. Profile memory usage: `memory-profiler`, `tracemalloc`.
3. Fix memory leaks: unbounded caches, retained references, accumulating listeners.
4. Restart as temporary mitigation.

---

## Common Python error codes

| Code | Name | Fix |
|---|---|---|
| ModuleNotFoundError | Module not found | Install package, check working directory |
| ImportError | Import failed | Check spelling, circular imports, dependencies |
| TypeError | Invalid type operation | Verify types, convert explicitly |
| ValueError | Invalid value | Validate input, check range/format |
| KeyError | Dict key missing | Use `get()` or check key exists |
| IndexError | List index out of range | Check list length before access |
| AttributeError | Missing attribute | Check import path, spelling, installed version |
| FileNotFoundError | File not found | Verify path, check file exists |
| PermissionError | Permission denied | Check permissions, run with correct user |
| OSError | OS-level error | Check errno, fix underlying issue |
| ConnectionRefusedError | Connection refused | Verify target service running |
| TimeoutError | Operation timed out | Increase timeout, check target service |
| MemoryError | Out of memory | Reduce workload, increase limits, fix leaks |

---

## Debugging tips

1. **Logging:** Use `logging` module with levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
2. **Stack traces:** Read bottom-up; the last frame is where the error originated.
3. **Breakpoints:** Use `breakpoint()` (Python 3.7+) or `import pdb; pdb.set_trace()`.
4. **Profiling:** Use `py-spy` for CPU profiling, `memory-profiler` for memory.
5. **Type checking:** Run `mypy` to catch type errors early.
6. **Linting:** Use `ruff` or `flake8` to catch style and potential bugs.
