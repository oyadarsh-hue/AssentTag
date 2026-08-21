import pymysql

connection = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='root',
    database='assentnew',
    port=3307
)

with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS follow_request (
            request_id INT AUTO_INCREMENT PRIMARY KEY,
            created_at DATETIME(6) NOT NULL,
            requester_user_id INT NOT NULL,
            target_user_id INT NOT NULL,
            UNIQUE KEY follow_request_unique (requester_user_id, target_user_id)
        )
    """)
    connection.commit()
print("Table created successfully")
