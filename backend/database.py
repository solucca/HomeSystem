""" database.py
    created by: Lucca Giusti (solucca)
    This module uses functional programming to handle
    data from the mariadb mysql database
"""

import mysql.connector
from typing import Dict, List, Union
import json

DATABASE_CONFIG = {}
with open("./credentials.json", "r") as f:
    DATABASE_CONFIG = json.load(f)


def create_type_table(payload: dict) -> str:
    """Creates a table for the entity type provided in the payload"""
    entity_type: str = payload.get("type")

    # Connect to the MariaDB database
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()

    try:
        # Create the SQL query to create the table
        table_name = entity_type.lower()
        columns = [
            "id INT AUTO_INCREMENT PRIMARY KEY",
            "entity_id VARCHAR(64)",
            "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP",
        ]

        for key, data in payload.items():
            if key in ["id", "type"]:
                continue

            # Add columns based on the data type
            if data["type"] == "str":
                columns.append(f"{key} VARCHAR(255)")
            elif data["type"] == "float":
                columns.append(f"{key} FLOAT")
            elif data["type"] == "int":
                columns.append(f"{key} INT")
            elif data["type"] == "datetime":
                columns.append(f"{key} DATETIME")
            else:
                raise ValueError(f"Invalid attribute type: {data['type']}")

        # Construct the CREATE TABLE query
        create_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"

        # Execute the query
        cursor.execute(create_query)
        conn.commit()

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

    return table_name


def table_exists(table_name: str) -> bool:
    cnx = mysql.connector.connect(**DATABASE_CONFIG)
    cursor = cnx.cursor()
    cursor.execute("SHOW TABLES;")
    tables = []
    for name in cursor:
        tables.append(name[0])
    cursor.close()
    cnx.close()
    return table_name.lower() in tables


def match_schema(payload: dict) -> bool:
    if not table_exists(payload.get("type")):
        return False
    entity_type = payload.get("type").lower()
    cnx = mysql.connector.connect(**DATABASE_CONFIG)
    cursor = cnx.cursor()
    try:
        cursor.execute(f"DESCRIBE {entity_type};")
        data = [i[0] for i in cursor.fetchall()]
        for key, value in payload.items():
            if key in ["id", "type"]:
                continue
            elif not key in data:
                return False
        return True

    finally:
        cursor.close()
        cnx.close()


def get_columns(type: str) -> Union[List, Dict]:
    """ Get Columns of table
    """
    try:
        cnx = mysql.connector.connect(**DATABASE_CONFIG)
        cursor = cnx.cursor()
        cursor.execute(f"DESCRIBE {type};")
        out = [{"Field": i[0], "Type": i[1]} for i in cursor.fetchall()]
        return out
    except Exception as e:
        return {"error" : str(e)}
    finally:
        cnx.close()
        cursor.close()


def insert_entity(payload: dict) -> bool:
    """Saves the Entity in a Table.
    If there is no Table for this Type of entity, one is created.
    """
    entity_id, entity_type = payload.get("id"), payload.get("type").lower()

    if not table_exists(entity_type):
        create_type_table(payload)
    if not match_schema(payload):
        return False

    # Construct the SQL insert query
    columns = ["entity_id"]
    values = [entity_id]

    for key, data in payload.items():
        if key in ["id", "type"]:
            continue

        # Extract the value and add it to the lists
        columns.append(key)
        values.append(data["value"])

    placeholders = ", ".join(["%s" for _ in values])
    sql = f"INSERT INTO {entity_type} ({', '.join(columns)}) VALUES ({placeholders})"

    # Connect to the MariaDB database
    cnx = mysql.connector.connect(**DATABASE_CONFIG)
    cursor = cnx.cursor()

    try:
        # Execute the SQL query
        cursor.execute(sql, values)
        cnx.commit()

    finally:
        # Close the cursor and connection
        cursor.close()
        cnx.close()

    return True


def get_entity(entity_id: str, n: int = None) -> Dict[str, object]:
    """Saves the Entity in a Table.
    If there is no Table for this Type of entity, one is created.
    """
    if not ":" in entity_id:
        return {"Error": "Wrong Format <Entity_Type>:<Entity_Id>"}
    entity_type, entity_id = entity_id.split(":")
    table_name = entity_type.lower()

    if not table_exists(entity_type):
        return {"Error": f"No data for the type {entity_type}"}
    if not n:
        n = 1

    # Connect to the MariaDB database
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()

    try:
        # Construct the SELECT query
        select_query = f"SELECT * FROM {table_name} WHERE entity_id = %s ORDER BY timestamp DESC LIMIT {n}"
        cursor.execute(select_query, (entity_id,))

        data = cursor.fetchmany(n)
        out = []
        for row in data:
            entry = {}
            for i in range(1, len(cursor.column_names)):
                entry[cursor.column_names[i]] = row[i]
            out.append(entry)

        return out

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()


def modify_type_table(type: str, new_column: dict):
    """ new_column example: 
        {"field":"humidity", "type":"float"}
    """
    if not table_exists(type): return {"error": f"Type {type} does not exist"}
    columns = get_columns(type)
    for column in columns:
        if column["Field"] == new_column["field"]:
            return {"error": f"Field {new_column['field']} already exists"}
        
    if new_column["type"] == "str":
        datatype = "VARCHAR(255)"
    elif new_column["type"] == "float":
        datatype = "FLOAT"
    elif new_column["type"] == "int":
        datatype = "INT"
    elif new_column["type"] == "datetime":
        datatype = "DATETIME"
    else:
        return {"error": f"Datatype {new_column['type']} does not exist"}
    try:
        cnx = mysql.connector.connect()
        cursor = cnx.cursor()
        cursor.execute(f"ALTER TABLE {type} ADD {new_column['field']} {datatype};")
        cursor.close()
        cnx.close()
        return {'success', f'added column: {type}'}
    except Exception as e:
        return {'error':str(e)}
        


if __name__ == "__main__":
    print("Running test on database")
    print(f"Testing connection: {table_exists('SoilSensor')}")
    payload = {
        "id": "01",
        "type": "SoilSensor",
        "temperature": {"type": "float", "value": 15.0},
        "soil_humidity": {"type": "int", "value": 28},
        "last_water": {"type": "datetime", "value": "2020-07-26 20:20:20"},
    }
    payload2 = {
        "id": "02",
        "type": "weather",
        "temperature": {"type": "float", "value": 15.0},
    }
    print(get_entity("weather:02"))
