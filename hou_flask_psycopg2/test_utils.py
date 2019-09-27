from typing import List, Dict

from uuid import uuid4
from psycopg2.pool import PoolError

from hou_flask_psycopg2 import FlaskPsycopg2

__all__ = [
    "database_setup",
    "cleanup_db",
    "setup_module_checkpoint",
    "setup_class_checkpoint",
    "setup_function_checkpoint",
]
global _LAST_SAVEPOINT
_LAST_SAVEPOINT = None


class TestHelper:
    def __init__(self, db: FlaskPsycopg2):
        self.db = db

    @staticmethod
    def _get_operator_type(value):
        return 'IS' if value in (True, False, None) else '='

    def assert_database_has(self, table: str, params: Dict[str, object], expected_count: int = 1):
        where_clause = " AND ".join(f"{key} {self._get_operator_type(value)} %({key})s" for key, value in params.items())
        actual_count = self.db.execute_query(
            f"SELECT COUNT(*) AS c FROM {table} WHERE {where_clause}", params
        )[0].c
        assert expected_count == actual_count


def database_setup(db: FlaskPsycopg2):
    db.setup_connection_pool()
    db._setup_connection()
    try:
        yield
    finally:
        try:
            db._release_connection()
        except AttributeError:
            pass
        try:
            db._connection_pool.closeall()
        except PoolError:
            pass


def cleanup_db(db: FlaskPsycopg2, tables: List[str], create_col_name: str = "created"):
    start = db.execute_query("SELECT NOW()", {})[0][0]
    template = "DELETE FROM {} WHERE {} >= %(start)s;"
    delete_statements = [template.format(table, create_col_name) for table in tables]
    try:
        yield
    finally:
        db._db.connection.rollback()
        with db.cursor() as cur:
            cur.execute(" ".join(delete_statements), {"start": start})
        db._db.connection.commit()


def setup_module_checkpoint(db: FlaskPsycopg2):
    savepoint = "TEST_MODULE_SAVEPOINT"
    _create_savepoint(db, savepoint)
    try:
        yield
    finally:
        _rollback_to_savepoint(db, savepoint)


def setup_class_checkpoint(db: FlaskPsycopg2):
    savepoint = "TEST_CLASS_SAVEPOINT"
    _create_savepoint(db, savepoint)
    try:
        yield
    finally:
        _rollback_to_savepoint(db, savepoint)


def setup_function_checkpoint(db: FlaskPsycopg2):
    savepoint = "TEST_FUNCTION_SAVEPOINT"
    _create_savepoint(db, savepoint)
    _original_connection = db._db.connection
    db._db.connection = _FakeConnection(db)
    try:
        yield
    finally:
        db._db.connection = _original_connection
        _rollback_to_savepoint(db, savepoint)


class _FakeConnection:
    def __init__(self, db: FlaskPsycopg2):
        self._db = db
        self._connection = db._db.connection

    def commit(self):
        return _fake_commit(self._db)

    def teardown(self):
        return _fake_rollback(self._db)

    def __getattr__(self, item):
        return getattr(self._connection, item)


def _create_savepoint(db: FlaskPsycopg2, savepoint_name: str):
    with db.cursor() as cur:
        cur.execute("SAVEPOINT {}".format(savepoint_name))


def _rollback_to_savepoint(db: FlaskPsycopg2, savepoint_name: str):
    with db.cursor() as cur:
        cur.execute("ROLLBACK TO SAVEPOINT {}".format(savepoint_name))


def _release_savepoint(db: FlaskPsycopg2, savepoint_name: str):
    with db.cursor() as cur:
        cur.execute("RELEASE SAVEPOINT {}".format(savepoint_name))


def _fake_commit(db: FlaskPsycopg2):
    global _LAST_SAVEPOINT
    _LAST_SAVEPOINT = "a{}".format(str(uuid4()).replace("-", ""))
    _create_savepoint(db, _LAST_SAVEPOINT)


def _fake_rollback(db: FlaskPsycopg2):
    global _LAST_SAVEPOINT
    savepoint = _LAST_SAVEPOINT or "TEST_FUNCTION_SAVEPOINT"
    _rollback_to_savepoint(db, savepoint)
    _LAST_SAVEPOINT = None
