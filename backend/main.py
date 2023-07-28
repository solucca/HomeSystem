from fastapi import FastAPI, HTTPException, Path, Body, Query
from typing import Dict, List, Union
import database

app = FastAPI()

@app.get("/")
async def base():
    return {"message":"API for the SmartHome system", 
            "paths":[
                {"POST /entities/" : "create entitiy"},
                {"GET /entities/{id}" : "get entitiy with id"},
                {"PATCH /{type}" : "add one or more columns to a entity type (not implemented yet)"}
            ]}

@app.post("/entities/")
async def create_entity(
    payload: Union[Dict, List[Dict]] = Body(..., title="Payload Information",
                         description="Data to be saved in the database",
                         example={"type":"weather", "id":"01","temperature": {"type":"float", "value":"15.0", "unit":"C"}})
):  
    return database.create_entity(payload)

@app.get("/entities/{entity_id}")
async def get_entity(
    entity_id: str = Path(..., title="Entity ID"),
    n: int = Query(None, title="Number of recent values to fetch")
):
    data = database.get_entity(entity_id, n)
    if not data:
        raise HTTPException(status_code=404, detail="Entity not found")
    return data