from app import ma
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import User, Student, SchoolClass, Subject, Exam, Result, WelfareReport

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_relationships = True
        load_instance = True

class StudentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        include_relationships = True
        load_instance = True

# ✅ Rename to SchoolClassSchema
class SchoolClassSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SchoolClass  # ✅ Updated reference

class SubjectSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Subject
        include_relationships = True
        load_instance = True

class ExamSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Exam
        include_relationships = True
        load_instance = True

class ResultSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Result
        include_relationships = True
        load_instance = True

class WelfareReportSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = WelfareReport
        include_relationships = True
        load_instance = True
