# Backend Troubleshooting — Python

## ModuleNotFoundError

Python cannot find the module. Causes: wrong working directory, missing __init__.py, virtualenv not activated, or package not installed. Fix: run from project root, ensure venv active, pip install -r requirements.txt.

## ImportError: cannot import name

Usually a circular import or name mismatch. Check spelling and that the symbol exists in the source module. Avoid top-level imports that trigger circular deps; move imports inside functions.

## Virtual environment

Create with python3 -m venv venv. Activate: source venv/bin/activate (Linux/Mac) or venv\Scripts\activate (Windows). Deactivate with deactivate. Always install deps inside venv.

## pip install fails

Upgrade pip: python -m pip install --upgrade pip. For SSL errors use trusted-host flags. For build errors install build tools (python3-dev, gcc). Use pip install -r requirements.txt.

## Asyncio event loop errors

"Event loop is closed" or "cannot run nested event loop" — don't nest asyncio.run. Use await directly inside async functions. For sync code calling async, use asyncio.run() once at top level.

## Type errors and tracebacks

Read the traceback bottom-up: last line is the actual error. Check None values, wrong types, missing keys. Use print/logging or pdb: import pdb; pdb.set_trace().

## Environment variables

Use os.getenv with defaults. Load .env with python-dotenv. Never commit secrets. os.environ.setdefault won't overwrite existing vars — unset them first if stale.

## Logging

Use logging module, not print. Configure with logging.basicConfig(level=logging.INFO). Use logger = logging.getLogger(__name__).
