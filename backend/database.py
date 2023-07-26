import mysql.connector
from typing import Tuple, List, Union
import json 

DATABASE_CONFIG = {}
with open("./credentials.json", "r") as f:
    DATABASE_CONFIG = json.load(f)

def create_table(payload: dict) -> str:
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
            "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"
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

def table_exists(entity_type: str) -> bool:
    cnx = mysql.connector.connect(**DATABASE_CONFIG)
    cursor = cnx.cursor()
    cursor.execute("SHOW TABLES;")
    tables = []
    for name in cursor:
        tables.append(name[0])
    return entity_type.lower() in tables

def save_entity(payload: dict) -> str:
    """Saves the Entity in a Table.
    If there is no Table for this Type of entity, one is created.
    """
    entity_id, entity_type = payload.get("id"), payload.get("type").lower()

    if not table_exists(entity_type):
        create_table(payload)

    # Construct the SQL insert query
    columns = ["entity_id"]
    values = [entity_id]

    for key, data in payload.items():
        if key in ["id", "type"]:
            continue

        # Extract the value and add it to the lists
        columns.append(key)
        values.append(data["value"])

    placeholders = ', '.join(['%s' for _ in values])
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

    return entity_id

def get_entity(entity_id: str, n: int = None) -> Union[Tuple[List, Tuple], None]:
    entity_type, entity_id = entity_id.split(':')
    table_name = entity_type.lower()
    
    if not table_exists(entity_type): return None
    if not n: n = 1

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

if __name__ == "__main__":
    from time import sleep
  
    print("Running test on database")
    print(f"Testing connection: {table_exists('SoilSensor')}")
    payload = {
        "id": "01",
        "type": "SoilSensor",
        "temperature": {"type": "float", "value": 15.0},
        "soil_humidity": {"type": "int", "value": 28},
        "last_water":{"type": "datetime", "value": "2020-07-26 20:20:20"}
    }
    out = get_entity("Weather:01")
    print(out)

