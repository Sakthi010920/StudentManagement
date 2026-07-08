# 🎓 Student Record Management System

A **Flask-based Student Record Management System** designed to simplify academic administration by providing an integrated platform for managing student information, attendance, academic records, assignments, and user accounts. The system supports both **Admin** and **Student** roles with secure authentication and an easy-to-use interface.

---

## 📌 Features

### 👨‍💼 Admin Module

* Secure Admin Login
* Dashboard with statistics
* Add, Update, View, Search and Delete Students
* Manage Student Attendance
* View Attendance Summary
* Add Academic Marks
* Manage Internal 1, Internal 2 and Semester Exams
* Manage Assignments
* Upload Assignment Files
* View Assignment Submissions
* Delete Student Accounts
* Reset Student Records

### 👨‍🎓 Student Module

* Secure Student Login
* Student Dashboard
* View Personal Profile
* View Attendance Percentage
* View Academic Marks
* Download Assignments
* Upload Assignment Submissions
* Delete Personal Account

---

## 📚 Academic Management

The Academic Module allows administrators to maintain semester-wise academic records.

Supported Exam Types:

* Internal Assessment 1
* Internal Assessment 2
* Semester Examination

Features:

* Semester Selection
* Subject-wise Marks Entry
* Grade/Result Storage
* View Academic Performance
* Student-wise Academic History

---

## 📝 Assignment Management

### Admin

* Create Assignments
* Upload Assignment Files
* Set Assignment Title
* Set Subject
* Set Due Date
* View Student Submissions

### Student

* View Available Assignments
* Download Assignment Files
* Upload Assignment Solutions
* Submit Before Due Date

---

## 📅 Attendance Management

* Mark Student Attendance
* Present / Absent Status
* Daily Attendance Records
* Attendance Summary
* Attendance Percentage

---

## 👥 Student Management

* Add Student
* Update Student Information
* Search Student
* View Student Details
* Delete Student
* User-wise Student Records

---

## 🔐 Authentication

* User Registration
* Secure Login
* Session Management
* Role-Based Access
* Logout Functionality

---

## 🛠 Technologies Used

### Backend

* Python
* Flask
* SQLite3

### Frontend

* HTML5
* CSS3
* JavaScript

### Database

* SQLite

### Tools

* Git
* GitHub
* VS Code
* Git Bash

---

## 📁 Project Structure

```
StudentManagement/
│
├── app.py
├── database.py
├── update_database.py
├── check_database.py
├── requirements.txt
├── README.md
├── database.db
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── student_dashboard.html
│   ├── add_student.html
│   ├── view_students.html
│   ├── search_student.html
│   ├── update_student.html
│   ├── add_marks.html
│   ├── view_marks.html
│   ├── view_academics.html
│   ├── manage_assignments.html
│   ├── assignment_submissions.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/
│       └── assignments/
│
└── database.db
```

---

## 💾 Installation

### Clone the Repository

```bash
git clone https://github.com/Sakthi010920/StudentManagement.git
```

### Navigate to Project

```bash
cd StudentManagement
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Initialize Database

```bash
python database.py
```

### Run the Application

```bash
python app.py
```

Open your browser and visit:

```
http://127.0.0.1:5000
```

---

## 📊 Modules Included

* User Authentication
* Dashboard
* Student Management
* Attendance Management
* Academic Records
* Marks Management
* Assignment Management
* Assignment Submission
* Student Dashboard
* Search Student
* Account Management

---

## 🎯 Project Objectives

* Digitize student record management.
* Reduce paperwork.
* Improve academic record maintenance.
* Simplify attendance tracking.
* Manage assignments efficiently.
* Provide role-based access.
* Ensure secure data storage.

---

## 🔒 Security Features

* Session-Based Authentication
* Role-Based Authorization
* User-Specific Data Access
* SQLite Database Protection
* Secure Login Validation

---

## 🚀 Future Enhancements

* Email Notifications
* Password Encryption
* OTP Login
* PDF Report Generation
* Excel Export
* QR Code Attendance
* SMS Notifications
* Cloud Database (MySQL)
* REST API Integration
* Mobile Application

---

## 👨‍💻 Developer

**Sakthivel S**

B.Tech Information Technology

V.S.B. Engineering College

---

## ⭐ If you like this project

Please consider giving this repository a ⭐ on GitHub.
