import re
import sqlite3
from typing import Optional

import markdown
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse


app = FastAPI()

DATABASE = "rentify.db"
'Único campo a cambiar, la ruta a la base de datos a atacar'
print("usar para arramcar la api")
print("python -m uvicorn rentifyAPI:app --reload")


def get_connection():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al conectar con la base de datos: {str(e)}"
        )

def execute_query(query: str, params=None):
    if params is None:
        params = []
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        rows = cur.fetchall()
        conn.close()
        return rows
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Violación de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")





@app.get("/")
def root():
    return {"message": "API Rentify cooking"}

def validate_table_name(table_name: str):
    if not re.match(r"^[a-z]+$", table_name):
        raise HTTPException(status_code=400, detail="Nombre de tabla inválido")

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
    validate_table_name(table_name)

    try:
        if by_id:
            query = f"SELECT * FROM {table_name} WHERE {id_table(table_name)} = ?"
            rows = execute_query(query, [by_id])
            if not rows:
                raise HTTPException(status_code=404, detail="Registro no encontrado")
            return dict(rows[0])
        else:
            query = f"SELECT * FROM {table_name}"
            rows = execute_query(query)
            return [dict(row) for row in rows]
    except Exception as e:
        raise e


@app.get("/filter/{table_name}")
def get_data_where(table_name: str,  request: Request):
    validate_table_name(table_name)

    query_params = dict(request.query_params)
    print(query_params)
    print(headers_table(table_name))

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
@app.post("/{table_name}/")
def insert_data(table_name: str,  request: Request):
    validate_table_name(table_name)

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

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, insert_values)
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return {"message": "Registro creado", "id": new_id}
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")



#put
@app.put("/{table_name}/{by_id}")
def update_data(table_name: str, by_id: int,  request: Request):
    validate_table_name(table_name)

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


    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, insert_values)
        conn.commit()
        updated = cursor.rowcount
        conn.close()
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

    if updated == 0:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    return {"message": "Registro actualizado", "id": by_id}

#delete
@app.delete("/{table_name}/{by_id}")
def delete_data(table_name: str, by_id: int):
    validate_table_name(table_name)



    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE {id_table(table_name)} = ?", [by_id])
        conn.commit()
        conn.close()

    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Elemento de {table_name} no encontrado")

    return {"message": "Elemento de {table_name} eliminado"}






@app.get("/help", response_class=HTMLResponse)
def help():
    md = """ 
# 📘 API Documentation – RentifyAPI

## Endpoints disponibles
### `GET /show/{table_name}`
Muestra todos los registros o uno por ID.
<br>
Ejemplos:
<br>
/show/(tu_tabla)
<br>
/show/(tu_tabla)?by_id==(tu_id)

### `GET /filter/{table_name}`
Filtra con parámetros dinámicos.
<br>
Ejemplos:
<br>
/filter/(tu_tabla)?cabezera1=info1&cabezera2=info2

### `POST /{table_name}`
Inserta un registro.
<br>
Ejemplos:
<br>
/(tu_tabla)?cabezera1=info1&cabezera2=info2&cabezera3=info3&cabezera4=info4

### `PUT /{table_name}/{by_id}`
Actualiza un registro.
<br>
Ejemplos:
<br>
/(tu_tabla)/(tu_id)?cabezera1=info1&cabezera2=info2&cabezera3=info3&cabezera4=info4

### `DELETE /{table_name}/{by_id}`
Elimina un registro.
<br>
Ejemplos:
<br>
/(tu_tabla)/(tu_id)
"""

    body = markdown.markdown(md)

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f5f6fa;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}
            .content {{
                background: white;
                padding: 40px;
                border-radius: 12px;
                width: 60%;
                max-width: 800px;
                box-shadow: 0 0 12px rgba(0,0,0,0.1);
            }}
            h1, h2, h3, p {{
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="content">
            {body}
        </div>
    </body>
    </html>
    """

    return html



