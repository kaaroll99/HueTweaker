import csv
from config import bot, db
from database import database, model
import subprocess
import os



def export_database(db_config, filename='database_backup.sql'):
    command = [
        'mysqldump',
        '-h', db_config['db_host'],
        '-u', db_config['db_login'],
        f'-p{db_config["db_pass"]}',
        db_config['db_name'],
        '>', filename
    ]

    try:
        subprocess.run(' '.join(command), shell=True, check=True)
        print(f"Eksport zakończony. Baza danych zapisana do pliku {filename}")
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas eksportu bazy danych: {e}")


def import_database(db_config, filename='database_backup.sql'):
    command = [
        'mysql',
        '-h', db_config['db_host'],
        '-u', db_config['db_login'],
        f'-p{db_config["db_pass"]}',
        db_config['db_name'],
        '<', filename
    ]

    try:
        subprocess.run(' '.join(command), shell=True, check=True)
        print(f"Import zakończony. Baza danych wczytana z pliku {filename}")
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas importu bazy danych: {e}")

# Przykład użycia:
db_config = load_yml('token.yml')
export_database(db_config)
# import_database(db_config)