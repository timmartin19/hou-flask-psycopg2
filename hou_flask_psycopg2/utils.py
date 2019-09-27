import itertools
from enum import Enum
import dataclasses
from typing import Union, Dict, Iterable, Type, Any, List, Optional, Tuple, Generator

import rapidjson
from psycopg2._json import register_default_jsonb, register_default_json, Json
from psycopg2.extras import DictCursor, NamedTupleCursor, register_uuid
from psycopg2.extensions import cursor as _cursor
from abc import ABC, abstractmethod

from hou_flask_psycopg2.exceptions import SQLNotFoundException, SQLTooManyRowsException

__all__ = ["ValuesQuery", "CustomJSON", "register_types", "Psycopg2Utils"]


class ValuesQuery(Enum):
    positional = "positional"


class CustomJSON(Json):
    def dumps(self, obj):
        return rapidjson.dumps(obj)


def register_types():
    register_default_jsonb(loads=rapidjson.loads)
    register_default_json(loads=rapidjson.loads)
    register_uuid()


class Psycopg2Utils(ABC):
    @abstractmethod
    def cursor(self, factory: Type[_cursor] = NamedTupleCursor) -> Generator:
        pass

    def execute_query(
        self,
        query: str,
        params: Union[Dict, Iterable],
        factory: Type[_cursor] = NamedTupleCursor,
        expect_one: bool = False,
        expected_count: int = None,
    ) -> Any:
        rows = self._execute_query(query, params, factory)
        return self._verify_row_count(rows, expect_one, expected_count=expected_count)

    def execute_query_without_fetch(self, query, params) -> None:
        with self.cursor() as cur:
            cur.execute(query, params)

    def execute_query_conversion(
        self,
        query: str,
        params: Union[Dict, Iterable],
        dataclass: Type,
        expect_one: bool = False,
        expected_count: int = None,
    ) -> Any:
        rows = self._execute_query(query, params, DictCursor)
        rows = [dataclass(**row) for row in rows]
        return self._verify_row_count(rows, expect_one, expected_count)

    @staticmethod
    def verify_row_count(rows: List, count: Optional[int] = None) -> Any:
        if count is None:
            return rows
        if len(rows) < count:
            raise SQLNotFoundException
        if len(rows) > count:
            raise SQLTooManyRowsException
        return rows

    def bulk_insert(
        self,
        new_rows: Iterable,
        dataclass: Type,
        query: str,
        additional_params: Optional[Iterable] = None,
        require_all_inserted: bool = True,
    ) -> List:
        rows = self._execute_values(
            new_rows, query, additional_params, require_all_inserted
        )
        created = [dataclass(**row) for row in rows]
        return created

    def bulk_update(
        self,
        updated_rows: Iterable,
        query: str,
        primary_keys: Tuple[str, ...] = ("id",),
        additional_params: Optional[Iterable] = None,
        require_all_updated: bool = True,
    ) -> List:
        update_rows = [
            dataclasses.astuple(row) for row in updated_rows
        ]  # type: List[Tuple]
        updated = self._execute_values(
            update_rows,
            query,
            additional_params=additional_params,
            require_all=require_all_updated,
            factory=NamedTupleCursor,
        )

        ids = {self._build_primary_key(primary_keys, row) for row in updated}
        objects = [
            row
            for row in updated_rows
            if self._build_primary_key(primary_keys, row) in ids
        ]
        if require_all_updated:
            self.verify_row_count(objects, count=len(update_rows))
        return objects

    def bulk_query(
        self,
        param_rows: List,
        dataclass: Type,
        query: str,
        additional_params: Optional[Iterable] = None,
        require_all_found: bool = True,
    ) -> List:
        rows = self._execute_values(
            param_rows, query, additional_params, require_all_found
        )
        return [dataclass(**row) for row in rows]

    @staticmethod
    def unsafe_escape_like_string(parameter: str, escape_character: str = "=") -> str:
        """
        This function purely escapes a string for use in an ILIKE or LIKE
        It does NOT make it safe to directly format a string.  YOU MUST
        STILL USE PSYCOPG2 PARAMETERIZATION.

        This makes it so that if you search for a string that includes a '%'
        character it still works.

        ..code::python

            my_search_string = 'something%or_another'
            escaped_search_string = escape_like_strings(my_search_string)
            query = "SELECT * FROM my_table WHERE name LIKE %s ESCAPE '='"
            execute_query(query, (f'%{escaped_search_string}%',))
        """
        return (
            parameter.replace(escape_character, f"{escape_character * 2}")
            .replace("%", f"{escape_character}%")
            .replace("_", f"{escape_character}_")
        )

    @staticmethod
    def _format_query_for_bulk_insert(new_rows: List[Tuple], query: str) -> str:
        size_of_row = len(new_rows[0])
        assert all(
            len(row) == size_of_row for row in new_rows
        ), "All rows must be of the same size"
        row_placeholder = ", ".join("%s" for _ in range(size_of_row))
        values_template = ", ".join(f"({row_placeholder})" for _ in new_rows)
        return query.format(template=values_template)

    @staticmethod
    def _expand_params_for_bulk_insert(
        new_rows: List[Tuple], additional_params: Optional[Iterable]
    ) -> List:
        all_params = additional_params or [ValuesQuery.positional]
        params = []  # type: List
        for param in all_params:
            if param == ValuesQuery.positional:
                params.extend(itertools.chain(*new_rows))
            else:
                params.append(param)
        return params

    @staticmethod
    def _build_primary_key(primary_keys: Tuple[str, ...], obj: object) -> Tuple:
        return tuple(getattr(obj, key) for key in primary_keys)

    def _execute_query(self, query, params, factory) -> List:
        with self.cursor(factory=factory) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def _verify_row_count(
        self, rows: List, expect_one: bool, expected_count: int = None
    ) -> Any:
        if expect_one:
            return self.verify_row_count(rows, 1)[0]
        if expected_count is not None:
            return self.verify_row_count(rows, expected_count)
        return rows

    def _execute_values(
        self,
        rows,
        query,
        additional_params: Optional[Iterable] = None,
        require_all: bool = True,
        factory: Type[_cursor] = DictCursor,
    ) -> List:
        if not rows:
            return []
        query = self._format_query_for_bulk_insert(rows, query)
        params = self._expand_params_for_bulk_insert(rows, additional_params)
        found_rows = self.execute_query(query, params, factory=factory)
        if require_all:
            self.verify_row_count(found_rows, count=len(rows))
        return found_rows
