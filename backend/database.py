""" database.py
    created by: Lucca Giusti (solucca)
    This module uses functional programming to handle
    data from the mariadb mysql database
"""

import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector.connection import MySQLCursor
from typing import Dict, List, Tuple, Union
import json
from datetime import datetime

DATABASE_CONFIG = {}
with open("./credentials.json", "r") as f:
    DATABASE_CONFIG = json.load(f)

def connect() -> Tuple[MySQLConnection, MySQLCursor]:
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()
    return conn, cursor

def close(cnx: MySQLConnection, cursor: MySQLCursor):
    cursor.close()
    cnx.close()


def __check_format(payload: Dict) -> bool:
    """Returns True on error"""
    if not "id" in payload.keys(): return True
    if not "type" in payload.keys(): return True
    for key in payload:
        if key in ["id" , "type"]: continue
        value = payload[key]
        if not "type" in value.keys(): return True
        if not "value" in value.keys(): return True
    return False


def __entity_exists(id:str, type:str) -> bool:
    conn,cursor = connect()
    try:
        cursor.execute("SELECT * FROM entities where type = %s AND id = %s;", (type, id))
        result = cursor.fetchall()
        return len(result) > 0
    finally:
        cursor.close()
        conn.close()
        

def __create_entites_table() -> Union[bool,Dict]:
    try:
        cnx, cursor = connect()
        cursor.execute("""CREATE TABLE IF NOT EXISTS entities (
                    id VARCHAR(64) PRIMARY KEY,
                    type VARCHAR(64),
                    last_update DATETIME,
                    data JSON); """)
        cnx.commit()
        return True
    except Exception as e:
        return {"error":str(e)}
    finally:
        close(cnx, cursor)
        

def __create_type_table(payload: Dict) -> str:
    """Creates a table for the entity type provided in the payload"""
    entity_type: str = payload.get("type").lower()

    # Connect to the MariaDB database
    conn, cursor = connect()

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


def __insert_entities(entity: Dict):
    data = entity.copy()
    type = data.get("type").lower()
    id = data.get("id")
    del data["type"]
    del data ["id"]
    try:
        conn, cursor = connect()
        cursor.execute("INSERT INTO entities (%s, %s, %s, %s)",
                    (id, type, str(datetime.utcnow()), str(data))
                    )
        conn.commit()
    except Exception as e:
        return {"error":str(e)}
    finally:
        close(conn, cursor)


def __update_entities(entity: Dict):
    data = entity.copy()
    id = entity.get("id").lower()
    del data["type"]
    del data ["id"]
    cnx, cursor = connect()
    try:
        cursor.execute("""UPDATE entites
                       SET last_update = %s, data = %s
                       WHERE id = %s""", 
                       (str(datetime.utcnow()), str(data), id))
        cnx.commit()
    finally:
        close(cnx, cursor)


def __insert_data(payload: Dict):
    entity_id, entity_type = payload.get("id"), payload.get("type").lower()
    if not __match_schema(payload):
        return {"error":"entity does not match the schema"}
    
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
    cnx,cursor = connect()

    try:
        # Execute the SQL query
        cursor.execute(sql, values)
        cnx.commit()

    finally:
        # Close the cursor and connection
        cursor.close()
        cnx.close()


def __match_schema(payload: dict) -> bool:
    if not __type_table_exists(payload.get("type").lower()):
        return False
    entity_type = payload.get("type").lower()
    cnx, cursor = connect()
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


def __get_entitiy(id: str) -> Dict:
    
    cnx, cursor = connect()
    try:
        cursor.execute("SELECT * FROM entities WHERE id=%s;", (id,))
        out = cursor.fetchall()[0]
        if len(out) != 4: return None
        return {
            "id":out[0], "type":out[1], "last_update":out[2],"data":out[3]
        }
    finally:
        close(cnx, cursor)
    

def __type_table_exists(table_name: str) -> bool:
    cnx, cursor = connect()
    cursor.execute("SHOW TABLES;")
    tables = []
    for name in cursor:
        tables.append(name[0])
    cursor.close()
    cnx.close()
    return table_name.lower() in tables


def get_columns(type: str) -> Union[List, Dict]:
    """Get Columns of table"""
    try:
        cnx,cursor = connect()
        cursor.execute(f"DESCRIBE {type};")
        out = [{"Field": i[0], "Type": i[1]} for i in cursor.fetchall()]
        return out
    except Exception as e:
        return {"error": str(e)}
    finally:
        cnx.close()
        cursor.close()


def modify_type_table(type: str, new_column: dict):
    """new_column example:
    {"field":"humidity", "type":"float"}
    """
    if not __type_table_exists(type):
        return {"error": f"Type {type} does not exist"}
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
        cnx, cursor = connect()
        cursor.execute(f"ALTER TABLE {type} ADD {new_column['field']} {datatype};")
        return {"success", f"added column: {type}"}

    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        cnx.close()


######################
#### EXTERNAL USE ####
######################

def create_entity(payload: Dict):
    if __check_format(payload):
        return {"error":"Invalid payload format"}
    if __entity_exists(payload.get("id"), payload.get("type").lower()):
        __insert_data(payload)
        __update_entities(payload)
        return {"success":"updated entity"}
    else: # entity does not exists
        __create_type_table(payload) # create type table if not exists
        __insert_data(payload)       # insert into type table
        __insert_entities(payload)          # insert into entities table
        return {"success":"created entity"}


def get_entity(entity_id: str, n: int = None) -> Dict[str, object]:
    entity = __get_entitiy(entity_id)
    if n is None:
        return entity
        

    if not __type_table_exists(entity["type"]):
        return {"Error": f"No data for the type {entity['type']}"}

    # Connect to the MariaDB database
    conn, cursor = connect()

    try:
        # Construct the SELECT query
        select_query = f"SELECT * FROM {entity['type']} WHERE entity_id = %s ORDER BY timestamp DESC LIMIT {n}"
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
        close(conn, cursor)



__create_entites_table()

if __name__ == "__main__":
    print("Running test on database")
    print(f"Testing connection: {__type_table_exists('SoilSensor')}")
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
