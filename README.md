# HomeSystem
 Repository for my home server

# Tables:
## entities
- id , primary key, str
- type, primery key, str
- last_update, datetime
- attributes, json

## \<types\>
- id, primary key
- timestamp, primary key
- field1
- field2

Features:
- POST:
    if there is already entitiy:
        insert data in type table,
        update row in entities
    else:
        insert data in type table,
        insert row in entities

- GET