from app import ma
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import User, Student, Class, Subject, Exam, Result, WelfareReport

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User

class StudentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Student

class ClassSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Class

class SubjectSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Subject

class ExamSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Exam

class ResultSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Result

class WelfareReportSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = WelfareReport
