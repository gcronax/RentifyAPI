import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

DATABASE = "cars.sqlite"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # return dicks
    return conn

class Coche(BaseModel):
    id_coche: int
    modelo: str
    marca: str
    consumo: float
    hp: int






@app.get("/")
def root():
    return {"message": "API Rentify cooking"}

@app.get("/coches/show")
def get_coches():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM coches").fetchall()
    conn.close()
    print("si lo lees eres tontox")
    return [dict(row) for row in rows]


@app.get("/coches/search/{id_coche}")
def get_coche(id_coche: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM coches WHERE id_coche = ?", [id_coche]
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Coche no encontrado")

    return dict(row)


@app.get("/coches/filter/")
def get_cochesby(marca: str = None, modelo: str = None):
    conn = get_connection()
    query = "SELECT * FROM coches WHERE 1=1"
    params = []
    print(marca, modelo)
    if marca:
        query += " AND UPPER(marca) = UPPER(?)"
        params.append(marca)
    if modelo:
        query += " AND modelo = ?"
        params.append(modelo)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


#post
@app.get("/coches/insert/")
def insert_coche(modelo: str, marca: str, consumo: float, hp: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO coches (modelo, marca, consumo, hp) VALUES (?, ?, ?, ?)",
        (modelo, marca, consumo, hp),
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()

    return {"message": "Coche creado", "id_coche": nuevo_id}

#put
@app.get("/coches/update/{id_coche}")
def update_coche(id_coche: int, modelo: str, marca: str, consumo: float, hp: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE coches SET modelo = ?, marca = ?, consumo = ?, hp = ? WHERE id_coche = ?",
        (modelo, marca, consumo, hp, id_coche),
    )
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Coche no encontrado")

    return {"message": "Coche actualizado"}

#delete
@app.get("/coches/delete/{id_coche}")
def delete_coche(id_coche: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM coches WHERE id_coche = ?", (id_coche,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Coche no encontrado")

    return {"message": "Coche eliminado"}


"""
falta averiguar 
/coches/delete/{id_coche}
puede pasar a
/coches/{accion}/{id_coche}


@app.get("/coches/{accion}/{id_prueba}")
def get_cosas(accion:str, id_prueba: int):
    print(accion, id_prueba)
    return {"message": "prueba",accion: id_prueba}

crear uno nuevo para llamamiento interno de funciones
problematica mismo endponit para actualizar insertar y mostrar


y
si
        "SELECT * FROM coches WHERE id_coche = ?", [id_coche]
mirar si ese select para el tema del dinamismo se puede transformar en algo asi
        "SELECT * FROM ${nombre_tabla} WHERE ${id_tabla} = ?", [id_a_buscar]





user\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn rentifyAPI:app --reload
"""
