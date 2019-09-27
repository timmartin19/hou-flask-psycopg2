# import pytest
#
# from hou_flask_psycopg2 import SQLNotFoundException, SQLTooManyRowsException
# from oss_auth.utils.database import verify_row_count
#
#
# class VerifyRowCountTest:
#     def test_when_row_is_none__returns_rows(self):
#         rows = [1, 2, 3]
#         resp = verify_row_count(rows, count=None)
#         assert resp == [1, 2, 3]
#
#     def test_when_too_few_rows__raises_sql_not_found_exception(self):
#         with pytest.raises(SQLNotFoundException):
#             verify_row_count([], count=1)
#
#     def test_when_too_many_rows__raises_sql_too_many_rows_exception(self):
#         with pytest.raises(SQLTooManyRowsException):
#             verify_row_count([1, 2], count=1)
#
#     def test_when_same_number_of_rows__returns_rows(self):
#         rows = [1, 2, 3]
#         resp = verify_row_count(rows, count=3)
#         assert resp == [1, 2, 3]
