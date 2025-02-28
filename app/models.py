from datetime import datetime
from app import db

# Users Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)

# Students Table
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admission_number = db.Column(db.String(100), nullable=False, unique=True)  # Unique admission number
    parent = db.relationship('User', backref='students', foreign_keys=[parent_id])
    class_name = db.relationship('Class', backref='students', foreign_keys=[class_id])

# Classes Table
class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    class_teacher = db.relationship('User', backref='classes')

# Subjects Table
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    exam = db.relationship('Exam', backref='subjects')
    teacher_subjects = db.relationship('TeacherSubject', backref='subject_association', overlaps="teacher_subjects")

# Exams Table
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    term = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Results Table
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Welfare Reports Table
class WelfareReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    remarks = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Teacher Table (Add this to define the Teacher class)
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='teacher')
    subjects = db.relationship('Subject', secondary='teacher_subject', overlaps="teacher_subjects")

# Teacher-Subject Connector Table
class TeacherSubject(db.Model):
    __tablename__ = 'teacher_subject'

    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), primary_key=True)

    teacher = db.relationship('Teacher', backref=db.backref('teacher_subjects', lazy=True), overlaps="teacher_subjects")
    subject = db.relationship('Subject', backref=db.backref('teacher_subjects_association', lazy=True), overlaps="teacher_subjects")