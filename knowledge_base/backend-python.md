# Backend Troubleshooting — Python

## ModuleNotFoundError

Python cannot find the module. Causes: wrong working directory, missing `__init__.py`, virtualenv not activated, or package not installed. Fix: run from project root, ensure venv active, `pip install -r requirements.txt`.

## ImportError: cannot import name

Usually a circular import or name mismatch. Check spelling and that the symbol exists in the source module. Avoid top-level imports that trigger circular deps; move imports inside functions.

## Additional Python Errors

### `ValueError` / "invalid literal"
**Meaning:** A function received an argument of the correct type but inappropriate value.
**Fix:** Check for `None`, empty strings, or out-of-range values. Validate user input before passing to functions.

### `KeyError` / "key does not exist"
**Meaning:** A dictionary key was not found.
**Fix:** Use `.get()` with a default, check for the key first, or use `try/except KeyError`.

### `AttributeError` / "module has no attribute"
**Meaning:** An attribute or method does not exist on an object.
**Fix:** Check the object type, verify the attribute name, check for typos, use `hasattr()` to test before accessing.

### `IndexError` / "list index out of range"
**Meaning:** A list index is out of bounds.
**Fix:** Check the list length before accessing, use `try/except IndexError`, validate indices.

### `ModuleNotFoundError`
**Meaning:** A package is not installed, the wrong Python interpreter or virtual environment is active, the working directory/module path is wrong, or a package layout/import path is incorrect.
**Fix:**
1. Activate the project's virtual environment.
2. Install project dependencies: `python -m pip install -r requirements.txt`.
3. Confirm which interpreter is running: `python --version` and `python -m pip --version`.
4. Run the command from the project root and verify the import path and package layout. An `__init__.py` may be needed for some package layouts, though namespace packages can work without one.

### `pkg_resources` / `ImportError: cannot import name ...`
**Meaning:** Often a setuptools or packaging issue, especially with legacy packages or editable installs.
**Fix:** Upgrade setuptools (`pip install -U setuptools`), use `pip install -e .` for editable installs, check the package metadata.

### Virtual environment
**Fix:** Create with `python3 -m venv venv`. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows). Deactivate with `deactivate`. Always install deps inside venv.

### pip install fails
**Fix:** Upgrade pip: `python -m pip install --upgrade pip`. For SSL errors use trusted-host flags. For build errors install build tools (python3-dev, gcc). Use `pip install -r requirements.txt`.

### Asyncio event loop errors
**Fix:** "Event loop is closed" or "cannot run nested event loop" — don't nest asyncio.run. Use await directly inside async functions. For sync code calling async, use asyncio.run() once at top level.

### Type errors and tracebacks
**Fix:** Read the traceback bottom-up: last line is the actual error. Check `None` values, wrong types, missing keys. Use `print`/`logging` or `pdb`: `import pdb; pdb.set_trace()`.

### Environment variables
**Fix:** Use `os.getenv` with defaults. Load `.env` with `python-dotenv`. Never commit secrets. `os.environ.setdefault` won't overwrite existing vars — unset them first if stale.

### Logging
**Fix:** Use `logging` module, not `print`. Configure with `logging.basicConfig(level=logging.INFO)`. Use `logger = logging.getLogger(__name__)`.
