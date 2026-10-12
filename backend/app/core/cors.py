"""Cross-origin access, for clients that call the API straight from a browser.

The Next.js frontend doesn't need it: its browser only talks to Next.js. So
with the default empty allow-list the middleware isn't installed at all, and
browsers block every cross-origin read - the safe default.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.request_context import REQUEST_ID_HEADER


def add_cors(app: FastAPI, origins: list[str]) -> None:
    if not origins:
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        # Auth is a bearer token in a header, never a cookie, so a browser
        # never needs to send credentials cross-origin.
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        # Readable by the calling page: the id to quote in a bug report, and
        # where an accepted upload's job can be polled.
        expose_headers=[REQUEST_ID_HEADER, "Location"],
    )
