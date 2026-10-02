#!/usr/bin/env python3
import csv
import time
from contextlib import suppress
from pathlib import Path

# Конфигурационные константы
OUTPUT_SQL_PATH = "db_init.sql"
SOURCE_DATA_DIR = Path("dataset")

# Альтернативная структура описания метаданных таблиц
METADATA = {
    "movies": ("movies.csv", [("id", "INTEGER", True), ("title", "TEXT", False), ("year", "INTEGER", False), ("genres", "TEXT", False)]),
    "ratings": ("ratings.csv", [("id", "INTEGER", True), ("user_id", "INTEGER", False), ("movie_id", "INTEGER", False), ("rating", "REAL", False), ("timestamp", "INTEGER", False)]),
    "tags": ("tags.csv", [("id", "INTEGER", True), ("user_id", "INTEGER", False), ("movie_id", "INTEGER", False), ("tag", "TEXT", False), ("timestamp", "INTEGER", False)]),
    "users": ("users.csv", [("id", "INTEGER", True), ("name", "TEXT", False), ("email", "TEXT", False), ("gender", "TEXT", False), ("register_date", "TEXT", False), ("occupation", "TEXT", False)])
}


def to_sql_value(raw_val: str) -> str:
    """Трансформирует текстовую ячейку CSV в валидный SQL-литерал."""
    if not raw_val or not (clean_val := raw_val.strip()):
        return "NULL"

    for parser in (int, float):
        with suppress(ValueError):
            parser(clean_val)
            return clean_val

    escaped = clean_val.replace("'", "''")
    return f"'{escaped}'"


def run_generation() -> None:
    clock_start = time.time()

    with open(OUTPUT_SQL_PATH, "w", encoding="utf-8") as sql_stream:
        # Шаг 1: Очистка старой структуры данных
        for table_name in METADATA:
            sql_stream.write(f"DROP TABLE IF EXISTS {table_name};\n")

        # Шаг 2: Инициализация новых таблиц
        for table_name, (_, columns) in METADATA.items():
            definitions = [
                f"{col_name} {col_type} PRIMARY KEY" if is_pk else f"{col_name} {col_type}"
                for col_name, col_type, is_pk in columns
            ]
            sql_stream.write(f"CREATE TABLE {table_name} ({', '.join(definitions)});\n")

        # Шаг 3: Наполнение таблиц данными из CSV-источников
        sql_stream.write("\nBEGIN TRANSACTION;\n")

        for table_name, (csv_filename, columns) in METADATA.items():
            target_csv = SOURCE_DATA_DIR / csv_filename
            
            if not target_csv.exists():
                sql_stream.write(f"-- [!] Файл {target_csv} не найден\n")
                continue

            column_names = [col[0] for col in columns]
            insert_template = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES"

            with open(target_csv, "r", encoding="utf-8") as csv_file:
                for record in csv.DictReader(csv_file, delimiter=","):
                    serialized_values = (to_sql_value(record.get(col, "")) for col in column_names)
                    sql_stream.write(f"{insert_template} ({', '.join(serialized_values)});\n")

        sql_stream.write("COMMIT;\n")

    execution_time = time.time() - clock_start
    print(f"Скрипт {OUTPUT_SQL_PATH} сгенерирован за {execution_time:.3f} сек.")


if __name__ == "__main__":
    run_generation()
