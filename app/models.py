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
    class_id = db.Column(db.Integer, db.ForeignKey('class.id', ondelete="CASCADE"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    admission_number = db.Column(db.String(100), nullable=False, unique=True)  

    parent = db.relationship('User', backref='students', foreign_keys=[parent_id])
    school_class = db.relationship('SchoolClass', backref='students', foreign_keys=[class_id])
    subjects = db.relationship('Subject', secondary='student_subject', back_populates='students')  # Use back_populates

# School Class Table (Renamed from Class)
class SchoolClass(db.Model):
    __tablename__ = 'class'  # Keep table name as "class"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_teacher_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="SET NULL"))
    class_teacher = db.relationship('User', backref='classes')

# Exams Table
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    term = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Subjects Table
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    students = db.relationship('Student', secondary='student_subject', back_populates='subjects')  # Use back_populates

# Many-to-Many Relationship for Exam-Subject
class ExamSubject(db.Model):
    __tablename__ = 'exam_subject'
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id', ondelete="CASCADE"), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete="CASCADE"), primary_key=True)

# Results Table
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete="CASCADE"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete="CASCADE"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id', ondelete="CASCADE"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # Add relationships
    subject = db.relationship('Subject', backref='results')  # Relationship to Subject
    student = db.relationship('Student', backref='results')  # Relationship to Student
    exam = db.relationship('Exam', backref='results')  # Relationship to Exam
    teacher = db.relationship('User', backref='results')  # Relationship to User (teacher)

# Welfare Reports Table
class WelfareReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete="CASCADE"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    remarks = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # New column for category
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Teacher Table
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    user = db.relationship('User', backref='teacher')

    subjects = db.relationship('Subject', secondary='teacher_subject', backref='teachers')

# Teacher-Subject Connector Table
class TeacherSubject(db.Model):
    __tablename__ = 'teacher_subject'
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id', ondelete="CASCADE"), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete="CASCADE"), primary_key=True)

# Many-to-Many Relationship for Student-Subject
class StudentSubject(db.Model):
    __tablename__ = 'student_subject'
    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete="CASCADE"), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete="CASCADE"), primary_key=True)