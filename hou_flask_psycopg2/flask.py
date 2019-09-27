from contextlib import contextmanager
from typing import Type, Generator

from flask import Flask, Response
from psycopg2.extensions import cursor as _cursor
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import NamedTupleCursor
from werkzeug.local import Local, release_local
import logging

from hou_flask_psycopg2 import Psycopg2Utils

__all__ = ["FlaskPsycopg2"]
_LOG = logging.getLogger(__name__)


class FlaskPsycopg2(Psycopg2Utils):
    def __init__(
        self,
        min_connections: int = 2,
        max_connections: int = 5,
        release_connections: bool = False,
    ):
        self._db = Local()

        self._app = None
        self._connection_pool = None
        self.db_uri = None
        self.default_schema = None

        self.min_connections = min_connections
        self.max_connections = max_connections
        self.release_connections = release_connections

    def init_app(self, app: Flask, db_uri: str, default_schema: str):
        self._app = app
        self.init(db_uri, default_schema)
        app.teardown_request(self._teardown_commit_or_rollback)
        app.before_request(self._setup_connection)
        app.after_request(self._after_request_safe_commit)
        return app

    def init(self, db_uri: str, default_schema: str):
        self.db_uri = db_uri
        self.default_schema = default_schema
        self.setup_connection_pool()

    def configure(self, db_uri: str, default_schema: str):
        self.db_uri = db_uri
        self.default_schema = default_schema

    def setup_connection_pool(self) -> None:
        if not self._connection_pool:
            self._connection_pool = ThreadedConnectionPool(
                self.min_connections,
                self.max_connections,
                self.db_uri,
                options=f"-c search_path={self.default_schema}",
            )

    def _setup_connection(self) -> None:
        if not hasattr(self._db, "connection"):
            self._db.connection = self._connection_pool.getconn()

    def _teardown_commit_or_rollback(self, error: Exception) -> None:
        try:
            try:
                if error:
                    self._db.connection.rollback()
            finally:
                self._release_connection()
        except Exception:
            _LOG.exception("An error occurred while cleaning up the connections")

    def _after_request_safe_commit(self, response: Response) -> Response:
        if response.status_code < 400:
            self._safe_commit()
        else:
            self._db.connection.rollback()
        return response

    def _safe_commit(self) -> None:
        try:
            self._db.connection.commit()
        except Exception:
            _LOG.exception("A failure occurred while trying to commit")
            self._db.connection.rollback()
            raise

    def _release_connection(self) -> None:
        if self.release_connections:
            try:
                self._connection_pool.putconn(self._db.connection)
            finally:
                release_local(self._db)

    @contextmanager
    def cursor(self, factory: Type[_cursor] = NamedTupleCursor) -> Generator:
        cur = self._db.connection.cursor(cursor_factory=factory)
        try:
            yield cur
        finally:
            cur.close()
