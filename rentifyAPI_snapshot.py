from fastapi import FastAPI, Query, HTTPException
import sqlite3

app = FastAPI()
DATABASE = "cars.sqlite"

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # return dicks
    return conn




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


@app.get("/coches/{accion}/")
def manage_coche(accion: str,id_coche: int = Query(None),
    modelo: str = Query(None),
    marca: str = Query(None),
    consumo: float = Query(None),
    hp: int = Query(None) ):

    conn = get_connection()
    cursor = conn.cursor()



    if accion == "show":
        rows = conn.execute("SELECT * FROM coches").fetchall()
        conn.close()
        return [dict(row) for row in rows]

    elif accion == "insert":
        if not all([modelo, marca, consumo, hp]):
            raise HTTPException(status_code=400, detail="Faltan datos para insertar")
        cursor.execute(
            "INSERT INTO coches (modelo, marca, consumo, hp) VALUES (?, ?, ?, ?)",
            (modelo, marca, consumo, hp)
        )
        conn.commit()
        nuevo_id = cursor.lastrowid
        conn.close()
        return {"message": "Coche creado", "id_coche": nuevo_id}

    elif accion == "update":
        if not id_coche:
            raise HTTPException(status_code=400, detail="Falta id_coche para actualizar")
        fields = []
        values = []
        if modelo:
            fields.append("modelo = ?")
            values.append(modelo)
        if marca:
            fields.append("marca = ?")
            values.append(marca)
        if consumo is not None:
            fields.append("consumo = ?")
            values.append(consumo)
        if hp is not None:
            fields.append("hp = ?")
            values.append(hp)
        if not fields:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        values.append(id_coche)
        sql = f"UPDATE coches SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(sql, tuple(values))
        conn.commit()
        conn.close()
        return {"message": "Coche actualizado", "id_coche": id_coche}

    elif accion == "delete":
        print("prueba",id_coche)

        cursor.execute("DELETE FROM coches WHERE id_coche = ?", (id_coche,))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Coche no encontrado")

        return {"message": "Coche eliminado"}

    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Acción no permitida")

#http://127.0.0.1:8000/coches/delete/?id_coche=64