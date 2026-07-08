import sqlite3

def init_db():

    conn = sqlite3.connect("database.db")
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organizations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    admin_code TEXT NOT NULL
)
""")
    cursor.execute("""

    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    college TEXT,
    phone TEXT,
    status_message TEXT,
    status TEXT DEFAULT 'Active',
    role TEXT NOT NULL DEFAULT 'student',
    organization_id INTEGER,
    UNIQUE(email, organization_id)
)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        reg_number TEXT  NOT NULL,
        department TEXT NOT NULL,
        year TEXT NOT NULL,
        college TEXT,
        email TEXT ,
        phone TEXT,
        user_id INTEGER,
        admin_id INTEGER,
        organization_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(admin_id) REFERENCES users(id),
        FOREIGN KEY(organization_id) REFERENCES organizations(id),
        UNIQUE(reg_number, organization_id),
        UNIQUE(email, organization_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        date TEXT NOT NULL DEFAULT CURRENT_DATE,
        hour INTEGER NOT NULL,
        status TEXT NOT NULL,
        month TEXT,
        user_id INTEGER NOT NULL,
        organization_id INTEGER NOT NULL,
            FOREIGN KEY(student_id) REFERENCES student(id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(organization_id) REFERENCES organizations(id)

    )
    """)
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS academic_marks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    student_name TEXT NOT NULL,
    semester INTEGER NOT NULL,
    exam_type TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    marks INTEGER NOT NULL,
    result TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,

    FOREIGN KEY(student_id) REFERENCES student(id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(organization_id) REFERENCES organizations(id)
)
""")
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS semester_result(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    student_name TEXT NOT NULL,
    semester INTEGER NOT NULL,
    exam_type TEXT ,
    sgpa REAL DEFAULT 0,
    user_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,

    FOREIGN KEY(student_id) REFERENCES student(id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(organization_id) REFERENCES organizations(id),
    UNIQUE(student_id, semester)
)
""")
    
# ASSIGNMENTS TABLE

    cursor.execute("""
CREATE TABLE IF NOT EXISTS assignments(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,

    subject TEXT NOT NULL,

    description TEXT,

    due_date TEXT,

    file_path TEXT,

    user_id INTEGER,

    organization_id INTEGER,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id)

)
""")



# ASSIGNMENT SUBMISSIONS TABLE

    cursor.execute("""
CREATE TABLE IF NOT EXISTS assignment_submission(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    assignment_id INTEGER,

    student_id INTEGER,

    file_path TEXT,

    submitted_date TEXT DEFAULT CURRENT_TIMESTAMP,

    marks INTEGER DEFAULT 0,

    feedback TEXT,

    status TEXT DEFAULT 'Submitted',

    FOREIGN KEY(assignment_id)
    REFERENCES assignments(id),

    FOREIGN KEY(student_id)
    REFERENCES student(id)

)
""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    certificate_name TEXT NOT NULL,
    issuer TEXT NOT NULL,
    certificate_id TEXT,
    file_path TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',
    uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    organization_id INTEGER,
    FOREIGN KEY(student_id) REFERENCES student(id)
)
""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS delete_requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    request_date TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Pending'
    )
    """)

    conn.commit()
    conn.close()

    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()