from fastapi import FastAPI, HTTPException, Path, Body, Query
from datetime import datetime
from typing import Dict
import database

app = FastAPI()

@app.post("/entities/")
async def create_entity(payload: Dict):
    entity_id = payload.get("id")
    entity_type = payload.get("type")

    if not entity_id or not entity_type:
        raise HTTPException(status_code=400, detail="Invalid payload format")

    database.save_entity(payload)
    return {"message": "Entity created successfully"}

@app.get("/entities/{entity_id}")
async def get_entity(
    entity_id: str = Path(..., title="Entity ID"),
    n: int = Query(None, title="Number of recent values to fetch")
):
    data = database.get_entity(entity_id, n)
    if not data:
        raise HTTPException(status_code=404, detail="Entity not found")
    return data