import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

print("ACADEMIC_MARKS")
cursor.execute("PRAGMA table_info(academic_marks)")
for row in cursor.fetchall():
    print(row)

print("\nSEMESTER_RESULT")
cursor.execute("PRAGMA table_info(semester_result)")
for row in cursor.fetchall():
    print(row)

conn.close()