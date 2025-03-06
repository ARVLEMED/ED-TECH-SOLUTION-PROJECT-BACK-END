from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from app.models import Subject, Teacher, User, Student, Result, WelfareReport, SchoolClass, Form, Exam  # Ensure all models are imported

# Define schemas in a logical order to avoid forward references
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_relationships = True
        include_fk = True

    teacher = fields.Nested('TeacherSchema', dump_only=True, only=['id'])  # Limit to prevent recursion
    students = fields.Nested('StudentSchema', many=True, dump_only=True, only=['name'])  # Limit to student names
    managed_classes = fields.Nested('SchoolClassSchema', many=True, dump_only=True, only=['name'])  # Limit to class names

class TeacherSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Teacher
        load_instance = True
        include_relationships = True
        include_fk = True

    user = fields.Nested(UserSchema, dump_only=True, only=['username', 'email'])  # Limit to username and email
    subjects = fields.Nested('SubjectSchema', many=True, dump_only=True, only=['name'])  # Only include subject names

class SubjectSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Subject
        load_instance = True
        include_relationships = True
        include_fk = True

    results = fields.Nested('ResultSchema', many=True, dump_only=True, only=['id', 'score'])  # Limit fields
    enrolled_students = fields.Nested('StudentSchema', many=True, dump_only=True, only=['name'])  # Limit to name
    teaching_teachers = fields.Nested(TeacherSchema, many=True, dump_only=True, only=['id', 'user'])  # Limit fields

class ResultSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Result
        load_instance = True
        include_relationships = True
        include_fk = True

    student = fields.Nested('StudentSchema', dump_only=True, only=['name'])  # Limit to student name
    subject = fields.Nested('SubjectSchema', dump_only=True, only=['name'])  # Limit to subject name
    exam = fields.Nested('ExamSchema', dump_only=True, only=['name'])  # Limit to exam name

class StudentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        load_instance = True
        include_relationships = True
        include_fk = True

    subjects = fields.Nested(SubjectSchema, many=True, dump_only=True, only=['name'])  # Only include subject names
    results = fields.Nested(ResultSchema, many=True, dump_only=True, only=['id', 'score', 'exam'])  # Limit fields
    welfare_reports = fields.Nested('WelfareReportSchema', many=True, dump_only=True, only=['category', 'remarks'])  # Limit fields
    school_class = fields.Nested('SchoolClassSchema', dump_only=True, only=['name'])  # Limit to class name
    parent = fields.Nested(UserSchema, dump_only=True, only=['email'])  # Limit to email

class SchoolClassSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SchoolClass  # Now properly defined
        load_instance = True
        include_relationships = True
        include_fk = True

    form = fields.Nested('FormSchema', dump_only=True, only=['name'])  # Limit to form name
    class_teacher = fields.Nested(UserSchema, dump_only=True, only=['username'])  # Limit to teacher username (via User)
    students = fields.Nested(StudentSchema, many=True, dump_only=True, only=['name'])  # Limit to student names

class FormSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Form
        load_instance = True
        include_relationships = True
        include_fk = True

    school_classes = fields.Nested(SchoolClassSchema, many=True, dump_only=True, only=['name'])  # Limit to class names
    exams = fields.Nested('ExamSchema', many=True, dump_only=True, only=['name'])  # Limit to exam names

class ExamSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Exam
        load_instance = True
        include_relationships = True
        include_fk = True

    form = fields.Nested(FormSchema, dump_only=True, only=['name'])  # Limit to form name
    results = fields.Nested(ResultSchema, many=True, dump_only=True, only=['id', 'score'])  # Limit fields

class WelfareReportSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = WelfareReport
        load_instance = True
        include_relationships = True
        include_fk = True

    student = fields.Nested(StudentSchema, dump_only=True, only=['name', 'school_class'])  # Include school_class