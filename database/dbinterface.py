import sqlite3 as sql
import logging
import os
from sqlite3 import Connection, OperationalError
from typing import Dict, Optional, Any, Type

from hoi4.hoi4loadable import Hoi4Relationship

_DB_PATH: str = "resources/hoi4.db"
_DB_COPY_WILDCARD: str = ';'

_db: Optional[Connection] = None


def establish_database(db_definition: Dict[str, Dict[str, Any]]):
    global _db

    logging.info("ESTABLISHING CONNECTION TO THE DATABASE")

    need_create_db = not os.path.exists(_DB_PATH)
    _db = sql.connect(_DB_PATH)

    if need_create_db:
        logging.info("CREATING DATABASE")
        _create_database(db_definition)


def close_connection():
    _db.close()


def _create_database(db_definition: Dict[str, Dict[str, Any]]):
    assert _db is not None

    try:
        current_cursor = _db.cursor()

        create_table_sql = "CREATE TABLE ? (name TEXT NOT NULL PRIMARY KEY, " + _DB_COPY_WILDCARD + ")"

        for table_name, table_definition in db_definition.items():
            current_create_table_sql = create_table_sql.replace('?', table_name)

            table_definition_items = list(table_definition.items())

            foreign_keys = []

            for parameter_index in range(len(table_definition.keys()) - 1):
                key, value = table_definition_items[parameter_index]
                value_type = _get_value_type(type(value))

                if value_type is None:
                    continue

                column = f"{key} {value_type}"

                if value_type == "relationship":
                    table_name = value.data_type.__name__

                    column = column.replace(value_type, "TEXT")

                    foreign_keys.append(f"FOREIGN KEY({key}) REFERENCES {table_name}(name)")

                current_create_table_sql = current_create_table_sql.replace(
                    _DB_COPY_WILDCARD, f"{column}, {_DB_COPY_WILDCARD}")

            if len(table_definition_items) > 0:
                key, value = table_definition_items[-1]
                value_type = _get_value_type(type(value))

                if value_type is not None:
                    column = f"{key} {value_type}"

                    if value_type == "relationship":
                        table_name = value.data_type.__name__

                        column = column.replace(value_type, "TEXT")

                        foreign_keys.append(f"FOREIGN KEY({key}) REFERENCES {table_name}(name)")

                    current_create_table_sql = current_create_table_sql\
                        .replace(_DB_COPY_WILDCARD, f"{column}, {_DB_COPY_WILDCARD}")

            if len(foreign_keys) > 0:
                current_create_table_sql = current_create_table_sql\
                    .replace(f"{_DB_COPY_WILDCARD}", f"{', '.join(foreign_keys)}, "
                                                     f"{_DB_COPY_WILDCARD}")

            current_create_table_sql = current_create_table_sql\
                .replace(f", {_DB_COPY_WILDCARD}", "")

            logging.debug(current_create_table_sql)
            current_cursor.execute(current_create_table_sql)

        _db.commit()
        current_cursor.close()
    except OperationalError as error:
        _db.close()
        os.remove(_DB_PATH)

        raise error


def add_table_contents(table_type: Type, data: Dict[str, Dict[str, Any]]):
    logging.info(f"INSERTING DATA INTO TABLE {table_type.__name__}")

    insert_sql = f"INSERT INTO {table_type.__name__} ( name, {_DB_COPY_WILDCARD}0 ) values ( ?, {_DB_COPY_WILDCARD}1)"

    current_cursor = _db.cursor()

    for instance_name, instance_attributes in data.items():
        current_insert_sql = insert_sql

        attributes = list(instance_attributes.items())

        parameters = [instance_name]

        for attribute_index in range(len(attributes) - 1):
            attribute_name, attribute_value = attributes[attribute_index]
            attribute_type = _get_value_type(type(attribute_value))

            if attribute_type is None:
                continue

            if attribute_type != "relationship":
                parameters.append(attribute_value)
            else:
                relationship: Hoi4Relationship = attribute_value

                if len(relationship.entities_to) == 1:
                    parameters.append(relationship.entities_to[0].name)
                else:
                    continue

            current_insert_sql = current_insert_sql\
                .replace(f"{_DB_COPY_WILDCARD}0", attribute_name + f", {_DB_COPY_WILDCARD}0")\
                .replace(f"{_DB_COPY_WILDCARD}1", f"?, {_DB_COPY_WILDCARD}1")

        if len(attributes) > 0:
            attribute_name, attribute_value = attributes[-1]

            attribute_type = _get_value_type(type(attribute_value))

            if attribute_type is not None:
                if attribute_type != "relationship":
                    parameters.append(attribute_value)
                    current_insert_sql = current_insert_sql\
                        .replace(f"{_DB_COPY_WILDCARD}0", attribute_name)\
                        .replace(f"{_DB_COPY_WILDCARD}1", "?")
                else:
                    relationship: Hoi4Relationship = attribute_value

                    if len(relationship.entities_to) == 1:
                        parameters.append(relationship.entities_to[0].name)
                        current_insert_sql = current_insert_sql\
                            .replace(f"{_DB_COPY_WILDCARD}0", attribute_name)\
                            .replace(f"{_DB_COPY_WILDCARD}1", "?")

        current_insert_sql = current_insert_sql\
            .replace(f", {_DB_COPY_WILDCARD}0", "")\
            .replace(f", {_DB_COPY_WILDCARD}1", "")

        logging.debug(current_insert_sql)
        current_cursor.execute(current_insert_sql, parameters)

    _db.commit()
    current_cursor.close()


def _get_value_type(value: Type) -> Optional[str]:
    if value == int:
        return "int"
    elif value == float:
        return 'real'
    elif value == str:
        return 'text'
    elif value == bool:
        return 'boolean'
    elif value == Hoi4Relationship:
        return 'relationship'
    return None
