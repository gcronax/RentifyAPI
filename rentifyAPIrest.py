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

    conn=None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        rows = cur.fetchall()
        return rows
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Violación de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.rollback()
            conn.close()


@app.get("/")
def root():
    return {"message": "API Rentify cooking"}

def validate_table_name(table_name: str):
    if not re.match(r"^[a-z]+$", table_name):
        raise HTTPException(status_code=400, detail="Nombre de tabla inválido")

def validate_table_exists(table_name: str):
    validate_table_name(table_name)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
            [table_name]
        )
        exists = cursor.fetchone()
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Violación de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.rollback()
            conn.close()

    if not exists:
        raise HTTPException(status_code=404, detail="La tabla no existe")

    return True

def tables_exists():

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
        rows = cursor.fetchall()

        tables = [row[0] for row in rows]

    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Violación de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.close()

    return tables

def id_table(table_name: str):
    conn=None
    try:
        conn = get_connection()
        row = conn.execute(
            f"SELECT name FROM pragma_table_info('{table_name}') WHERE pk = 1"
        ).fetchone()
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.rollback()
            conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Dato no encontrado")
    return row[0]

def fk_headers(table_name: str):

    conn = None
    try:
        conn = get_connection()
        rows = conn.execute(
            f"PRAGMA foreign_key_list('{table_name}')"
        ).fetchall()
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.rollback()
            conn.close()

    return [
        {
            "column": row["from"],
            "references_table": row["table"],
            "references_column": row["to"]
        }
        for row in rows
    ]


def unique_header(table_name: str):

    conn = None
    try:
        conn = get_connection()

        index_list = conn.execute(
            f"PRAGMA index_list('{table_name}')"
        ).fetchall()

        uniques = list({
            col["name"]
            for idx in index_list if idx["unique"] == 1
            for col in conn.execute(
                f"PRAGMA index_info('{idx['name']}')"
            ).fetchall()

        })



    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.rollback()
            conn.close()

    return uniques

def not_null_header(table_name: str):
    conn = None
    try:
        conn = get_connection()
        rows = conn.execute(
            f"PRAGMA table_info('{table_name}')"
        ).fetchall()

        not_null = [row["name"] for row in rows if row["notnull"] == 1]
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.rollback()
            conn.close()

    return not_null

def headers_table(table_name: str):

    conn = None
    try:
        conn = get_connection()
        rows = conn.execute(f"PRAGMA table_info('{table_name}');").fetchall()
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.rollback()
            conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="Tabla no encontrada")

    headers = [row["name"] for row in rows if row["name"] != id_table(table_name)]
    return headers






#post
@app.post("/{table_name}")
async def insert_data(table_name: str,  request: Request):
    validate_table_name(table_name)

    body = await request.json()
    print("Body JSON:", body)

    query_params = dict(request.query_params)
    print("Body REQUEST:",query_params)

    insert_headers = []
    insert_values = []

    if body is not None:
        for name in headers_table(table_name):
            if name in body:
                if body[name] == "":
                    raise HTTPException(status_code=400, detail=f"{name} vacio")
                insert_headers.append(name)
                insert_values.append(body[name])

    if query_params is not None:
        for name in headers_table(table_name):
            if name in query_params:
                if query_params[name] == "":
                    raise HTTPException(status_code=400, detail=f"{name} vacio")
                insert_headers.append(name)
                insert_values.append(query_params[name])

    if not insert_headers:
        raise HTTPException(status_code=400, detail="No se enviaron datos válidos para insertar")

    headers = ", ".join(insert_headers)
    values = ", ".join(["?"] * len(insert_headers))

    query = f"INSERT INTO {table_name} ({headers}) VALUES ({values})"
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, insert_values)
        conn.commit()
        new_id = cur.lastrowid
        return {"message": "Registro creado", "id": new_id}
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.rollback()
            conn.close()


#put
@app.put("/{table_name}/{by_id}")
async def update_data(table_name: str, by_id: int, request: Request):
    validate_table_name(table_name)

    body = await request.json()
    print("Body JSON:", body)

    query_params = dict(request.query_params)
    print(query_params)

    insert_headers = []
    insert_values = []

    if body is not None:
        for name in headers_table(table_name):
            if name in body:
                if body[name] == "":
                    raise HTTPException(status_code=400, detail=f"{name} vacio")
                insert_headers.append(f"{name} = ?")
                insert_values.append(body[name])

    if query_params is not None:
        for name in headers_table(table_name):
            if name in query_params:
                if query_params[name] == "":
                    raise HTTPException(status_code=400, detail=f"{name} vacio")
                insert_headers.append(f"{name} = ?")
                insert_values.append(query_params[name])

    if not insert_headers:
        raise HTTPException(status_code=400, detail="No se enviaron datos válidos para insertar")

    headers = ", ".join(insert_headers)
    query = f"UPDATE {table_name} SET {headers} WHERE {id_table(table_name)} = ?"

    insert_values.append(by_id)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, insert_values)
        conn.commit()
        updated = cursor.rowcount
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.rollback()
            conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    return {"message": "Registro actualizado", "id": by_id}

#delete
@app.delete("/{table_name}/{by_id}")
def delete_data(table_name: str, by_id: int):
    validate_table_name(table_name)


    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE {id_table(table_name)} = ?", [by_id])
        conn.commit()
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Error SQL: {str(e)}")
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn:
            conn.rollback()
            conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Elemento de {table_name} no encontrado")

    return {"message": f"Elemento de {table_name} eliminado"}






@app.get("/help", response_class=HTMLResponse)
def helpx(table_name: Optional[str] = None):
    md = """ 
# 📘 API Documentation – RentifyAPI
## Endpoints disponibles

### `GET /show/{table_name}`
Muestra todos los registros o uno por ID y 
filtra con parámetros dinámicos.

Ejemplos:
<br>
/(tu_tabla)
<br>
/(tu_tabla)?(tu_id)
<br>
/(tu_tabla)?cabezera1=info1&cabezera2=info2

### `POST /{table_name}`
Inserta un registro.
<br>
Ejemplos:
<br>
curl -X POST "http://localhost:8000/users"      -H "Content-Type: application/json"      -d '{
           "nif": "21edfd32s13d",
           "email": "asererdrasd@gmail.com",
           "password": "passwordblablabla"
         }' -v


### `PUT /{table_name}/{by_id}`
Actualiza un registro.
<br>
Ejemplos:
<br>
curl -X PUT "http://localhost:8000/users"      -H "Content-Type: application/json"      -d '{
           "nif": "21edfd32s13d",
           "email": "asererdrasd@gmail.com",
           "password": "passwordblablabla"
         }' -v

### `DELETE /{table_name}/{by_id}`
Elimina un registro.
<br>
Ejemplos:
<br>
curl -X DELETE "http://localhost:8000/users/40" -v

### `/help`
Pagina de ayuda desde navegador.
<br>
Ejemplos:
<br>
/help?table_name=users

### `/docs`
Documentación automática hecha por la propia API

### tablas disponibles
"""
    for tabla in tables_exists():
        if not tabla=="sqlite_sequence":
            md += f"""{tabla}<br>"""


    if table_name is not None:
        validate_table_exists(table_name)

        idtable = id_table(table_name)
        campos = headers_table(table_name)
        fk = fk_headers(table_name)
        unique = unique_header(table_name)
        not_null = not_null_header(table_name)

        fk_column=[row["column"] for row in fk]

        aux = """"""
        for campo in campos:
            void: bool = False
            aux+=f"""<br> <br> {campo} ->"""
            if campo in unique:
                aux += f""" **uniq**"""
                void=True
            if campo in not_null:
                aux += f""" **notNULL**"""
                void=True
            if campo in fk_column:
                aux += f""" **foreignKEY**"""
                void=True
            if not void:
                aux += f""" nothing"""
        md = f"""## {table_name}   
"""
        md += f"""<br>{idtable} -> **primaryKEY** {aux}   """


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

@app.get("/{table_name}")
def get_data(table_name: str, request: Request):
    validate_table_name(table_name)

    validate_table_exists(table_name)
    query_params = dict(request.query_params)
    print(query_params)
    print(headers_table(table_name))

    if query_params:
        first_key = list(query_params.keys())[0]
        if first_key.isdigit():
            try:
                query = f"SELECT * FROM {table_name} WHERE {id_table(table_name)} = ?"
                rows = execute_query(query, [first_key])
                if not rows:
                    raise HTTPException(status_code=404, detail="Registro no encontrado")
                return dict(rows[0])
            except Exception as e:
                raise e
        else:
            for row in list(query_params.keys()):
                if row not in headers_table(table_name):
                    raise HTTPException(status_code=404, detail=f"Cabezera {row} no existe en la tabla {table_name}")

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
    else:
        query = f"SELECT * FROM {table_name}"
        rows = execute_query(query)
        return [dict(row) for row in rows]



