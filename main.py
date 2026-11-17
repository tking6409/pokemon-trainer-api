# main.py
# Pokémon Trainer API - Week 7 Starter Code
# This file is the foundation of your semester-long project.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

DATABASE = "pokemon.db"

def initialize_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trainers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        hometown TEXT NOT NULL,
        badges INTEGER NOT NULL,
        favorite_pokemon TEXT NOT NULL
)
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pokemon_team (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trainer_id INTEGER NOT NULL,
        pokemon_name TEXT NOT NULL,
        pokemon_type TEXT NOT NULL,
        level INTEGER NOT NULL,
        nickname TEXT,
        FOREIGN KEY (trainer_id) REFERENCES trainers(id)
    )
    """)
    conn.commit()
    conn.close()

initialize_database()

# Create the application. Everything else in this file attaches to "app".
app = FastAPI(
    title="Pokémon Trainer API",
    description="A semester-long project API for managing Pokémon Trainers.",
    version="0.1.0",
)

class Trainer (BaseModel):
    name: str
    hometown: str
    badges: int
    favorite_pokemon: str
class Pokemon(BaseModel):
    pokemon_name: str
    pokemon_type: str
    level: int
    nickname: str | None = None

# Endpoint 1: the home page of your API.
# A GET request to "/" returns a welcome message.
@app.get("/")
def read_root():
    return {"message": "Welcome to the Pokémon Trainer API!"}


# Endpoint 2: the full list of trainers.
# A GET request to "/trainers" returns every trainer in the list.
@app.get("/trainers")
def get_trainers():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, hometown, badges, favorite_pokemon
        FROM trainers
""")

    rows = cursor.fetchall()
    conn.close()

    results = []

    for row in rows:
        results.append({
            "id": row[0],
            "name": row[1],
            "hometown": row[2],
            "badges": row[3],
            "favorite_pokemon": row[4]
})

    return results

# Endpoint 3: one specific trainer.
# {trainer_id} is a path parameter (like the Pokémon name in Week 5).
# FastAPI reads the number from the URL and passes it into the function.
@app.get("/trainers/{trainer_id}")
def get_trainer(trainer_id: int):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, hometown, badges, favorite_pokemon
        FROM trainers
        WHERE id = ?
    """, (trainer_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Trainer not found")

    return {
        "id": row[0],
        "name": row[1],
        "hometown": row[2],
        "badges": row[3],
        "favorite_pokemon": row[4]
}

@app.post("/trainers", status_code=201)
def create_trainer(trainer: Trainer):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trainers
        (name, hometown, badges, favorite_pokemon)
        VALUES (?, ?, ?, ?)
""", (
        trainer.name,
        trainer.hometown,
        trainer.badges,
        trainer.favorite_pokemon
))

    conn.commit()
    trainer_id = cursor.lastrowid
    conn.close()

    return {
        "id": trainer_id,
        "name": trainer.name,
        "hometown": trainer.hometown,
        "badges": trainer.badges,
        "favorite_pokemon": trainer.favorite_pokemon
}

@app.put("/trainers/{trainer_id}")
def update_trainer(trainer_id: int, trainer: Trainer):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE trainers
        SET name = ?, hometown = ?, badges = ?, favorite_pokemon = ?
        WHERE id = ?
""", (
    trainer.name,
    trainer.hometown,
    trainer.badges,
    trainer.favorite_pokemon,
    trainer_id
))
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Trainer not found")

    cursor.execute("""
        SELECT id, name, hometown, badges, favorite_pokemon
        FROM trainers WHERE id = ?
    """, (trainer_id,))
    row = cursor.fetchone()
    conn.close()

    return { 
        "id": row[0],
        "name": row[1],
        "hometown": row[2],
        "badges": row[3],
        "favorite_pokemon": row[4]
    }

@app.delete("/trainers/{trainer_id}")
def delete_trainer(trainer_id: int):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM trainers WHERE id = ?", (trainer_id,)
)
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Trainer not found")

    conn.close()
    return {"message": "Trainer deleted successfully"}

@app.get("/trainers/{trainer_id}/team")
def get_trainer_team(trainer_id: int):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM trainers WHERE id = ?", (trainer_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Trainer not found")

    cursor.execute("""
        SELECT id, pokemon_name, pokemon_type, level, nickname
        FROM pokemon_team WHERE trainer_id = ?
    """, (trainer_id,))

    team = [
        {
            "id": row[0],
            "pokemon_name": row[1],
            "pokemon_type": row[2],
            "level": row[3],
            "nickname": row[4]
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return {"trainer_id": trainer_id, "team": team}

@app.post("/trainers/{trainer_id}/team", status_code=201)
def add_pokemon(trainer_id: int, pokemon: Pokemon):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM trainers WHERE id = ?", (trainer_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Trainer not found")

    cursor.execute("""
        INSERT INTO pokemon_team
        (trainer_id, pokemon_name, pokemon_type, level, nickname)
        VALUES (?, ?, ?, ?, ?)
    """, (
        trainer_id,
        pokemon.pokemon_name,
        pokemon.pokemon_type,
        pokemon.level,
        pokemon.nickname
    ))

    conn.commit()
    pokemon_id = cursor.lastrowid
    conn.close()

    return {
        "id": pokemon_id,
        "trainer_id": trainer_id,
        **pokemon.model_dump()
    }

@app.delete("/trainers/{trainer_id}/team/{pokemon_id}")
def delete_pokemon(trainer_id: int, pokemon_id: int):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM trainers WHERE id = ?", (trainer_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Trainer not found")

    cursor.execute("""
        DELETE FROM pokemon_team
        WHERE id = ? AND trainer_id = ?
    """, (pokemon_id, trainer_id))

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Pokémon not found")

    return {
        "message": f"Pokémon {pokemon_id} was removed from Trainer {trainer_id}'s team."
    }