from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from app.models import User, Student, SchoolClass, Subject, Exam, Result, WelfareReport, Teacher, Form

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_relationships = True
        include_fk = True

    teacher = fields.Nested('TeacherSchema', only=('id',), dump_only=True)
    students = fields.Nested('StudentSchema', many=True, only=('id', 'name'), dump_only=True)
    managed_classes = fields.Nested('SchoolClassSchema', many=True, only=('id', 'name'), dump_only=True)

class TeacherSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Teacher
        load_instance = True
        include_relationships = True
        include_fk = True

    user = fields.Nested('UserSchema', only=('id', 'name'), dump_only=True)
    subjects = fields.Nested('SubjectSchema', many=True, only=('id', 'name'), dump_only=True)

class StudentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        load_instance = True
        include_relationships = True
        include_fk = True

    school_class = fields.Nested('SchoolClassSchema', only=('id', 'name'), dump_only=True)
    school_class_id = fields.Integer(required=True)  # Allow passing class ID instead of full object

    parent = fields.Nested('UserSchema', only=('id', 'name'), dump_only=True)
    parent_id = fields.Integer(required=True)  # Allow passing parent ID

    subjects = fields.Nested('SubjectSchema', many=True, only=('id', 'name'), dump_only=True)
    results = fields.Nested('ResultSchema', many=True, dump_only=True)
    welfare_reports = fields.Nested('WelfareReportSchema', many=True, dump_only=True)

class FormSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Form
        load_instance = True
        include_relationships = True
        include_fk = True

    classes = fields.Nested('SchoolClassSchema', many=True, only=('id', 'name'), dump_only=True)
    exams = fields.Nested('ExamSchema', many=True, only=('id', 'name'), dump_only=True)

class SchoolClassSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SchoolClass
        load_instance = True
        include_relationships = True
        include_fk = True

    form = fields.Nested('FormSchema', only=('id', 'name'), dump_only=True)
    form_id = fields.Integer(required=True)  # Allow passing form ID

    class_teacher = fields.Nested('UserSchema', only=('id', 'name'), dump_only=True)
    class_teacher_id = fields.Integer(required=False)  # Optional class teacher assignment

    students = fields.Nested('StudentSchema', many=True, only=('id', 'name'), dump_only=True)

class SubjectSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Subject
        load_instance = True
        include_relationships = True
        include_fk = True

    results = fields.Nested('ResultSchema', many=True, dump_only=True)
    enrolled_students = fields.Nested('StudentSchema', many=True, only=('id', 'name'), dump_only=True)
    teaching_teachers = fields.Nested('TeacherSchema', many=True, only=('id', 'name'), dump_only=True)

class ExamSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Exam
        load_instance = True
        include_relationships = True
        include_fk = True

    form = fields.Nested('FormSchema', only=('id', 'name'), dump_only=True)
    form_id = fields.Integer(required=True)  # Allow passing form ID

    results = fields.Nested('ResultSchema', many=True, dump_only=True)

class ResultSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Result
        load_instance = True
        include_relationships = True
        include_fk = True

    student = fields.Nested('StudentSchema', only=('id', 'name'), dump_only=True)
    student_id = fields.Integer(required=True)  # Allow passing student ID

    exam = fields.Nested('ExamSchema', only=('id', 'name'), dump_only=True)
    exam_id = fields.Integer(required=True)  # Allow passing exam ID

    subject = fields.Nested('SubjectSchema', only=('id', 'name'), dump_only=True)
    subject_id = fields.Integer(required=True)  # Allow passing subject ID

class WelfareReportSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = WelfareReport
        load_instance = True
        include_relationships = True
        include_fk = True

    student = fields.Nested('StudentSchema', only=('id', 'name'), dump_only=True)
    student_id = fields.Integer(required=True)  # Allow passing student ID
