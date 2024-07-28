import csv
import mysql.connector
import config
from config import bot, db
from database import database, model


def import_database():
    token_file = config.load_yml('token.yml')

    # Otworzenie pliku CSV
    with open('guilds.csv', 'r') as csv_file: # Zmień 'guilds.csv' na rzeczywistą nazwę pliku
        csv_reader = csv.reader(csv_file)

        db.connect()
        # Iteracja po wierszach CSV (pomijając nagłówek, jeśli istnieje)
        next(csv_reader, None)
        for row in csv_reader:
            db.create(model.guilds_class(f"guilds"), {"server": row[0], "role": row[1]})
            print(row)
        db.close()
