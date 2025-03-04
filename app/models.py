from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime

# Association table for Teacher-Subject many-to-many relationship
class TeacherSubject(db.Model):
    __tablename__ = 'teacher_subject'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

    # Add index for performance on frequently queried fields
    __table_args__ = (
        db.Index('idx_teacher_subject_teacher_id', 'teacher_id'),
        db.Index('idx_teacher_subject_subject_id', 'subject_id'),
    )

# Association table for Student-Subject many-to-many relationship
student_subjects = db.Table('student_subject',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True),
    db.Index('idx_student_subject_student_id', 'student_id'),
    db.Index('idx_student_subject_subject_id', 'subject_id'),
)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    teacher = db.relationship('Teacher', back_populates='user', uselist=False)  # Use back_populates
    students = db.relationship('Student', back_populates='parent')  # Use back_populates
    managed_classes = db.relationship('SchoolClass', back_populates='class_teacher')  # Use back_populates

    @validates('role')
    def validate_role(self, key, role):
        valid_roles = ['admin', 'teacher', 'parent']
        if role not in valid_roles:
            raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")
        return role

# Teacher Model
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Many-to-Many Relationship with Subject
    subjects = db.relationship(
        'Subject', secondary='teacher_subject',
        back_populates='teaching_teachers'  # Use back_populates
    )
    user = db.relationship('User', back_populates='teacher')  # Add back_populates for user

    @validates('user_id')
    def validate_user_id(self, key, user_id):
        if not User.query.get(user_id):
            raise ValueError(f"Invalid user_id: {user_id} - No matching user exists")
        return user_id

    deleted_at = db.Column(db.DateTime, nullable=True)

# Student Model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    school_class_id = db.Column(db.Integer, db.ForeignKey('school_class.id'), nullable=False, index=True, server_default='1')
    admission_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    school_class = db.relationship('SchoolClass', back_populates='students')  # Use back_populates
    parent = db.relationship('User', back_populates='students')  # Use back_populates
    subjects = db.relationship('Subject', secondary='student_subject', back_populates='enrolled_students')  # Use back_populates
    results = db.relationship('Result', back_populates='student')  # Use back_populates
    welfare_reports = db.relationship('WelfareReport', back_populates='student')  # Use back_populates

    @validates('school_class_id')
    def validate_school_class_id(self, key, school_class_id):
        if not SchoolClass.query.get(school_class_id):
            raise ValueError(f"Invalid school_class_id: {school_class_id} - No matching class exists")
        return school_class_id

    @validates('parent_id')
    def validate_parent_id(self, key, parent_id):
        if not User.query.get(parent_id):
            raise ValueError(f"Invalid parent_id: {parent_id} - No matching user exists")
        return parent_id

# Form Model
class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    classes = db.relationship('SchoolClass', back_populates='form')  # Use back_populates
    exams = db.relationship('Exam', back_populates='form')  # Use back_populates

# School Class Model
class SchoolClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False, index=True)
    class_teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True, server_default=None)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    form = db.relationship('Form', back_populates='classes', foreign_keys='SchoolClass.form_id')  # Use back_populates
    class_teacher = db.relationship('User', back_populates='managed_classes', foreign_keys='SchoolClass.class_teacher_id')  # Use back_populates
    students = db.relationship('Student', back_populates='school_class')  # Use back_populates

    @validates('form_id')
    def validate_form_id(self, key, form_id):
        if not Form.query.get(form_id):
            raise ValueError(f"Invalid form_id: {form_id} - No matching form exists")
        return form_id

    @validates('class_teacher_id')
    def validate_class_teacher_id(self, key, class_teacher_id):
        if class_teacher_id and not User.query.get(class_teacher_id):
            raise ValueError(f"Invalid class_teacher_id: {class_teacher_id} - No matching user exists")
        return class_teacher_id

# Subject Model
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    results = db.relationship('Result', back_populates='subject')  # Use back_populates
    enrolled_students = db.relationship('Student', secondary='student_subject', back_populates='subjects')  # Use back_populates
    teaching_teachers = db.relationship('Teacher', secondary='teacher_subject', back_populates='subjects')  # Use back_populates

# Exam Model
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    term = db.Column(db.String(50), nullable=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    form = db.relationship('Form', back_populates='exams', foreign_keys='Exam.form_id')  # Use back_populates
    results = db.relationship('Result', back_populates='exam')  # Use back_populates

    @validates('form_id')
    def validate_form_id(self, key, form_id):
        if not Form.query.get(form_id):
            raise ValueError(f"Invalid form_id: {form_id} - No matching form exists")
        return form_id

# Result Model
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False, server_default='0.0')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    student = db.relationship('Student', back_populates='results')  # Use back_populates
    exam = db.relationship('Exam', back_populates='results')  # Use back_populates
    subject = db.relationship('Subject', back_populates='results')  # Use back_populates

    @validates('student_id')
    def validate_student_id(self, key, student_id):
        if not Student.query.get(student_id):
            raise ValueError(f"Invalid student_id: {student_id}")
        return student_id

    @validates('exam_id')
    def validate_exam_id(self, key, exam_id):
        if not Exam.query.get(exam_id):
            raise ValueError(f"Invalid exam_id: {exam_id}")
        return exam_id

    @validates('subject_id')
    def validate_subject_id(self, key, subject_id):
        if not Subject.query.get(subject_id):
            raise ValueError(f"Invalid subject_id: {subject_id}")
        return subject_id

    @validates('score')
    def validate_score(self, key, score):
        if not (0 <= score <= 100):
            raise ValueError(f"Invalid score: {score} - Must be between 0 and 100")
        return score

# Welfare Report Model
class WelfareReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    remarks = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    student = db.relationship('Student', back_populates='welfare_reports')  # Use back_populates

    @validates('student_id')
    def validate_student_id(self, key, student_id):
        if not Student.query.get(student_id):
            raise ValueError(f"Invalid student_id: {student_id}")
        return student_id