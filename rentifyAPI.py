import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

DATABASE = "cars.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # return dicks
    return conn

#class Coche(BaseModel):
class Coche(BaseModel):
    id_coche: int
    modelo: str
    marca: str
    consumo: float
    hp: int



@app.get("/")
def root():
    return {"message": "API Rentify cooking"}

@app.get("/show/{table_name}")
def get_coches(table_name: str):
    conn = get_connection()
    rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def  id_table(table_name: str):
    conn = get_connection()
    row = conn.execute(
        f"SELECT name FROM pragma_table_info('{table_name}') WHERE pk = 1"
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Coche no encontrado")
    return row[0]







@app.get("/search/{table_name}/{id}")
def get_coche(table_name: str, id: int ):
    conn = get_connection()
    row = conn.execute(
        f"SELECT * FROM {table_name} WHERE {id_table(table_name)} = ?", [id]
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Coche no encontrado")

    return dict(row)


@app.get("/filter/coches/")
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
@app.post("/insert/{table_name}/")
def insert_coche(
        modelo: str,
        marca: str,
        consumo: float,
        hp: int
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO coches (modelo, marca, consumo, hp) VALUES (?, ?, ?, ?)",
        (modelo, marca, consumo, hp),
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()

    return {"message": "Coche creado", "id_coche": nuevo_id}

#put
@app.put("/coches/update/{id_coche}")
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
@app.delete("/coches/delete/{id_coche}")
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
        
        
        
        
import sqlite3

# Listas blancas de tablas y columnas permitidas
TABLAS_PERMITIDAS = ["coches", "usuarios", "ventas"]
COLUMNAS_PERMITIDAS = {
    "coches": ["id_coche", "modelo", "marca"],
    "usuarios": ["id_usuario", "nombre", "email"],
    "ventas": ["id_venta", "id_coche", "id_usuario"]
}

def consulta_segura(nombre_tabla: str, columna: str, valor):
    # Validar tabla
    if nombre_tabla not in TABLAS_PERMITIDAS:
        raise ValueError("Tabla no permitida")
    # Validar columna
    if columna not in COLUMNAS_PERMITIDAS[nombre_tabla]:
        raise ValueError("Columna no permitida")
    
    conn = sqlite3.connect("mi_base.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Construir la consulta de forma segura
    sql = f"SELECT * FROM {nombre_tabla} WHERE {columna} = ?"
    cursor.execute(sql, (valor,))
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

# Ejemplo de uso
filas = consulta_segura("coches", "id_coche", 1)
print(filas)
        
        
        
        





python.exe -m uvicorn rentifyAPI:app --reload




"""
