from flask import Blueprint, request, jsonify
from app import db, bcrypt
from app.models import User, Student, Class, Subject, Exam, Result, WelfareReport
from app.schemas import UserSchema, StudentSchema, ClassSchema, SubjectSchema, ExamSchema, ResultSchema, WelfareReportSchema

api_bp = Blueprint('api', __name__)

# User Routes

# Create User
@api_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password=hashed_password, role=data['role'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify(UserSchema().dump(new_user)), 201

# Get All Users
@api_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify(UserSchema(many=True).dump(users))

# Get User by Username
@api_bp.route('/users/search', methods=['GET'])
def search_user():
    username = request.args.get('username')
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify(UserSchema().dump(user))
    return jsonify({"message": "User not found"}), 404

# Update User
@api_bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)
    if user:
        data = request.get_json()
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8') if 'password' in data else user.password
        user.role = data.get('role', user.role)
        db.session.commit()
        return jsonify(UserSchema().dump(user))
    return jsonify({"message": "User not found"}), 404

# Delete User
@api_bp.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"})
    return jsonify({"message": "User not found"}), 404

# Student Routes

# Create Student
@api_bp.route('/students', methods=['POST'])
def create_student():
    data = request.get_json()
    new_student = Student(name=data['name'], class_id=data['class_id'], parent_id=data['parent_id'])
    db.session.add(new_student)
    db.session.commit()
    return jsonify(StudentSchema().dump(new_student)), 201

# Get All Students
@api_bp.route('/students', methods=['GET'])
def get_students():
    students = Student.query.all()
    return jsonify(StudentSchema(many=True).dump(students))

# Get Student by ID
@api_bp.route('/students/<int:id>', methods=['GET'])
def get_student_by_id(id):
    student = Student.query.get(id)
    if student:
        return jsonify(StudentSchema().dump(student))
    return jsonify({"message": "Student not found"}), 404

# Update Student
@api_bp.route('/students/<int:id>', methods=['PUT'])
def update_student(id):
    student = Student.query.get(id)
    if student:
        data = request.get_json()
        student.name = data.get('name', student.name)
        student.class_id = data.get('class_id', student.class_id)
        student.parent_id = data.get('parent_id', student.parent_id)
        db.session.commit()
        return jsonify(StudentSchema().dump(student))
    return jsonify({"message": "Student not found"}), 404

# Delete Student
@api_bp.route('/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    student = Student.query.get(id)
    if student:
        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Student deleted successfully"})
    return jsonify({"message": "Student not found"}), 404

# Class Routes

# Create Class
@api_bp.route('/classes', methods=['POST'])
def create_class():
    data = request.get_json()
    new_class = Class(name=data['name'], class_teacher_id=data['class_teacher_id'])
    db.session.add(new_class)
    db.session.commit()
    return jsonify(ClassSchema().dump(new_class)), 201

# Get All Classes
@api_bp.route('/classes', methods=['GET'])
def get_classes():
    classes = Class.query.all()
    return jsonify(ClassSchema(many=True).dump(classes))

# Get Class by ID
@api_bp.route('/classes/<int:id>', methods=['GET'])
def get_class_by_id(id):
    class_obj = Class.query.get(id)
    if class_obj:
        return jsonify(ClassSchema().dump(class_obj))
    return jsonify({"message": "Class not found"}), 404

# Update Class
@api_bp.route('/classes/<int:id>', methods=['PUT'])
def update_class(id):
    class_obj = Class.query.get(id)
    if class_obj:
        data = request.get_json()
        class_obj.name = data.get('name', class_obj.name)
        class_obj.class_teacher_id = data.get('class_teacher_id', class_obj.class_teacher_id)
        db.session.commit()
        return jsonify(ClassSchema().dump(class_obj))
    return jsonify({"message": "Class not found"}), 404

# Delete Class
@api_bp.route('/classes/<int:id>', methods=['DELETE'])
def delete_class(id):
    class_obj = Class.query.get(id)
    if class_obj:
        db.session.delete(class_obj)
        db.session.commit()
        return jsonify({"message": "Class deleted successfully"})
    return jsonify({"message": "Class not found"}), 404

# Subject Routes

# Create Subject
@api_bp.route('/subjects', methods=['POST'])
def create_subject():
    data = request.get_json()
    new_subject = Subject(subject_name=data['subject_name'], exam_id=data['exam_id'])
    db.session.add(new_subject)
    db.session.commit()
    return jsonify(SubjectSchema().dump(new_subject)), 201

# Get All Subjects
@api_bp.route('/subjects', methods=['GET'])
def get_subjects():
    subjects = Subject.query.all()
    return jsonify(SubjectSchema(many=True).dump(subjects))

# Get Subject by ID
@api_bp.route('/subjects/<int:id>', methods=['GET'])
def get_subject_by_id(id):
    subject = Subject.query.get(id)
    if subject:
        return jsonify(SubjectSchema().dump(subject))
    return jsonify({"message": "Subject not found"}), 404

# Update Subject
@api_bp.route('/subjects/<int:id>', methods=['PUT'])
def update_subject(id):
    subject = Subject.query.get(id)
    if subject:
        data = request.get_json()
        subject.subject_name = data.get('subject_name', subject.subject_name)
        subject.exam_id = data.get('exam_id', subject.exam_id)
        db.session.commit()
        return jsonify(SubjectSchema().dump(subject))
    return jsonify({"message": "Subject not found"}), 404

# Delete Subject
@api_bp.route('/subjects/<int:id>', methods=['DELETE'])
def delete_subject(id):
    subject = Subject.query.get(id)
    if subject:
        db.session.delete(subject)
        db.session.commit()
        return jsonify({"message": "Subject deleted successfully"})
    return jsonify({"message": "Subject not found"}), 404

# Exam Routes

# Create Exam
@api_bp.route('/exams', methods=['POST'])
def create_exam():
    data = request.get_json()
    new_exam = Exam(name=data['name'], term=data['term'])
    db.session.add(new_exam)
    db.session.commit()
    return jsonify(ExamSchema().dump(new_exam)), 201

# Get All Exams
@api_bp.route('/exams', methods=['GET'])
def get_exams():
    exams = Exam.query.all()
    return jsonify(ExamSchema(many=True).dump(exams))

# Get Exam by ID
@api_bp.route('/exams/<int:id>', methods=['GET'])
def get_exam_by_id(id):
    exam = Exam.query.get(id)
    if exam:
        return jsonify(ExamSchema().dump(exam))
    return jsonify({"message": "Exam not found"}), 404

# Update Exam
@api_bp.route('/exams/<int:id>', methods=['PUT'])
def update_exam(id):
    exam = Exam.query.get(id)
    if exam:
        data = request.get_json()
        exam.name = data.get('name', exam.name)
        exam.term = data.get('term', exam.term)
        db.session.commit()
        return jsonify(ExamSchema().dump(exam))
    return jsonify({"message": "Exam not found"}), 404

# Delete Exam
@api_bp.route('/exams/<int:id>', methods=['DELETE'])
def delete_exam(id):
    exam = Exam.query.get(id)
    if exam:
        db.session.delete(exam)
        db.session.commit()
        return jsonify({"message": "Exam deleted successfully"})
    return jsonify({"message": "Exam not found"}), 404

# Result Routes

# Create Result
@api_bp.route('/results', methods=['POST'])
def create_result():
    data = request.get_json()
    new_result = Result(student_id=data['student_id'], subject_id=data['subject_id'], 
                        exam_id=data['exam_id'], score=data['score'], teacher_id=data['teacher_id'])
    db.session.add(new_result)
    db.session.commit()
    return jsonify(ResultSchema().dump(new_result)), 201

# Get All Results
@api_bp.route('/results', methods=['GET'])
def get_results():
    results = Result.query.all()
    return jsonify(ResultSchema(many=True).dump(results))

# Get Result by ID
@api_bp.route('/results/<int:id>', methods=['GET'])
def get_result_by_id(id):
    result = Result.query.get(id)
    if result:
        return jsonify(ResultSchema().dump(result))
    return jsonify({"message": "Result not found"}), 404

# Update Result
@api_bp.route('/results/<int:id>', methods=['PUT'])
def update_result(id):
    result = Result.query.get(id)
    if result:
        data = request.get_json()
        result.score = data.get('score', result.score)
        db.session.commit()
        return jsonify(ResultSchema().dump(result))
    return jsonify({"message": "Result not found"}), 404

# Delete Result
@api_bp.route('/results/<int:id>', methods=['DELETE'])
def delete_result(id):
    result = Result.query.get(id)
    if result:
        db.session.delete(result)
        db.session.commit()
        return jsonify({"message": "Result deleted successfully"})
    return jsonify({"message": "Result not found"}), 404

# Welfare Report Routes

# Create Welfare Report
@api_bp.route('/welfare_reports', methods=['POST'])
def create_welfare_report():
    data = request.get_json()
    new_report = WelfareReport(student_id=data['student_id'], teacher_id=data['teacher_id'], remarks=data['remarks'])
    db.session.add(new_report)
    db.session.commit()
    return jsonify(WelfareReportSchema().dump(new_report)), 201

# Get All Welfare Reports
@api_bp.route('/welfare_reports', methods=['GET'])
def get_welfare_reports():
    reports = WelfareReport.query.all()
    return jsonify(WelfareReportSchema(many=True).dump(reports))

# Get Welfare Report by ID
@api_bp.route('/welfare_reports/<int:id>', methods=['GET'])
def get_welfare_report_by_id(id):
    report = WelfareReport.query.get(id)
    if report:
        return jsonify(WelfareReportSchema().dump(report))
    return jsonify({"message": "Welfare Report not found"}), 404

# Update Welfare Report
@api_bp.route('/welfare_reports/<int:id>', methods=['PUT'])
def update_welfare_report(id):
    report = WelfareReport.query.get(id)
    if report:
        data = request.get_json()
        report.remarks = data.get('remarks', report.remarks)
        db.session.commit()
        return jsonify(WelfareReportSchema().dump(report))
    return jsonify({"message": "Welfare Report not found"}), 404

# Delete Welfare Report
@api_bp.route('/welfare_reports/<int:id>', methods=['DELETE'])
def delete_welfare_report(id):
    report = WelfareReport.query.get(id)
    if report:
        db.session.delete(report)
        db.session.commit()
        return jsonify({"message": "Welfare Report deleted successfully"})
    return jsonify({"message": "Welfare Report not found"}), 404