from flask import Flask, render_template, request, redirect,flash,url_for,session
import sqlite3,os
print("DATABASE PATH:",os.path.abspath("database.db"))
app = Flask(__name__)
app.secret_key = "student_management_secret"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            return render_template('register.html', message="Email already exists!",message_type="error")
        cursor.execute("INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)",(name, email, password, phone))
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
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email=? AND password=?',(email, password))
        users = cursor.fetchone()
        conn.close()
        if users:
            session['user_id']=users[0]
            return redirect(url_for('dashboard') )
        else:
            return render_template('login.html',message="Invalid Email or Password!",message_type="error")    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM student WHERE user_id=?",(user_id,))
    total_students = cursor.fetchone()[0] 
    cursor.execute("SELECT name, email,phone FROM users WHERE id = ?",(user_id,))
    user = cursor.fetchone()
    conn.close()
    if user is None:
        return redirect(url_for('login'))  
    return render_template('dashboard.html',user=user,total_students=total_students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    message = ""
    message_type = ""
    if request.method == 'POST':
        name = request.form['name']
        reg_number = request.form['reg_no']
        department = request.form['department']
        year = request.form['year']
        email = request.form['email']
        phone = request.form['phone']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM student WHERE reg_number=? AND user_id=?",(reg_number, session['user_id']))
        existing_reg = cursor.fetchone()
        cursor.execute("SELECT * FROM student WHERE email=? AND user_id=?",(email, session['user_id']))
        existing_email = cursor.fetchone()
        if existing_reg:
            message = "❌ Register Number already exists!"
            message_type = "error"
        elif existing_email:
            message = "❌ Email already exists!"
            message_type = "error"
        else:
            cursor.execute("""INSERT INTO student(name, reg_number, department, year, email, phone, user_id)VALUES (?, ?, ?, ?, ?, ?, ?)""", (name,reg_number,department,year,email,phone,session['user_id']))
            conn.commit()
            message = "✅ Student registered successfully!"
            message_type = "success"
        conn.close()
    return render_template('add_student.html',message=message,message_type=message_type)

@app.route('/view_students')
def view_students():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student WHERE user_id=?", (session['user_id'],))
    students = cursor.fetchall()
    conn.close()
    return render_template('view_students.html', students=students)

@app.route('/update_student/<int:id>', methods=['GET', 'POST'])
def update_student(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        reg_number = request.form['reg_number']
        department = request.form['department']
        year = request.form['year']
        email = request.form['email']
        phone = request.form['phone']
        cursor.execute('''UPDATE student SET name=?,reg_number=?,department=?,year=?,email=?,phone=? WHERE id=? AND user_id=?''', (name,reg_number,department,year,email,phone,id,session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('view_students'))
    cursor.execute("SELECT * FROM student WHERE id=? AND user_id=?",(id, session['user_id']))
    student = cursor.fetchone()
    conn.close()
    return render_template('update_student.html', student=student)

@app.route('/search_student', methods=['GET', 'POST'])
def search_student():
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    student = []
    message =""
    if request.method == 'POST':
        name = request.form['keyword']
        reg_number = request.form['register_number']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM student WHERE name=? AND reg_number=? AND user_id=?",(name, reg_number, session['user_id']))
        student = cursor.fetchall()
        conn.close()
        if len(student) == 0:
            message = "No student record found."
    return render_template('search_student.html',student=student,message=message)
    
@app.route('/delete_student/<int:id>')
def delete_student(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM student WHERE id=? AND user_id=?", (id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect('/view_students')

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    session.clear()
    return redirect(url_for('register'))

@app.route('/reset')
def reset():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # delete only this user's students
    cursor.execute("DELETE FROM student WHERE user_id=?", (user_id,))
    # OPTIONAL: reset auto-increment (SQLite only)
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='student'")
    conn.commit()
    conn.close()
    return redirect(url_for('view_students'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
