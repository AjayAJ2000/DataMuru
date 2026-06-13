from __future__ import annotations

from functools import wraps

from datamuru.errors import DataMuruError

from .output import render_error


def with_cli_errors(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except DataMuruError as exc:
            render_error(exc)
            raise SystemExit(exc.exit_code) from exc

    return wrapper
