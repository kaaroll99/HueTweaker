import csv
from database import model, database

from utils.data_loader import load_yml

token_file = load_yml('assets/token.yml')


def export_database(db, filename='guilds_export.csv'):
    with open(filename, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['server', 'role'])

        with db as db_session:
            query = db_session.select(model.guilds_class("guilds"), {})
            for guild in query:
                csv_writer.writerow([guild['server'], guild['role']])

    print(f"Eksport zakończony. Dane zapisano do pliku {filename}")


def import_database(db, filename='guilds_export.csv'):
    with open(filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        next(csv_reader, None)
        for row in csv_reader:
            db.create(model.guilds_class(f"guilds"), {"server": row[0], "role": row[1]})
            print(f"Zaimportowano: {row}")

    print(f"Import zakończony. Dane wczytano z pliku {filename}")

db = database.Database(url=f"mysql+pymysql://{token_file['db_login']}:{token_file['db_pass']}@{token_file['db_host']}/{token_file['db_name']}")

export_database(db)
# import_database(db)
