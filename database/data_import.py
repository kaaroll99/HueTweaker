import sqlite3
import mysql.connector
import config


def import_database():
    token_file = config.load_yml('token.yml')

    # Połączenie z bazą SQLite
    sqlite_conn = sqlite3.connect('guilds.db')
    sqlite_cursor = sqlite_conn.cursor()

    # Połączenie z bazą MySQL
    mysql_conn = mysql.connector.connect(
        host=token_file['db_host'],
        user=token_file['db_login'],
        password=token_file['db_pass'],
        database=token_file['db_name']
    )
    mysql_cursor = mysql_conn.cursor()

    # Pobranie danych z SQLite
    sqlite_cursor.execute("SELECT * FROM guilds")
    rows = sqlite_cursor.fetchall()

    # Wstawienie danych do MySQL
    for row in rows:
        mysql_cursor.execute("INSERT INTO guilds VALUES (%s, %s, %s)", row)
        print(row)

    mysql_conn.commit()

    # Zamknięcie połączeń
    sqlite_conn.close()
    mysql_conn.close()