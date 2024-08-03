import csv
import config
from config import bot, db
from database import database, model


def import_database():
    with open('guilds.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        db.connect()
        next(csv_reader, None)
        for row in csv_reader:
            db.create(model.guilds_class(f"guilds"), {"server": row[0], "role": row[1]})
            print(row)
        db.close()
