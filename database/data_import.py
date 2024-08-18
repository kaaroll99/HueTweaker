import csv
import config
from config import bot, db
from database import database, model


def import_database():
    with open('guilds.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        with db as db_session:
            next(csv_reader, None)
            for row in csv_reader:
                db_session.create(model.guilds_class(f"guilds"), {"server": row[0], "role": row[1]})
                print(row)
