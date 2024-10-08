import json
import re
import uuid
from enum import Enum
from typing import Any, List


class Type(Enum):
    integer = "integer"
    real = "real"
    char = "char"
    string = "string"
    time = "time"
    timeInvl = "timeInvl"


class ValidError(Exception):
    def __init__(self, invalid_columns, message=None):
        self.invalid_columns = invalid_columns
        if message is None:
            message = f"Некоректний тип даних в колонках: {', '.join(invalid_columns)}"
        self.message = message
        super().__init__(self.message)


class Row:
    def __init__(self):
        self.id = uuid.uuid4()
        self.values: dict[str, Any] = {}
        self.column_types: dict[str, Type] = {}

    def edit_row(self, data: dict[str, Any]) -> bool:
        demo_row = Row()
        demo_row.column_types = self.column_types
        new_valid_dict = {}
        demo_row.values = new_valid_dict

        is_all_none = True
        for key, value in data.items():
            if value is not None:
                value = value.strip()
            if key not in self.column_types:
                print(f"Колонка '{key}' не знайдена у таблиці.")
                return False
            if self.column_types[key] == Type.timeInvl:
                if value != '' and value is not None:
                    both_val = value.split('-')
                    if both_val[0] != "" or both_val[1] != "":
                        is_all_none = False
                        demo_row.values[key] = value
                    else:
                        demo_row.values[key] = None
                else:
                    demo_row.values[key] = None
            elif self.column_types[key] == Type.string:
                if value == "":
                    demo_row.values[key] = None
                else:
                    if value is not None:
                        is_all_none = False
                    demo_row.values[key] = value
            else:
                if value is not None:
                    is_all_none = False
                demo_row.values[key] = value
        if is_all_none:
            raise ValueError("Усі поля порожні. Введіть, будь ласка, дані.")

        invalid_columns = demo_row.validate_row()
        if invalid_columns:
            raise ValidError(invalid_columns)

        self.values = demo_row.values
        return True

    def validate_cell(self, value: Any, col_type: Type) -> Any:
        def is_valid_time_format(time_str):
            pattern = r'^\d{1,3}:\d{2}:\d{2}$'
            match = re.match(pattern, time_str)
            if not match:
                raise ValueError
            hours, minutes, seconds = map(int, time_str.split(':'))
            if 0 <= minutes < 60 and 0 <= seconds < 60:
                return value
            raise ValueError

        def time_to_seconds(time_str):
            hours, minutes, seconds = map(int, time_str.split(':'))
            return hours * 3600 + minutes * 60 + seconds

        if value is None:
            return value

        if col_type == Type.integer:
            return int(value)
        elif col_type == Type.real:
            return float(value)
        elif col_type == Type.char:
            if len(value) != 1:
                raise ValueError
        elif col_type == Type.time:
            if not is_valid_time_format(value):
                raise ValueError
        elif col_type == Type.timeInvl:
            value = str(value)
            values = value.split('-')
            if not is_valid_time_format(values[0]) or not is_valid_time_format(values[1]):
                raise ValueError
            time1_seconds = time_to_seconds(values[0])
            time2_seconds = time_to_seconds(values[1])
            sub = time2_seconds - time1_seconds
            if sub < 0:
                raise ValueError
        elif col_type == Type.string:
            value = str(value)
        return value

    def validate_row(self) -> List[str]:
        invalid_col_values = []
        for key, value in self.values.items():
            col_type = self.column_types[key]
            try:
                converted_type_value = self.validate_cell(value, col_type)
                self.values[key] = converted_type_value
            except ValueError:
                invalid_col_values.append(key)
        return invalid_col_values


class Table:
    def __init__(self, name: str):
        self.name = name
        self.columns: dict[str, Type] = {}
        self.rows: dict[uuid.UUID, Row] = {}

    def add_row(self, data: dict[str, Any]) -> bool:
        new_row = Row()
        new_row.column_types = self.columns
        if not self.columns:
            raise AttributeError("Неможливо створити рядок. Будь ласка, створіть принаймні одну колонку.")

        is_all_none = True
        for key, value in data.items():
            if value is not None:
                if isinstance(value, str):
                    value = value.strip()
                data[key] = value
            if key not in self.columns:
                print(f"Колонка '{key}' не знайдена у таблиці.")
                return False
            if self.columns[key] == Type.timeInvl:
                if value is not None:
                    both_val = value.split('-')
                    if both_val[0] != "" or both_val[1] != "":
                        is_all_none = False
                    else:
                        data[key] = None
            elif self.columns[key] == Type.string:
                if value == "":
                    data[key] = None
                elif value is not None:
                    is_all_none = False
            else:
                if value is not None:
                    is_all_none = False

        if is_all_none:
            raise ValueError("Усі поля порожні. Введіть, будь ласка, дані.")

        new_row.values = data
        invalid_columns = new_row.validate_row()
        if invalid_columns:
            raise ValidError(invalid_columns)
        self.rows[new_row.id] = new_row
        return True

    def add_column(self, column_name: str, column_type: Type) -> bool:
        if column_name is None or not column_name.strip():
            raise ValueError("Колонка повинна мати назву. Будь ласка, спробуйте ще раз.")
        if column_name not in self.columns:
            self.columns[column_name] = column_type
            for row in self.rows.values():
                row.column_types[column_name] = column_type
                row.values[column_name] = None
        else:
            raise ValueError("Колонка з такою назвою вже існує.")
        return True

    def delete_column(self, col_name: str) -> bool:
        if col_name in self.columns:
            del self.columns[col_name]
            rows_to_delete = []

            for row_id, row in self.rows.items():
                if col_name in row.values:
                    del row.values[col_name]
                row.column_types = self.columns

                if all(value is None for value in row.values.values()):
                    rows_to_delete.append(row_id)

            for row_id in rows_to_delete:
                del self.rows[row_id]
            return True
        else:
            print(f"Колонка '{col_name}' не знайдена.")
            return False

    def table_difference(self, table2: 'Table') -> List[Row]:
        if self.columns != table2.columns:
            raise ValueError("Таблиці мають різні колонки. Оберіть інші таблиці.")
        if self.name == table2.name:
            raise ValueError("Ви обрали одну таблицю. Будь ласка, оберіть різні, щоб отримати їх різницю.")

        result_list = []
        for id1, row1 in self.rows.items():
            is_in_table = False
            for id2, row2 in table2.rows.items():
                if row1.values == row2.values:
                    is_in_table = True
                    break
            if not is_in_table:
                result_list.append(row1)
        return result_list


class Database:
    def __init__(self, name: str, file=None):
        if name is None or not name.strip():
            raise ValueError("База даних повинна мати назву. Будь ласка, спробуйте ще раз.")
        self.name = name
        self.tables: dict[str, Table] = {}
        if file:
            self.load_from_file(file)

    def create_table(self, table_name: str) -> bool:
        if table_name is None or not table_name.strip():
            raise ValueError("Таблиця повинна мати назву. Будь ласка, спробуйте ще раз.")
        if table_name not in self.tables.keys():
            table = Table(table_name)
            self.tables[table_name] = table
        else:
            raise ValueError("Таблиця з такою назвою вже існує.")
        return True

    def load_from_file(self, file_path: str):
        with open(file_path, 'r') as f:
            data = json.load(f)

        self.name = data["name"]
        for table_name, table_data in data["tables"].items():
            table = Table(table_name)
            table.columns = {col_name: Type[col_type] for col_name, col_type in table_data["columns"].items()}
            for row_id_str, row_data in table_data["rows"].items():
                row = Row()
                row.id = uuid.UUID(row_id_str)
                row.values = row_data["values"]
                row.column_types = {col_name: Type[col_type] for col_name, col_type in row_data["column_types"].items()}

                if not row.validate_row():
                    table.rows[row.id] = row
            self.tables[table_name] = table

    def save_to_file(self, file_path: str) -> None:
        data = {
            "name": self.name,
            "tables": {
                table_name: {
                    "columns": {col_name: col_type.name for col_name, col_type in table.columns.items()},
                    "rows": {
                        str(row_id): {
                            "values": row.values,
                            "column_types": {col_name: col_type.name for col_name, col_type in row.column_types.items()}
                        }
                        for row_id, row in table.rows.items()
                    }
                }
                for table_name, table in self.tables.items()
            }
        }
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
