import os
import mysql.connector

db_connection = mysql.connector.connect(
    host=os.getenv("MYSQLHOST"),
    port=int(os.getenv("MYSQLPORT")),
    database=os.getenv("MYSQL_DATABASE"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
)

cursor = db_connection.cursor()
