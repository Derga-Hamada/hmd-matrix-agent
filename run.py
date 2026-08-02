"""
Application Entry Point.

Starts the Uvicorn ASGI server to serve the FastAPI application.
"""

import uvicorn

if __name__ == "__main__":
    # We point Uvicorn to the 'app' instance inside src/api/main.py
    # reload=True automatically restarts the server when you change code
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)