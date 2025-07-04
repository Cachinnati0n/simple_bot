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
            production_order_id INT,
            amount INT NOT NULL,
            fulfilled_amount INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            channel_id VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'open',
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

    cursor.execute("""CREATE TABLE IF NOT EXISTS DropoffPanel (
    server_id VARCHAR(32),
    channel_id VARCHAR(32),
    message_id VARCHAR(32),
    PRIMARY KEY (server_id, channel_id)
    );   
    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS ProductionOrders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id VARCHAR(32),
    user_id VARCHAR(32),
    recipe_name VARCHAR(100),
    bay_number VARCHAR(20),
    title VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS ProductionPanels (
    production_order_id INT PRIMARY KEY,
    thread_id VARCHAR(32),
    message_id VARCHAR(32)
    );""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ProductionUI (
            server_id VARCHAR(32) PRIMARY KEY,
            channel_id VARCHAR(32) NOT NULL,
            message_id VARCHAR(32) NOT NULL
        );
        """)
    db_connection.commit()


cursor = db_connection.cursor()
