from werkzeug.utils import secure_filename
from flask import Flask, config, render_template, request, redirect,flash,url_for,session,jsonify
import sqlite3,os
print("DATABASE PATH:",os.path.abspath("database.db"))
from datetime import datetime
from zoneinfo import ZoneInfo
app = Flask(__name__)
app.secret_key = "student_management_secret"

UPLOAD_FOLDER = os.path.join(app.root_path, "uploads", "assignments")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create the folder automatically if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("UPLOAD FOLDER:", app.config["UPLOAD_FOLDER"])
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        department = request.form['department']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        role = request.form['role'].lower()

        organization = request.form['organization'].strip()

        admin_code = request.form.get('admin_code', '').strip()
        confirm_admin_code = request.form.get('confirm_admin_code', '').strip()

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Check organization
        cursor.execute(
            "SELECT id, admin_code FROM organizations WHERE name=?",
            (organization,)
        )

        org = cursor.fetchone()

        if role == "admin":

            # First admin of a new organization
            if org is None:

                if admin_code == "" or confirm_admin_code == "":
                    conn.close()
                    return render_template(
                        "register.html",
                        message="Create an Admin Code.",
                        message_type="error"
                    )

                if admin_code != confirm_admin_code:
                    conn.close()
                    return render_template(
                        "register.html",
                        message="Admin codes do not match.",
                        message_type="error"
                    )

                cursor.execute("""
                    INSERT INTO organizations(name, admin_code)
                    VALUES(?, ?)
                """, (organization, admin_code))

                organization_id = cursor.lastrowid

            else:
                organization_id = org[0]

                if admin_code != org[1]:
                    conn.close()
                    return render_template(
                        "register.html",
                        message="Invalid Admin Code!",
                        message_type="error"
                    )

        else:
            # Student registration
            if org is None:
                conn.close()
                return render_template(
                    "register.html",
                    message="Organization not found.",
                    message_type="error"
                )

            organization_id = org[0]

        # Check email only inside this organization
        cursor.execute("""
            SELECT id
            FROM users
            WHERE email = ?
            AND organization_id = ?
        """, (email, organization_id))

        if cursor.fetchone():
            conn.close()
            return render_template(
                "register.html",
                message="Email already exists in this organization!",
                message_type="error"
            )

        # Create user
        cursor.execute("""
            INSERT INTO users
            (
                name,
                department,
                email,
                password,
                phone,
                role,
                organization_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            department,
            email,
            password,
            phone,
            role,
            organization_id
        ))

        user_id = cursor.lastrowid

        # Link student account to student record
        cursor.execute("""
            UPDATE student
            SET user_id = ?
            WHERE email = ?
            AND organization_id = ?
        """, (user_id, email, organization_id))

        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                department,
                email,
                password,
                college,
                phone,
                role,
                status,
                organization_id
            FROM users
            WHERE email=? AND password=?
        """, (email, password))

        user = cursor.fetchone()

        # Invalid login
        if not user:
            conn.close()
            return render_template(
                'login.html',
                message="Invalid Email or Password!",
                message_type="error"
            )

        # Check account status
        if user[8] == "Inactive":
            conn.close()
            return render_template(
                'login.html',
                message="Your account has been deactivated by the administrator.",
                message_type="error"
            )

        # ==========================
        # CREATE SESSION
        # ==========================
        session['user_id'] = user[0]
        session['name'] = user[1]
        session['email'] = user[3]
        session['role'] = user[7]
        session['organization_id'] = user[9]

        # ==========================
        # GET STUDENT ID
        # ==========================
        if user[7] == "student":

            cursor.execute("""
                SELECT id
                FROM student
                WHERE email = ?
                AND organization_id = ?
            """, (
                user[3],
                user[9]
            ))

            student = cursor.fetchone()

            if student:
                session["student_id"] = student[0]
                print("Student ID:", session["student_id"])
            else:
                session["student_id"] = None
                print("Student record not found!")

        conn.close()

        print("LOGIN SUCCESS")
        print("ROLE:", session.get('role'))

        # ==========================
        # REDIRECT
        # ==========================
        if user[7] == "admin":
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('student_dashboard'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():

    # User must be logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Only admin can access dashboard
    if session.get('role') != 'admin':
        return redirect(url_for('student_dashboard'))

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Get admin details
    cursor.execute("""
        SELECT
            users.name,
            users.department,
            organizations.name AS organization_name,
            users.email,
            users.phone
        FROM users
        JOIN organizations
            ON users.organization_id = organizations.id
        WHERE users.id = ?
    """, (session['user_id'],))

    user = cursor.fetchone()

    if user is None:
        conn.close()
        session.clear()
        return redirect(url_for('login'))

    # Total students added by this admin
    cursor.execute("""
        SELECT COUNT(*)
        FROM student
        WHERE organization_id = ?
        AND admin_id = ?
    """, (session['organization_id'], session['user_id']))

    total_students = cursor.fetchone()[0]
    current_month = datetime.now().strftime("%Y-%m")

    # Attendance statistics
    cursor.execute("""
        SELECT status, COUNT(*)
        FROM attendance
        WHERE organization_id = ?
        AND user_id = ?
        AND month = ?
        GROUP BY status
    """, (session['organization_id'], session['user_id'], current_month))

    attendance = cursor.fetchall()

    present = 0
    absent = 0

    for row in attendance:
        status = row[0]
        count = row[1]

        if status == "Present":
            present = count
        elif status == "Absent":
            absent = count

    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        total_students=total_students,
        present=present,
        absent=absent
    )

@app.route('/student_dashboard')
def student_dashboard():

    # =========================
    # LOGIN CHECK
    # =========================
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    user_id = session["user_id"]

    # =========================
    # CHECK ACCOUNT STATUS
    # =========================
    cursor.execute("""
        SELECT status
        FROM users
        WHERE id=?
    """, (user_id,))

    row = cursor.fetchone()

    if row and row[0] == "Inactive":
        session.clear()
        conn.close()
        return redirect(url_for("login"))

    # =========================
    # USER DETAILS
    # =========================
    cursor.execute("""
        SELECT
            name,
            email,
            phone
        FROM users
        WHERE id=?
    """, (user_id,))

    user_row = cursor.fetchone()

    if user_row is None:
        conn.close()
        return redirect(url_for("login"))

    # =========================
    # STUDENT DETAILS
    # =========================
    cursor.execute("""
        SELECT
            id,
            reg_number,
            department,
            year,
            college
        FROM student
        WHERE user_id=?
    """, (user_id,))

    student_row = cursor.fetchone()

    if student_row is None:
        conn.close()
        return redirect(url_for("login"))

    student_id = student_row[0]

    user = {
        "name": user_row[0],
        "email": user_row[1],
        "phone": user_row[2],
        "reg_number": student_row[1],
        "department": student_row[2],
        "year": student_row[3],
        "college": student_row[4]
    }

    # =========================
    # CURRENT MONTH
    # =========================
    current_month_db = datetime.now().strftime("%Y-%m")
    current_month = datetime.now().strftime("%B %Y")

    # =========================
    # PRESENT COUNT
    # =========================
    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE student_id=?
        AND status='Present'
        AND month=?
    """, (student_id, current_month_db))

    present = cursor.fetchone()[0]

    # =========================
    # ABSENT COUNT
    # =========================
    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE student_id=?
        AND status='Absent'
        AND month=?
    """, (student_id, current_month_db))

    absent = cursor.fetchone()[0]

    total = present + absent

    if total > 0:
        percentage = round((present / total) * 100, 2)
    else:
        percentage = 0

    # =========================
    # LATEST SGPA
    # =========================
    cursor.execute("""
        SELECT sgpa
        FROM semester_result
        WHERE student_id=?
        ORDER BY semester DESC
        LIMIT 1
    """, (student_id,))

    sgpa_row = cursor.fetchone()

    if sgpa_row:
        sgpa = sgpa_row[0]
    else:
        sgpa = 0

    conn.close()

    return render_template(
        "student_dashboard.html",
        user=user,
        student=student_row,
        present=present,
        absent=absent,
        percentage=percentage,
        sgpa=sgpa,
        current_month=current_month
    )

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Only admin can add students
    if session.get('role') != 'admin':
        return redirect(url_for('student_dashboard'))

    message = ""
    message_type = ""

    if request.method == 'POST':

        name = request.form['name']
        reg_number = request.form['reg_no']
        department = request.form['department']
        year = request.form['year']
        college = request.form.get('college', '')
        email = request.form['email']
        phone = request.form['phone']

        conn = sqlite3.connect('database.db')
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Check duplicate register number
        cursor.execute("""
    SELECT id
    FROM student
    WHERE reg_number = ?
    AND organization_id = ?
""", (
    reg_number,
    session['organization_id']
))

        if cursor.fetchone():
            message = "❌ Register Number already exists!"
            message_type = "error"

        else:
            # Check duplicate email
            cursor.execute("""
    SELECT id
    FROM student
    WHERE email = ?
    AND organization_id = ?
""", (
    email,
    session['organization_id']
))

            if cursor.fetchone():
                message = "❌ Email already exists!"
                message_type = "error"

            else:
                # Add student WITHOUT user account
                cursor.execute("""
                    INSERT INTO student
                    (name, reg_number, department, year, college, email, phone, admin_id, organization_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    reg_number,
                    department,
                    year,
                    college,
                    email,
                    phone,
                    session['user_id'],
                    session['organization_id']
                ))

                conn.commit()

                message = "✅ Student added successfully!"
                message_type = "success"

        conn.close()

    return render_template(
        'add_student.html',
        message=message,
        message_type=message_type
    )
    
@app.route('/view_students')
def view_students():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return redirect(url_for('student_dashboard'))

    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM student
        WHERE organization_id = ?
        AND admin_id = ?
        ORDER BY id ASC
    """, (session['organization_id'], session['user_id']))

    students = cursor.fetchall()

    conn.close()

    return render_template(
        'view_students.html',
        students=students
    )
@app.route('/update_student/<int:id>', methods=['GET', 'POST'])
def update_student(id):

    # Login check
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Admin only
    if session.get('role') != 'admin':
        return redirect(url_for('student_dashboard'))

    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    if request.method == 'POST':

        name = request.form['name']
        reg_number = request.form['reg_number']
        department = request.form['department']
        year = request.form['year']
        college = request.form.get('college', '')
        email = request.form['email']
        phone = request.form['phone']

        # Check duplicate register number
        cursor.execute("""
            SELECT id
            FROM student
            WHERE reg_number=? AND id!=?
        """, (reg_number, id))

        if cursor.fetchone():
            conn.close()
            flash("❌ Register Number already exists!", "error")
            return redirect(url_for("update_student", id=id))

        # Check duplicate email
        cursor.execute("""
            SELECT id
            FROM student
            WHERE email=? AND id!=?
        """, (email, id))

        if cursor.fetchone():
            conn.close()
            flash("❌ Email already exists!", "error")
            return redirect(url_for("update_student", id=id))

        # Update student
        cursor.execute("""
            UPDATE student
            SET
                name=?,
                reg_number=?,
                department=?,
                year=?,
                college=?,
                email=?,
                phone=?
            WHERE id=?
        """, (
            name,
            reg_number,
            department,
            year,
            college,
            email,
            phone,
            id
        ))

        conn.commit()
        conn.close()

        flash("✅ Student details updated successfully!", "success")
        return redirect(url_for("update_student", id=id))
    cursor.execute("SELECT id, name, reg_number FROM student")
    print(cursor.fetchall())

    # Load student details
    cursor.execute("""
        SELECT *
        FROM student
        WHERE id=?
    """, (id,))

    student = cursor.fetchone()
    conn.close()

    if student is None:
        return "Student not found!"

    return render_template(
        "update_student.html",
        student=student
    )

@app.route('/search_student', methods=['GET', 'POST'])
def search_student():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return redirect(url_for('student_dashboard'))

    students = []
    message = ""

    if request.method == "POST":

        name = request.form.get("keyword", "").strip()
        reg_number = request.form.get("register_number", "").strip()

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM student
            WHERE organization_id=?
        """

        params = [session["organization_id"]]

        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")

        if reg_number:
            query += " AND reg_number LIKE ?"
            params.append(f"%{reg_number}%")

        cursor.execute(query, params)
        students = cursor.fetchall()

        conn.close()

        if not students:
            message = "No student record found."

    return render_template(
        "search_student.html",
        student=students,
        message=message
    )
    
from datetime import datetime

@app.route('/create_assignment', methods=['GET', 'POST'])
def create_assignment():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':

        title = request.form['title']
        subject = request.form['subject']
        description = request.form['description']

        # Convert due date format
        due_date_input = request.form['due_date']

        try:
            due_date = datetime.strptime(
                due_date_input,
                "%Y-%m-%d"
            ).strftime("%d-%m-%Y")

        except ValueError:
            due_date = due_date_input


        file = request.files.get('file')
        filename = ""

        if file and file.filename != "":
            filename = secure_filename(file.filename)

            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)

            file.save(
                os.path.join(upload_folder, filename)
            )


        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO assignments
            (title, subject, description, due_date, file_path, user_id, organization_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            subject,
            description,
            due_date,
            filename,
            session['user_id'],
            session['organization_id']
        ))

        conn.commit()
        conn.close()

        flash("✅ Assignment created successfully!", "success")

        return redirect(url_for('create_assignment'))


    return render_template("create_assignment.html")


from datetime import datetime

@app.route('/manage_assignments')
def manage_assignments():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return redirect(url_for('student_dashboard'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            title,
            subject,
            due_date,
            file_path,
            created_at
        FROM assignments
        WHERE organization_id = ?
        ORDER BY id DESC
    """, (session['organization_id'],))

    rows = cursor.fetchall()

    conn.close()

    assignments = []

    for row in rows:
        row = list(row)

        # Format due date
        if row[3]:
            try:
                date = datetime.strptime(row[3], "%Y-%m-%d")
                row[3] = date.strftime("%d-%m-%Y")
            except ValueError:
                pass

        assignments.append(row)

    return render_template(
        "manage_assignments.html",
        assignments=assignments
    )

@app.route("/delete_assignment/<int:assignment_id>")
def delete_assignment(assignment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("student_dashboard"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get file name before deleting
    cursor.execute("""
        SELECT file_path
        FROM assignments
        WHERE id = ?
    """, (assignment_id,))

    assignment = cursor.fetchone()

    if assignment and assignment[0]:

        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            assignment[0]
        )

        if os.path.exists(file_path):
            os.remove(file_path)


    # Delete assignment submissions first
    cursor.execute("""
        DELETE FROM assignment_submission
        WHERE assignment_id = ?
    """, (assignment_id,))


    # Delete assignment
    cursor.execute("""
        DELETE FROM assignments
        WHERE id = ?
    """, (assignment_id,))


    conn.commit()
    conn.close()

    flash("✅ Assignment deleted successfully!", "success")

    return redirect(url_for("manage_assignments"))

@app.route("/student_assignments")
def student_assignments():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "student":
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            title,
            subject,
            description,
            due_date,
            file_path
        FROM assignments
        WHERE organization_id=?
        ORDER BY due_date ASC
    """, (session["organization_id"],))

    assignments = cursor.fetchall()

    conn.close()

    return render_template(
        "student_assignments.html",
        assignments=assignments
    ) 

from flask import send_from_directory   
@app.route("/uploads/assignments/<filename>")
def uploaded_assignment(filename):
    return send_from_directory(
        "uploads/assignments",
        filename
    )

@app.route("/submit_assignment/<int:assignment_id>", methods=["GET", "POST"])
def submit_assignment(assignment_id):

    # Check login
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only students can submit assignments
    if session.get("role") != "student":
        return redirect(url_for("student_dashboard"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get assignment details
    cursor.execute("""
        SELECT
            id,
            title,
            subject,
            description,
            due_date,
            file_path
        FROM assignments
        WHERE id = ?
    """, (assignment_id,))

    assignment = cursor.fetchone()

    if not assignment:
        conn.close()
        flash("❌ Assignment not found.", "error")
        return redirect(url_for("student_assignments"))

    if request.method == "POST":

        # Check if already submitted
        cursor.execute("""
            SELECT id
            FROM assignment_submission
            WHERE assignment_id = ? AND student_id = ?
        """, (
            assignment_id,
            session["student_id"]
        ))

        existing = cursor.fetchone()

        if existing:
            conn.close()
            flash("⚠️ You have already submitted this assignment.", "warning")
            return redirect(url_for("submit_assignment", assignment_id=assignment_id))

        # Check file
        if "file" not in request.files:
            conn.close()
            flash("❌ Please choose a file.", "error")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            conn.close()
            flash("❌ Please choose a file.", "error")
            return redirect(request.url)

        # Save uploaded file
        filename = secure_filename(file.filename)

        upload_folder = os.path.join("uploads", "submissions")
        os.makedirs(upload_folder, exist_ok=True)

        file.save(os.path.join(upload_folder, filename))

        # Save submission in database
        cursor.execute("""
            INSERT INTO assignment_submission
            (assignment_id, student_id, file_path)
            VALUES (?, ?, ?)
        """, (
            assignment_id,
            session["student_id"],
            filename
        ))

        conn.commit()
        conn.close()

        flash("✅ Assignment submitted successfully!", "success")
        return redirect(url_for("submit_assignment", assignment_id=assignment_id))

    conn.close()

    return render_template(
        "submit_assignment.html",
        assignment=assignment
    )

@app.route("/assignment_submissions")
def assignment_submissions():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only admin can access this page
    if session.get("role") != "admin":
        return redirect(url_for("student_dashboard"))

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            assignment_submission.id,
            assignments.title,
            student.name,
            student.reg_number,
            student.department,
            assignment_submission.file_path,
            assignment_submission.submitted_date,
            assignment_submission.marks,
            assignment_submission.feedback,
            assignment_submission.status

        FROM assignment_submission

        INNER JOIN assignments
            ON assignments.id = assignment_submission.assignment_id

        INNER JOIN student
            ON student.id = assignment_submission.student_id

        WHERE assignments.organization_id = ?

        ORDER BY assignment_submission.submitted_date DESC
    """, (session["organization_id"],))

    rows = cursor.fetchall()
    conn.close()

    submissions = []

    for row in rows:
        submission = list(row)

        # Format submitted date
        if submission[6]:
            try:
                dt = datetime.strptime(submission[6], "%Y-%m-%d %H:%M:%S")
                submission[6] = dt.strftime("%d-%m-%Y")
            except (ValueError, TypeError):
                pass

        submissions.append(submission)

    return render_template(
        "assignment_submissions.html",
        submissions=submissions
    )
    
from flask import send_from_directory

@app.route("/download_submission/<filename>")
def download_submission(filename):

    upload_folder = "uploads/submissions"

    return send_from_directory(
        upload_folder,
        filename,
        as_attachment=False
    )    

@app.route("/mark_attendance/<int:student_id>/<status>", methods=["GET"])
def mark_attendance(student_id, status):

    # Login check
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        })

    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "message": "Access denied."
        })

    # Validate status
    if status not in ["Present", "Absent"]:
        return jsonify({
            "success": False,
            "message": "Invalid attendance status."
        })

    # Get selected hour
    hour = request.args.get("hour")

    if not hour:
        return jsonify({
            "success": False,
            "message": "Please select an hour."
        })

    try:
        hour = int(hour)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid hour."
        })

    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    today = now.strftime("%Y-%m-%d")
    attendance_time = now.strftime("%Y-%m-%d %H:%M:%S")
    month = now.strftime("%Y-%m")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:

        # Check student exists
        cursor.execute("""
            SELECT id
            FROM student
            WHERE id = ?
        """, (student_id,))

        if cursor.fetchone() is None:
            conn.close()
            return jsonify({
                "success": False,
                "message": "Student not found."
            })

        # Check duplicate
        cursor.execute("""
            SELECT id
            FROM attendance
            WHERE student_id=?
            AND substr(date,1,10)=?
            AND hour=?
        """, (student_id, today, hour))

        if cursor.fetchone():
            conn.close()
            return jsonify({
                "success": False,
                "message": f"Hour {hour} already marked."
            })

        organization_id = session.get("organization_id")

        if organization_id is None:
            organization_id = 1

        cursor.execute("""
            INSERT INTO attendance
            (student_id,date,hour,status,month,user_id,organization_id)
            VALUES(?,?,?,?,?,?,?)
        """,(
            student_id,
            attendance_time,
            hour,
            status,
            month,
            session["user_id"],
            organization_id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": f"{status} marked successfully for Hour {hour}."
        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        })

    finally:
        conn.close()

@app.route('/view_attendance/<int:student_id>')
def view_attendance(student_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Student name
    cursor.execute("""
        SELECT name
        FROM student
        WHERE id=?
    """, (student_id,))

    student_ = cursor.fetchone()

    if not student_:
        conn.close()
        return "Student not found"

    student_name = student_[0]

    # Attendance records
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
    SELECT date, hour, status
    FROM attendance
    WHERE student_id = ?
      AND substr(date, 1, 10) = ?
    ORDER BY hour ASC
""", (student_id, today))
    data = cursor.fetchall()

    records = []

    present = 0
    absent = 0

    for date_time, hour, status in data:

        try:
            dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dt = datetime.fromisoformat(date_time)

        date = dt.strftime("%d-%m-%Y")
        time = dt.strftime("%I:%M %p")

        if status == "Present":
            present += 1
        else:
            absent += 1

        records.append({
            "date": date,
            "time": time,
            "hour": hour,
            "status": status
        })

    total = present + absent

    percentage = 0

    if total > 0:
        percentage = round((present / total) * 100, 2)

    conn.close()

    return render_template(
        "view_attendance.html",
        student_name=student_name,
        records=records,
        present=present,
        absent=absent,
        percentage=percentage
    )
@app.route('/attendance_summary/<int:student_id>')
def attendance_summary(student_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Students can only view their own attendance
    if session.get("role") != "admin":

        cursor.execute("""
            SELECT id
            FROM student
            WHERE user_id=?
        """, (session["user_id"],))

        own_student = cursor.fetchone()

        if not own_student:
            conn.close()
            return redirect(url_for("student_dashboard"))

        if own_student[0] != student_id:
            conn.close()
            return redirect(url_for("student_dashboard"))

    # Get student name
    cursor.execute("""
        SELECT name
        FROM student
        WHERE id=?
    """, (student_id,))

    student = cursor.fetchone()

    if not student:
        conn.close()
        return "Student not found"

    student_name = student[0]

    # Get attendance summary
    current_month = datetime.now().strftime("%Y-%m")
    cursor.execute("""
        SELECT LOWER(status), COUNT(*)
        FROM attendance
        WHERE student_id=?
        AND month=?
        GROUP BY LOWER(status)
    """, (student_id, current_month))

    rows = dict(cursor.fetchall())

    present = rows.get("present", 0)
    absent = rows.get("absent", 0)

    total = present + absent
    percentage = round((present / total) * 100, 2) if total > 0 else 0

    conn.close()

    return render_template(
        "attendance_summary.html",
        student_name=student_name,
        present=present,
        absent=absent,
        percentage=percentage
    )
    
@app.route('/academic', methods=['GET', 'POST'])
def academic():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get("role") != "admin":
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":

        # Get values from the form
        semester = request.form.get("semester")
        exam_type = request.form.get("exam_type")

        if not semester or not exam_type:
            flash("Please select Semester and Exam Type.", "warning")
            return redirect(url_for("academic"))

        # Store in session
        session["semester"] = semester
        session["exam_type"] = exam_type

        return redirect(url_for("add_academic"))

    return render_template("academic.html")

@app.route('/add_academic', methods=['GET', 'POST'])
def add_academic():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get("role") != "admin":
        return redirect(url_for("student_dashboard"))

    # Get selected semester and exam type from session
    semester = session.get("semester")
    exam_type = session.get("exam_type")

    if semester is None or exam_type is None:
        flash("Please select Semester and Exam Type first.", "warning")
        return redirect(url_for("academic"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get students
    cursor.execute("""
        SELECT id, name, reg_number
        FROM student
        WHERE organization_id = ?
        ORDER BY name
    """, (session["organization_id"],))

    students = cursor.fetchall()

    if request.method == "POST":

        student_id = request.form["student_id"]

        subjects = request.form.getlist("subject[]")
        marks = request.form.getlist("marks[]")

        marks_list = []

        for subject, mark in zip(subjects, marks):

            subject = subject.strip()

            if not subject or mark == "":
                continue

            mark = int(mark)

            marks_list.append(mark)

            # Pass / Fail
            if mark >= 40:
                result = "Pass"
            else:
                result = "Fail"

            cursor.execute("""
                INSERT INTO academic_marks
                (
                    student_id,
                    semester,
                    exam_type,
                    subject_name,
                    marks,
                    result,
                    user_id,
                    organization_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                semester,
                exam_type,
                subject,
                mark,
                result,
                session["user_id"],
                session["organization_id"]
            ))

        # SGPA Calculation
        def calculate_sgpa(marks_list):

            total_points = 0
            count = 0

            for mark in marks_list:

                if mark >= 90:
                    grade_point = 10
                elif mark >= 80:
                    grade_point = 9
                elif mark >= 70:
                    grade_point = 8
                elif mark >= 60:
                    grade_point = 7
                elif mark >= 50:
                    grade_point = 6
                elif mark >= 40:
                    grade_point = 5
                else:
                    grade_point = 0

                total_points += grade_point
                count += 1

            if count == 0:
                return 0

            return round(total_points / count, 2)

        sgpa = 0

        if exam_type.lower() == "semester":
            sgpa = calculate_sgpa(marks_list)

        # Check existing SGPA
        cursor.execute("""
            SELECT id
            FROM semester_result
            WHERE student_id=?
            AND semester=?
            AND exam_type=?
        """,
        (
            student_id,
            semester,
            exam_type
        ))

        existing = cursor.fetchone()

        if existing:

            cursor.execute("""
                UPDATE semester_result
                SET
                    sgpa=?,
                    user_id=?,
                    organization_id=?
                WHERE student_id=?
                AND semester=?
                AND exam_type=?
            """,
            (
                sgpa,
                session["user_id"],
                session["organization_id"],
                student_id,
                semester,
                exam_type
            ))

        else:

            cursor.execute("""
                INSERT INTO semester_result
                (
                    student_id,
                    semester,
                    exam_type,
                    sgpa,
                    user_id,
                    organization_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                semester,
                exam_type,
                sgpa,
                session["user_id"],
                session["organization_id"]
            ))

        conn.commit()

        flash(
            f"✅ Marks saved successfully! SGPA = {sgpa}",
            "success"
        )

        conn.close()

        return redirect(url_for("add_academic"))

    conn.close()

    return render_template(
        "add_academic.html",
        students=students,
        semester=semester,
        exam_type=exam_type
    )
@app.route('/view_academics/<int:student_id>', methods=['GET', 'POST'])
def view_academics(student_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Student Details
    cursor.execute("""
        SELECT name, reg_number, department
        FROM student
        WHERE id=?
    """, (student_id,))

    student = cursor.fetchone()

    if not student:
        conn.close()
        return "Student not found"

    student_name = student[0]
    reg_number = student[1]
    department = student[2]

    records = []
    sgpa = None
    semester = None
    exam_type = None

    if request.method == "POST":

        semester = int(request.form["semester"])
        exam_type = request.form["exam_type"]

        # Fetch academic marks
        cursor.execute("""
            SELECT subject_name, marks, result
            FROM academic_marks
            WHERE student_id=?
            AND semester=?
            AND exam_type=?
            ORDER BY subject_name
        """, (student_id, semester, exam_type))

        records = cursor.fetchall()

        # Fetch stored SGPA
        if exam_type == "Semester":

            cursor.execute("""
                SELECT sgpa
                FROM semester_result
                WHERE student_id=?
                AND semester=?
                LIMIT 1
            """, (student_id, semester))

            row = cursor.fetchone()

            if row:
                sgpa = row[0]

    conn.close()

    return render_template(
        "view_academic.html",
        student_name=student_name,
        reg_number=reg_number,
        department=department,
        records=records,
        sgpa=sgpa,
        exam_type=exam_type,
        semester=semester
    )
    
@app.route('/upload_certificate', methods=['GET', 'POST'])
def upload_certificate():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Only students can upload certificates
    if session.get("role") != "student":
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get the logged-in student's ID
    cursor.execute("""
        SELECT id
        FROM student
        WHERE user_id = ?
    """, (session["user_id"],))

    student = cursor.fetchone()

    if student is None:
        conn.close()
        flash("Student record not found.", "danger")
        return redirect(url_for("student_dashboard"))

    student_id = student[0]

    if request.method == "POST":

        certificate_name = request.form["certificate_name"]
        issuer = request.form["issuer"]
        certificate_id = request.form["certificate_id"]

        file = request.files["certificate"]

        upload_folder = "uploads/certificates"

        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file.filename)

        filepath = os.path.join(upload_folder, filename)

        file.save(filepath)

        cursor.execute("""
            INSERT INTO certificates
            (
                
                certificate_name,
                issuer,
                certificate_id,
                file_path,
                status,
                user_id,
                organization_id
            )
            VALUES ( ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            certificate_name,
            issuer,
            certificate_id,
            filepath,
            "Pending",
            session["user_id"],
            session["organization_id"]
        ))

        conn.commit()

        flash("✅ Certificate uploaded successfully.", "success")

        conn.close()

        return redirect(url_for("upload_certificate"))

    conn.close()

    return render_template("upload_certificate.html")

@app.route('/view_certificates')
def view_certificates():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get("role") != "admin":
        return redirect(url_for("student_dashboard"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            certificates.id,
            student.name,
            student.reg_number,
            certificates.certificate_name,
            certificates.issuer,
            certificates.certificate_id,
            certificates.file_path,
            certificates.status
        FROM certificates
        JOIN student
        ON certificates.student_id = student.id
        WHERE certificates.organization_id = ?
        ORDER BY certificates.id DESC
    """, (session["organization_id"],))

    certificates = cursor.fetchall()

    conn.close()

    return render_template(
        "view_certificates.html",
        certificates=certificates
    )
@app.route('/view_certificate/<path:filename>')
def view_certificate(filename):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    upload_folder = os.path.join("uploads", "certificates")

    return send_from_directory(upload_folder, filename)  

@app.route('/verify_certificate/<int:certificate_id>')
def verify_certificate(certificate_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get("role") != "admin":
        return redirect(url_for("student_dashboard"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE certificates
        SET status = 'Verified'
        WHERE id = ?
    """, (certificate_id,))

    conn.commit()
    conn.close()

    flash("✅ Certificate verified successfully.", "success")

    return redirect(url_for("view_certificates")) 

@app.route('/reject_certificate/<int:certificate_id>')
def reject_certificate(certificate_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get("role") != "admin":
        return redirect(url_for("student_dashboard"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE certificates
        SET status = 'Rejected'
        WHERE id = ?
    """, (certificate_id,))

    conn.commit()
    conn.close()

    flash("❌ Certificate rejected.", "warning")

    return redirect(url_for("view_certificates"))
    
@app.route('/delete_student/<int:id>')
def delete_student(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return redirect(url_for('student_dashboard'))

    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Get student details first
    cursor.execute("""
        SELECT name
        FROM student
        WHERE id=?
    """, (id,))

    student = cursor.fetchone()

    if student:

        student_name = student[0]

        # Delete attendance
        cursor.execute("""
            DELETE FROM attendance
            WHERE student_id=?
        """, (id,))

        # Delete marks
        cursor.execute("""
            DELETE FROM academic_marks
            WHERE student_id=?
        """, (id,))

        # Delete student
        cursor.execute("""
            DELETE FROM student
            WHERE id=?
        """, (id,))

    conn.commit()
    conn.close()

    return redirect(url_for('view_students'))

@app.route('/request_delete_account', methods=['POST'])
def request_delete_account():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get the logged-in student's ID
    cursor.execute("""
        SELECT id
        FROM student
        WHERE user_id=?
    """, (session['user_id'],))

    student = cursor.fetchone()

    if not student:
        conn.close()
        flash("Student record not found.")
        return redirect(url_for('student_dashboard'))

    student_id = student[0]

    # Check if a pending request already exists
    cursor.execute("""
        SELECT id
        FROM delete_requests
        WHERE user_id=? AND status='Pending'
    """, (session['user_id'],))

    existing = cursor.fetchone()

    if existing:
        conn.close()
        flash("You have already submitted a deletion request.", "warning")
        return redirect(url_for('student_dashboard'))

    # Insert a new delete request
    request_time = datetime.now().strftime("%d-%m-%y %H:%M:%S")
    cursor.execute("""
    INSERT INTO delete_requests(user_id, student_id, request_date)
    VALUES(?, ?, ?)
""", (session['user_id'], student_id, request_time))

    conn.commit()
    conn.close()

    flash("✅ Your account deletion request has been sent to the administrator.", "success")

    return redirect(url_for('student_dashboard'))


@app.route('/delete_requests')
def delete_requests():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get("role") != "admin":
        return redirect(url_for("student_dashboard"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            delete_requests.id,
            student.name,
            student.reg_number,
            student.department,
            delete_requests.request_date,
            delete_requests.status
        FROM delete_requests
        JOIN student
        ON delete_requests.student_id = student.id
        ORDER BY delete_requests.id DESC
    """)

    requests = cursor.fetchall()

    formatted_requests = []

    for row in requests:

        request_date = row[4]
        try:
            dt = datetime.strptime(request_date, "%d-%m-%y %H:%M:%S")
            request_date = dt.strftime("%d-%m-%y %I:%M %p")
        except:
            pass

        formatted_requests.append((
            row[0],          # id
            row[1],          # student name
            row[2],          # register number
            row[3],          # department
            request_date,    # formatted date
            row[5]           # status
        ))

    conn.close()

    return render_template(
        "delete_requests.html",
        requests=formatted_requests
    )
    
@app.route('/approve_delete/<int:request_id>')
def approve_delete(request_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get("role") != "admin":
        return redirect(url_for("student_dashboard"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get request details
    cursor.execute("""
        SELECT user_id, status
        FROM delete_requests
        WHERE id=?
    """, (request_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return redirect(url_for("delete_requests"))

    user_id, status = row

    # Already processed
    if status != "Pending":
        conn.close()
        return redirect(url_for("delete_requests"))

    # Approve request
    cursor.execute("""
        UPDATE delete_requests
        SET status='Approved'
        WHERE id=?
    """, (request_id,))

    # Deactivate account
    cursor.execute("""
        UPDATE users
        SET status='Inactive'
        WHERE id=?
    """, (user_id,))

    conn.commit()
    conn.close()

    flash("Account deletion request approved.", "success")

    return redirect(url_for("delete_requests"))

@app.route('/reject_delete/<int:request_id>')
def reject_delete(request_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get("role") != "admin":
        return redirect(url_for('student_dashboard'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status
        FROM delete_requests
        WHERE id=?
    """, (request_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return redirect(url_for('delete_requests'))

    status = row[0]

    if status != "Pending":
        conn.close()
        return redirect(url_for('delete_requests'))

    cursor.execute("""
        UPDATE delete_requests
        SET status='Rejected'
        WHERE id=?
    """, (request_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('delete_requests'))


@app.route('/delete_account', methods=['POST'])
def delete_account():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return redirect(url_for('student_dashboard'))

    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Get all students
    cursor.execute("""
        SELECT id, name
        FROM student
    """)

    students = cursor.fetchall()

    for student_id, student_name in students:

        # Delete attendance
        cursor.execute("""
            DELETE FROM attendance
            WHERE student_id=? AND student_name=?
        """, (student_id, student_name))

        # Delete academic marks
        cursor.execute("""
            DELETE FROM academic_marks
            WHERE student_id=? AND student_name=?
        """, (student_id, student_name))
    
     # Delete semester results
        cursor.execute("""
            DELETE FROM semester_result
            WHERE student_id = ? AND student_name = ?
        """, (student_id, student_name))
    
    # Delete students of this admin only
    cursor.execute("""
        DELETE FROM student
        WHERE admin_id = ?
    """, (session['user_id'],))
        

    # Delete admin account
    cursor.execute("""
        DELETE FROM users
        WHERE id=?
    """, (session['user_id'],))

    conn.commit()
    conn.close()

    session.clear()

    return redirect(url_for('register'))

@app.route('/reset')
def reset():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Admin only
    if session.get('role') != 'admin':
        return redirect(url_for('student_dashboard'))

    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Get all students first
    cursor.execute("""
        SELECT id, name
        FROM student
    """)
    students = cursor.fetchall()

    # Delete attendance and marks
    for student_id, student_name in students:
        cursor.execute("DELETE FROM attendance WHERE student_id=? AND student_name=?", (student_id, student_name))
        cursor.execute("DELETE FROM academic_marks WHERE student_id=? AND student_name=?", (student_id, student_name))
        cursor.execute("DELETE FROM semester_result WHERE student_id=? AND student_name=?", (student_id, student_name))
        cursor.execute("DELETE FROM assignment_submission WHERE student_id=? AND student_name=?", (student_id, student_name))
        cursor.execute("DELETE FROM certificates WHERE student_id=? AND student_name=?", (student_id, student_name))
        cursor.execute("DELETE FROM student WHERE id=? AND name=?", (student_id, student_name))

    conn.commit()
    conn.close()

    return redirect(url_for('view_students'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
