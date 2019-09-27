__all__ = ["SQLException", "SQLNotFoundException", "SQLTooManyRowsException"]


class SQLException(Exception):
    pass


class SQLNotFoundException(SQLException):
    pass


class SQLTooManyRowsException(SQLException):
    pass
