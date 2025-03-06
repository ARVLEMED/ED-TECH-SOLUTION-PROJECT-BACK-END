from app import db
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship, validates
from datetime import datetime

# Association table for Teacher-Subject many-to-many relationship
class TeacherSubject(db.Model):
    __tablename__ = 'teacher_subjects'  # Pluralized for consistency
    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False)  # Updated to 'teachers.id'
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)  # Updated to 'subjects.id'
    deleted_at = Column(DateTime, nullable=True)  # Added for soft deletes

    # Add index for performance on frequently queried fields
    __table_args__ = (
        db.Index('idx_teacher_subject_teacher_id', 'teacher_id'),
        db.Index('idx_teacher_subject_subject_id', 'subject_id'),
    )

# Association table for Student-Subject many-to-many relationship
student_subjects = db.Table('student_subjects',  # Pluralized for consistency
    Column('student_id', Integer, ForeignKey('students.id'), primary_key=True),  # Updated to 'students.id'
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True),  # Updated to 'subjects.id'
    db.Index('idx_student_subject_student_id', 'student_id'),
    db.Index('idx_student_subject_subject_id', 'subject_id'),
)

# User Model
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    teacher = relationship('Teacher', back_populates='user', uselist=False)
    students = relationship('Student', back_populates='parent')
    managed_classes = relationship('SchoolClass', back_populates='class_teacher')

    @validates('role')
    def validate_role(self, key, role):
        valid_roles = ['admin', 'teacher', 'parent']
        if role not in valid_roles:
            raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")
        return role

# Teacher Model
class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Many-to-Many Relationship with Subject
    subjects = relationship(
        'Subject', secondary='teacher_subjects',  # Updated to plural
        back_populates='teaching_teachers'
    )
    user = relationship('User', back_populates='teacher')
    results = relationship('Result', back_populates='teacher')  # Add this line

    @validates('user_id')
    def validate_user_id(self, key, user_id):
        if not User.query.get(user_id):
            raise ValueError(f"Invalid user_id: {user_id} - No matching user exists")
        return user_id

# Student Model
class Student(db.Model):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    school_class_id = Column(Integer, ForeignKey('school_classes.id'), nullable=False, index=True, server_default='1')  # Updated to 'school_classes.id'
    admission_number = Column(String(50), unique=True, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    school_class = relationship('SchoolClass', back_populates='students')
    parent = relationship('User', back_populates='students')
    subjects = relationship('Subject', secondary='student_subjects', back_populates='enrolled_students')  # Updated to plural
    results = relationship('Result', back_populates='student')
    welfare_reports = relationship('WelfareReport', back_populates='student')

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
    __tablename__ = 'forms'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String(50), unique=True, nullable=False, index=True)
    deleted_at = Column(db.DateTime, nullable=True)
    
    classes = db.relationship('SchoolClass', back_populates='form')
    exams = db.relationship('Exam', back_populates='form')

# School Class Model
class SchoolClass(db.Model):
    __tablename__ = 'school_classes'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String(100), unique=True, nullable=False, index=True)
    form_id = Column(db.Integer, ForeignKey('forms.id'), nullable=False, index=True)  # Updated to 'forms.id'
    class_teacher_id = Column(db.Integer, ForeignKey('users.id'), nullable=True, index=True, server_default=None)
    deleted_at = Column(db.DateTime, nullable=True)
    
    form = db.relationship('Form', back_populates='classes', foreign_keys=[form_id])
    class_teacher = relationship('User', back_populates='managed_classes', foreign_keys='SchoolClass.class_teacher_id')
    students = relationship('Student', back_populates='school_class')

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
    __tablename__ = 'subjects'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String(100), unique=True, nullable=False, index=True)
    deleted_at = Column(db.DateTime, nullable=True)
    
    results = relationship('Result', back_populates='subject')
    enrolled_students = relationship('Student', secondary='student_subjects', back_populates='subjects')  # Updated to plural
    teaching_teachers = relationship('Teacher', secondary='teacher_subjects', back_populates='subjects')  # Updated to plural

# Exam Model
class Exam(db.Model):
    __tablename__ = 'exams'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    term = Column(String(50), nullable=True)
    form_id = Column(Integer, ForeignKey('forms.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    form = relationship('Form', back_populates='exams', foreign_keys=[form_id])
    results = relationship('Result', back_populates='exam')

    @validates('form_id')
    def validate_form_id(self, key, form_id):
        if not Form.query.get(form_id):
            raise ValueError(f"Invalid form_id: {form_id} - No matching form exists")
        return form_id

# In app/models.py
class Result(db.Model):
    __tablename__ = 'results'
    id = Column(db.Integer, primary_key=True)
    student_id = Column(db.Integer, ForeignKey('students.id'), nullable=False, index=True)
    exam_id = Column(db.Integer, ForeignKey('exams.id'), nullable=False, index=True)
    subject_id = Column(db.Integer, ForeignKey('subjects.id'), nullable=False, index=True)
    teacher_id = Column(db.Integer, ForeignKey('teachers.id'), nullable=False, index=True)  # New column
    score = Column(Float, nullable=False, server_default='0.0')
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    student = relationship('Student', back_populates='results')
    exam = relationship('Exam', back_populates='results')
    subject = relationship('Subject', back_populates='results')
    teacher = relationship('Teacher', back_populates='results')  # Optional relationship

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

    @validates('teacher_id')
    def validate_teacher_id(self, key, teacher_id):
        if not Teacher.query.get(teacher_id):
            raise ValueError(f"Invalid teacher_id: {teacher_id}")
        return teacher_id

    @validates('score')
    def validate_score(self, key, score):
        if not (0 <= score <= 100):
            raise ValueError(f"Invalid score: {score} - Must be between 0 and 100")
        return score
# Welfare Report Model
class WelfareReport(db.Model):
    __tablename__ = 'welfare_reports'
    id = Column(db.Integer, primary_key=True)
    student_id = Column(db.Integer, ForeignKey('students.id'), nullable=False, index=True)  # Updated to 'students.id'
    category = Column(db.String(50), nullable=False)
    remarks = Column(db.Text, nullable=False)
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(db.DateTime, nullable=True)
    
    student = relationship('Student', back_populates='welfare_reports')

    @validates('student_id')
    def validate_student_id(self, key, student_id):
        if not Student.query.get(student_id):
            raise ValueError(f"Invalid student_id: {student_id}")
        return student_id