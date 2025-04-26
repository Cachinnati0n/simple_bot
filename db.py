import os
import mysql.connector

db_connection = mysql.connector.connect(
    host=os.getenv("MYSQLHOST"),
    port=int(os.getenv("MYSQLPORT")),
    database=os.getenv("MYSQL_DATABASE"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
)

def initialize_tables():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS RecurringOrders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            server_id VARCHAR(50) NOT NULL,
            resource_name VARCHAR(100) NOT NULL,
            amount INT NOT NULL,
            recurrence VARCHAR(50) NOT NULL,
            next_run_time DATETIME NOT NULL,
            channel_id VARCHAR(50) NOT NULL,
            active BOOLEAN DEFAULT TRUE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS GeneratedOrders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            recurring_order_id INT,
            user_id VARCHAR(50) NOT NULL,
            server_id VARCHAR(50) NOT NULL,
            resource_name VARCHAR(100) NOT NULL,
            amount INT NOT NULL,
            fulfilled_amount INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            channel_id VARCHAR(50) NOT NULL,
            FOREIGN KEY (recurring_order_id) REFERENCES RecurringOrders(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Dropoffs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT,
            user_id VARCHAR(50),
            amount INT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES GeneratedOrders(id)
        );
    """)

    db_connection.commit()

cursor = db_connection.cursor()
