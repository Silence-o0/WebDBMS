import os
from enum import Enum
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from dbclasses import *

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_FOLDER = Path.cwd() / "databases"


class RowModel(BaseModel):
    values: dict[str, Any]


databases = {}


def save_database_to_file(db_name: str):
    db_file_path = DATABASE_FOLDER / f"{db_name}.json"

    try:
        database = databases[db_name]
        database.save_to_file(str(db_file_path))
        return {"message": f"База даних '{db_name}' успішно збережена у файл."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при збереженні: {str(e)}")


def load_database_from_file(db_name: str):
    db_file_path = DATABASE_FOLDER / f"{db_name}.json"

    if not db_file_path.exists():
        raise HTTPException(status_code=404, detail="Файл бази даних не знайдений.")

    try:
        database = Database(db_name)
        database.load_from_file(str(db_file_path))
        databases[db_name] = database
        return {"message": f"База даних '{db_name}' успішно завантажена з файлу."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при завантаженні: {str(e)}")


@app.on_event("startup")
def load_databases():
    DATABASE_FOLDER.mkdir(exist_ok=True)
    for file_path in DATABASE_FOLDER.iterdir():
        if file_path.is_file() and file_path.suffix == '.json':
            load_database_from_file(file_path.stem)


@app.post("/{db_name}/create")
def create_database(db_name: str):
    if db_name in databases:
        raise HTTPException(status_code=400, detail="База даних з такою назвою вже існує.")
    try:
        database = Database(db_name)
        databases[db_name] = database
        save_database_to_file(db_name)
        return {"message": f"База даних '{db_name}' успішно створена."}
    except (ValueError, ValidError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/all_databases")
def list_databases():
    return {"databases": list(databases.keys())}


@app.delete("/{db_name}/delete")
def delete_database(db_name: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")

    del databases[db_name]
    db_file_path = DATABASE_FOLDER / f"{db_name}.json"
    db_file_path.unlink(missing_ok=True)
    save_database_to_file(db_name)
    return {"message": f"База даних '{db_name}' успішно видалена."}


@app.post("/{db_name}/{table_name}/create")
def create_table(db_name: str, table_name: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")

    database = databases[db_name]
    try:
        if table_name in database.tables:
            raise HTTPException(status_code=400, detail="Таблиця з такою назвою вже існує.")

        new_table = Table(table_name)
        database.tables[table_name] = new_table
        save_database_to_file(db_name)
        return {"message": f"Таблиця '{table_name}' успішно створена у базі '{db_name}'."}

    except (ValueError, ValidError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/{db_name}/{table_name}/delete")
def delete_table(db_name: str, table_name: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="Database not found.")

    database = databases[db_name]

    if table_name not in database.tables:
        raise HTTPException(status_code=404, detail="Table not found.")

    del database.tables[table_name]
    save_database_to_file(db_name)
    return {"detail": f"Таблиця '{table_name}' успішно видалена."}


@app.get("/{db_name}/tables")
def list_tables(db_name: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")
    database = databases[db_name]
    return {"tables": list(database.tables.keys())}


@app.get("/{db_name}/{table_name}/get_columns")
def get_columns(db_name: str, table_name: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")
    database = databases[db_name]
    table = database.tables[table_name]
    return table.columns


@app.post("/{db_name}/{table_name}/add_column")
def add_column(db_name: str, table_name: str, column_name: str, column_type: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")

    database = databases[db_name]
    if table_name not in database.tables:
        raise HTTPException(status_code=404, detail="Таблиця не знайдена.")

    table = database.tables[table_name]
    try:
        table.add_column(column_name, Type[column_type])
        save_database_to_file(db_name)
        return {"message": f"Колонка '{column_name}' додана до таблиці '{table_name}'."}
    except (ValueError, ValidError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/{db_name}/{table_name}/delete_column")
def delete_column(db_name: str, table_name: str, column_name: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")

    database = databases[db_name]
    if table_name not in database.tables:
        raise HTTPException(status_code=404, detail="Таблиця не знайдена.")

    table = database.tables[table_name]
    try:
        table.delete_column(column_name)
        save_database_to_file(db_name)
        return {"message": f"Колонка '{column_name}' успішно видалена з таблиці '{table_name}'."}
    except (ValueError, ValidError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/{db_name}/{table_name}/add_row")
def add_row(db_name: str, table_name: str, row_data: RowModel):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")

    database = databases[db_name]
    if table_name not in database.tables:
        raise HTTPException(status_code=404, detail="Таблиця не знайдена.")

    table = database.tables[table_name]
    try:
        table.add_row(row_data.values)
        save_database_to_file(db_name)
        return {"message": "Рядок успішно доданий до таблиці."}

    except (ValueError, AttributeError, ValidError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/{db_name}/{table1_name}/compare/{table2_name}")
def compare_tables(db_name: str, table1_name: str, table2_name: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")

    database = databases[db_name]
    if table1_name not in database.tables or table2_name not in database.tables:
        raise HTTPException(status_code=404, detail="Одна або обидві таблиці не знайдені.")

    table1 = database.tables[table1_name]
    table2 = database.tables[table2_name]

    try:
        result = table1.table_difference(table2)
        return {"rows": [row.values for row in result],
                "columns": table1.columns}

    except (ValueError, ValidError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/{db_name}/{table_name}/rows")
def get_all_rows(db_name: str, table_name: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")

    database = databases[db_name]
    if table_name not in database.tables:
        raise HTTPException(status_code=404, detail="Таблиця не знайдена.")

    table = database.tables[table_name]
    return {"rows": [{"values": row.values,
                     "id": row.id} for row in table.rows.values()],
            "columns": list(table.columns.keys())}


@app.get("/{db_name}/{table_name}/row/{row_id}")
def get_row(db_name: str, table_name: str, row_id: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")

    database = databases[db_name]
    if table_name not in database.tables:
        raise HTTPException(status_code=404, detail="Таблиця не знайдена.")

    table = database.tables[table_name]
    row_uuid = uuid.UUID(row_id)

    if row_uuid not in table.rows:
        raise HTTPException(status_code=404, detail="Рядок не знайдений.")

    row = table.rows[row_uuid]
    return row.values


@app.put("/{db_name}/{table_name}/row/{row_id}/edit")
def edit_row(db_name: str, table_name: str, row_id: str, row_data: RowModel):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")

    database = databases[db_name]
    if table_name not in database.tables:
        raise HTTPException(status_code=404, detail="Таблиця не знайдена.")

    table = database.tables[table_name]
    row_uuid = uuid.UUID(row_id)

    if row_uuid not in table.rows:
        raise HTTPException(status_code=404, detail="Рядок не знайдений.")

    row = table.rows[row_uuid]
    try:
        row.edit_row(row_data.values)
        save_database_to_file(db_name)
        return {"message": "Рядок успішно відредагований."}

    except (ValueError, AttributeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/{db_name}/{table_name}/delete_row")
def delete_row(db_name: str, table_name: str, row_id: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена.")

    database = databases[db_name]
    if table_name not in database.tables:
        raise HTTPException(status_code=404, detail="Таблиця не знайдена.")

    table = database.tables[table_name]
    row_uuid = uuid.UUID(row_id)

    if row_uuid not in table.rows:
        raise HTTPException(status_code=404, detail="Рядок не знайдений.")

    del table.rows[row_uuid]
    save_database_to_file(db_name)
    return {"message": "Рядок успішно видалений."}


@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        with open("static/main_page.html") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Сторінка не знайдена")


@app.get("/{db_name}", response_class=HTMLResponse)
async def get_database_page(db_name: str):
    if db_name not in databases:
        raise HTTPException(status_code=404, detail="База даних не знайдена")
    try:
        with open("static/database_page.html") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Сторінка не знайдена")
