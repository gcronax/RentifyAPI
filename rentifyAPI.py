import sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI()

DATABASE = "cars.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # return dicks
    return conn

@app.get("/")
def root():
    return {"message": "API Rentify cooking"}

def id_table(table_name: str):
    conn = get_connection()
    row = conn.execute(
        f"SELECT name FROM pragma_table_info('{table_name}') WHERE pk = 1"
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Dato no encontrado")
    return row[0]

def headers_table(table_name: str):
    conn = get_connection()
    rows = conn.execute(f"PRAGMA table_info('{table_name}');").fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Tabla no encontrada")

    headers = [row["name"] for row in rows if row["name"] != id_table(table_name)]
    return headers


@app.get("/show/{table_name}")
def get_data(table_name: str, by_id: Optional[int] = None):
    if by_id is not None:
        conn = get_connection()
        row = conn.execute(
            f"SELECT * FROM {table_name} WHERE {id_table(table_name)} = ?", [by_id]
        ).fetchone()
        conn.close()

        if row is None:
            raise HTTPException(status_code=404, detail="Coche no encontrado")

        return dict(row)
    else:
        conn = get_connection()
        rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
        conn.close()
        return [dict(row) for row in rows]


@app.get("/filter/{table_name}")
def get_data_where(table_name: str,  request: Request):

    query_params = dict(request.query_params)
    print(query_params)

    query = f"SELECT * FROM {table_name} WHERE 1=1"
    params = []

    for name, value in query_params.items():
        if name in headers_table(table_name):
            query += f" AND {name} = ?"
            params.append(value)

    conn = get_connection()
    result = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in result]


#post
@app.post("/insert/{table_name}/")
def insert_data(table_name: str,  request: Request):

    query_params = dict(request.query_params)
    print(query_params)

    insert_headers = []
    insert_values = []

    for name in headers_table(table_name):
        if name in query_params:
            insert_headers.append(name)
            insert_values.append(query_params[name])

    if not insert_headers:
        raise HTTPException(status_code=400, detail="No se enviaron datos válidos para insertar")

    headers = ", ".join(insert_headers)
    values = ", ".join(["?"] * len(insert_headers))

    query = f"INSERT INTO {table_name} ({headers}) VALUES ({values})"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, insert_values)
    conn.commit()

    nuevo_id = cur.lastrowid
    conn.close()

    return {"message": "Registro creado", "id": nuevo_id}

#put
@app.put("/update/{table_name}/{by_id}")
def update_data(table_name: str, by_id: int,  request: Request):

    query_params = dict(request.query_params)
    print(query_params)

    insert_headers = []
    insert_values = []

    for name in headers_table(table_name):
        if name in query_params:
            insert_headers.append(f"{name} = ?")
            insert_values.append(query_params[name])

    if not insert_headers:
        raise HTTPException(status_code=400, detail="No se enviaron datos válidos para insertar")

    headers = ", ".join(insert_headers)
    query = f"UPDATE {table_name} SET {headers} WHERE {id_table(table_name)} = ?"

    insert_values.append(by_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, insert_values)
    conn.commit()

    updated = cursor.rowcount
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    return {"message": "Registro actualizado", "id": by_id}

#delete
@app.delete("/delete/{table_name}/{by_id}")
def delete_data(table_name: str, by_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE {id_table(table_name)} = ?", [by_id])
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



crear uno nuevo para llamamiento interno de funciones
problematica mismo endponit para actualizar insertar y mostrar

y
si
        "SELECT * FROM coches WHERE id_coche = ?", [id_coche]
mirar si ese select para el tema del dinamismo se puede transformar en algo asi
        "SELECT * FROM ${nombre_tabla} WHERE ${id_tabla} = ?", [id_a_buscar]
        
        
           





python.exe -m uvicorn rentifyAPI:app --reload




"""
