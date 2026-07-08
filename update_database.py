import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

admin_id = 8

queries = [
    ("student.user_id", "SELECT * FROM student WHERE user_id=?"),
    ("student.admin_id", "SELECT * FROM student WHERE admin_id=?"),
    ("attendance.user_id", "SELECT * FROM attendance WHERE user_id=?"),
    ("academic_marks.user_id", "SELECT * FROM academic_marks WHERE user_id=?"),
    ("semester_result.user_id", "SELECT * FROM semester_result WHERE user_id=?"),
    ("assignments.user_id", "SELECT * FROM assignments WHERE user_id=?")
]

for name, query in queries:
    cursor.execute(query, (admin_id,))
    rows = cursor.fetchall()
    print(f"\n{name}: {len(rows)} rows")
    for row in rows:
        print(row)

conn.close()