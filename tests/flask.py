# import logging
# from unittest import mock
#
# import pytest
#
# from hou_flask_psycopg2 import SQLNotFoundException, SQLTooManyRowsException
# from oss_auth.database import _safe_commit, _teardown_commit_or_rollback
# from oss_auth.utils.database import _verify_row_count
#
#
# class CommitOrRollbackTest:
#     @mock.patch("oss_auth.database.DB")
#     def test_when_successful_commit__no_rollback(self, db_local, log_capture):
#         _safe_commit()
#         assert db_local.connection.commit.called
#         assert not db_local.connection.rollback.called
#         assert not log_capture.records
#
#     @mock.patch("oss_auth.database.DB")
#     def test_when_commit_fails__rollback_raise_log(self, db_local, log_capture):
#         db_local.connection.commit.side_effect = FileNotFoundError
#         with pytest.raises(FileNotFoundError):
#             _safe_commit()
#
#         assert len(log_capture.records) == 1
#         assert log_capture.records[0].levelno == logging.ERROR
#
#
# class TeardownCommitOrRollbackTest:
#     @mock.patch("oss_auth.database.DB")
#     def test_when_error__executes_rollback(self, db_local):
#         _teardown_commit_or_rollback(Exception("blah"))
#         assert db_local.connection.rollback.called
#
#     @mock.patch("oss_auth.database.DB")
#     def test_when_exception_on_rollback__logs_exception(self, db_local, log_capture):
#         db_local.connection.rollback.side_effect = FileNotFoundError
#         _teardown_commit_or_rollback(Exception("blah"))
#         assert len(log_capture.records) == 1
#         assert log_capture.records[0].levelno == logging.ERROR
#
#
# class VerifyOneRowTest:
#     @pytest.mark.parametrize(("rows",), [([1],), ([],), ([1, 2],)])
#     def test_when_does_not_expect_one_row__always_returns_rows(self, rows):
#         result = _verify_row_count(rows, False)
#         assert result == rows
#
#     def test_when_empty__raises_sql_not_found(self):
#         with pytest.raises(SQLNotFoundException):
#             _verify_row_count([], True)
#
#     def test_when_more_than_one_row__raises_too_many_exception(self):
#         with pytest.raises(SQLTooManyRowsException):
#             _verify_row_count([1, 2], True)
#
#     def test_when_one_row__returns_row(self):
#         assert _verify_row_count([1], True) == 1
