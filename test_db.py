from db import get_connection

try:
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM students")
        total = cursor.fetchone()[0]

    print("Oracle connected successfully!")
    print("Total students:", total)

except Exception as e:
    print("Connection failed:", e)

finally:
    if "connection" in locals():
        connection.close()