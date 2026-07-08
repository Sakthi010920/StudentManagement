import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
UPDATE users
SET name=?
WHERE id=?
""", ("Charan", 1))

conn.commit()
conn.close()

print("Updated successfully!")