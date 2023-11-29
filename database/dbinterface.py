import sqlite3 as sql
import logging
import os
from sqlite3 import Connection, OperationalError, Cursor
from typing import Dict, Optional, Any, Type, List, Tuple, List

from hoi4.hoi4loadable import Hoi4Relationship, Hoi4RelationshipType

_DB_PATH: str = "resources/hoi4.db"
_DB_COPY_WILDCARD: str = ';'

_db: Optional[Connection] = None

TABLE_DEFINITION = Dict[str, Any]
NEW_TABLE = Tuple[str, TABLE_DEFINITION, List[str]]


def establish_database(db_definition: Dict[str, TABLE_DEFINITION]):
    global _db

    logging.info("ESTABLISHING CONNECTION TO THE DATABASE")

    need_create_db = not os.path.exists(_DB_PATH)
    _db = sql.connect(_DB_PATH)

    if need_create_db:
        logging.info("CREATING DATABASE")
        _create_database(db_definition)


def close_connection():
    _db.close()


def _create_database(db_definition: Dict[str, TABLE_DEFINITION]):
    assert _db is not None

    try:
        current_cursor = _db.cursor()

        all_new_tables: List[NEW_TABLE] = []

        for table_name, table_definition in db_definition.items():
            create_sql, new_tables = _create_table_construct_sql(table_name, table_definition)

            for new_table in new_tables:
                if new_table not in all_new_tables:
                    all_new_tables.append(new_table)

            logging.debug(create_sql)
            current_cursor.execute(create_sql)

        for table_name, table_definition, foreign_keys in all_new_tables:
            create_sql, _ = _create_table_construct_sql(
                table_name, table_definition, foreign_keys, False)

            logging.debug(create_sql)
            current_cursor.execute(create_sql)

        _db.commit()
        current_cursor.close()
    except OperationalError as error:
        _db.close()
        os.remove(_DB_PATH)

        raise error


def _create_table_construct_sql(table_name: str, table_definition: TABLE_DEFINITION,
                                foreign_keys: List[str] = None,
                                needs_primary_key: bool = True) \
        -> Tuple[str, List[NEW_TABLE]]:
    create_table_sql = "CREATE TABLE ? (" + _DB_COPY_WILDCARD + ")"

    if needs_primary_key:
        create_table_sql = create_table_sql.replace(
            _DB_COPY_WILDCARD, "name TEXT NOT NULL PRIMARY KEY, " + _DB_COPY_WILDCARD)

    current_create_table_sql = create_table_sql.replace('?', table_name)
    table_definition_items = list(table_definition.items())

    if foreign_keys is None:
        foreign_keys = []

    new_tables: List[NEW_TABLE] = []

    for parameter_index in range(len(table_definition.keys())):
        key, value = table_definition_items[parameter_index]
        current_create_table_sql, col_new_tables = _create_table_construct_sql_add_column(
            key, value, current_create_table_sql, foreign_keys)

        for new_table in col_new_tables:
            if new_table not in new_tables:
                new_tables.append(new_table)

    if len(foreign_keys) > 0:
        current_create_table_sql = current_create_table_sql \
            .replace(f"{_DB_COPY_WILDCARD}", f"{', '.join(foreign_keys)}, "
                                             f"{_DB_COPY_WILDCARD}")

    current_create_table_sql = current_create_table_sql \
        .replace(f", {_DB_COPY_WILDCARD}", "")

    return current_create_table_sql, new_tables


def _create_table_construct_sql_add_column(
        key: str, value: Any,
        current_create_table_sql: str, foreign_keys: List[str]) \
        -> Tuple[str, List[NEW_TABLE]]:
    value_type = _get_value_type(type(value))

    new_tables: List[NEW_TABLE] = []

    if value_type is not None:
        column = f"{key} {value_type},"

        if value_type == "relationship":
            column, new_table = _create_table_construct_sql_handle_relationship(
                key, value, column, foreign_keys)

            if new_table is not None and new_table not in new_tables:
                new_tables.append(new_table)

        current_create_table_sql = current_create_table_sql \
            .replace(_DB_COPY_WILDCARD, f"{column} {_DB_COPY_WILDCARD}")

    return current_create_table_sql, new_tables


def _create_table_construct_sql_handle_relationship(
        key: str, relationship: Hoi4Relationship, column: str,
        foreign_keys: List[str]) \
        -> Tuple[str, Optional[NEW_TABLE]]:
    table_name = relationship.data_type.__name__

    new_table = None

    if relationship.relationship_type == Hoi4RelationshipType.ONE_TO_MANY:
        foreign_keys.append(f"FOREIGN KEY({key}) REFERENCES {table_name}(name)")

        column = column.replace(_get_value_type(type(relationship)), "TEXT")
    elif relationship.relationship_type == Hoi4RelationshipType.MANY_TO_MANY:
        from_table_name = type(relationship.entity_from).__name__
        new_table_name = f"{from_table_name}{relationship.field.upper()}"

        new_table_definition = {
            from_table_name: "",
            table_name: ""
        }

        foreign_keys = [
            f"FOREIGN KEY({from_table_name}) REFERENCES {from_table_name}(name)",
            f"FOREIGN KEY({table_name}) REFERENCES {table_name}(name)"
        ]

        new_table = new_table_name, new_table_definition, foreign_keys

        column = ""

    return column, new_table


def add_table_contents(table_type: Type, data: Dict[str, Dict[str, Any]]):
    logging.info(f"INSERTING DATA INTO TABLE {table_type.__name__}")

    current_cursor = _db.cursor()

    for instance_name, instance_attributes in data.items():
        insert_sql, parameters = \
            _insert_table_construct_sql_add_item(
                current_cursor, table_type, instance_name, instance_attributes)

        logging.debug(insert_sql)
        current_cursor.execute(insert_sql, parameters)

    _db.commit()
    current_cursor.close()


def _insert_table_construct_sql_add_item(
        cursor: Cursor,
        table_type: Type, instance_name: str,
        instance_attributes: Dict[str, Any]) \
        -> Tuple[str, List[str]]:
    insert_sql = f"INSERT INTO {table_type.__name__} ( name, {_DB_COPY_WILDCARD}0 ) " \
                 f"values ( ?, {_DB_COPY_WILDCARD}1)"

    current_insert_sql = insert_sql

    attributes = list(instance_attributes.items())

    parameters = [instance_name]

    for attribute_name, attribute_value in attributes:
        attribute_type = _get_value_type(type(attribute_value))

        if attribute_type is None:
            continue

        if attribute_type != "relationship":
            parameters.append(attribute_value)
            current_insert_sql = current_insert_sql \
                .replace(f"{_DB_COPY_WILDCARD}0", attribute_name + f", {_DB_COPY_WILDCARD}0") \
                .replace(f"{_DB_COPY_WILDCARD}1", f"?, {_DB_COPY_WILDCARD}1")
        else:
            current_insert_sql = _insert_table_construct_sql_handle_relationship(
                cursor, attribute_name, attribute_value, parameters, current_insert_sql)

    current_insert_sql = current_insert_sql \
        .replace(f", {_DB_COPY_WILDCARD}0", "") \
        .replace(f", {_DB_COPY_WILDCARD}1", "")

    return current_insert_sql, parameters


def _insert_table_construct_sql_handle_relationship(
        cursor: Cursor,
        attribute_name: str, relationship: Hoi4Relationship,
        parameters: List[Any], current_insert_sql) -> str:
    if len(relationship.entities_to) != 0:
        if relationship.relationship_type == Hoi4RelationshipType.ONE_TO_MANY:
            parameters.append(relationship.entities_to[0].name)
            current_insert_sql = current_insert_sql \
                .replace(f"{_DB_COPY_WILDCARD}0", attribute_name + f", {_DB_COPY_WILDCARD}0") \
                .replace(f"{_DB_COPY_WILDCARD}1", f"?, {_DB_COPY_WILDCARD}1")
        elif relationship.relationship_type == Hoi4RelationshipType.MANY_TO_MANY:
            from_table_name = type(relationship.entity_from).__name__
            to_table_name = relationship.data_type.__name__

            table_name = f"{from_table_name}{relationship.field.upper()}"

            from_entity_name = relationship.entity_from.name

            for entity_to in relationship.entities_to:
                to_entity_name = entity_to.name

                parameters = [from_entity_name, to_entity_name]

                insert_sql = f"INSERT INTO {table_name} ({from_table_name}, {to_table_name})" \
                             f"VALUES" \
                             f"(?, ?)"

                logging.debug(insert_sql)
                cursor.execute(insert_sql, parameters)
    return current_insert_sql


def _get_value_type(value: Type) -> Optional[str]:
    if value == int:
        return "int"

    if value == float:
        return 'real'

    if value == str:
        return 'text'

    if value == bool:
        return 'boolean'

    if value == Hoi4Relationship:
        return 'relationship'

    return None
