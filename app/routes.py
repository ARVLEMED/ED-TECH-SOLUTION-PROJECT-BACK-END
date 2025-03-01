from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from datetime import datetime
from app import db
from app.models import User, Student, SchoolClass, Subject, Exam, Result, WelfareReport, Teacher
from app.schemas import UserSchema, StudentSchema, SchoolClassSchema, SubjectSchema, ExamSchema, ResultSchema, WelfareReportSchema

api_bp = Blueprint('api', __name__)
bcrypt = Bcrypt()

# User Routes

# Create User
@api_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data or 'password' not in data or 'role' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], email=data['email'], password=hashed_password, role=data['role'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify(UserSchema().dump(new_user)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create user", "error": str(e)}), 500

# Get All Users
@api_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify(UserSchema(many=True).dump(users))

# Get User by Username
@api_bp.route('/users/search', methods=['GET'])
def search_user():
    username = request.args.get('username')
    if not username:
        return jsonify({"message": "Username is required"}), 400

    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify(UserSchema().dump(user))
    return jsonify({"message": "User not found"}), 404

# Update User
@api_bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    try:
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        if 'password' in data:
            user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user.role = data.get('role', user.role)
        db.session.commit()
        return jsonify(UserSchema().dump(user))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update user", "error": str(e)}), 500

# Delete User
@api_bp.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete user", "error": str(e)}), 500

# Student Routes

# Create Student
@api_bp.route('/students', methods=['POST'])
def create_student():
    data = request.get_json()
    if not data or 'name' not in data or 'class_id' not in data or 'parent_id' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        new_student = Student(name=data['name'], class_id=data['class_id'], parent_id=data['parent_id'])
        db.session.add(new_student)
        db.session.commit()
        return jsonify(StudentSchema().dump(new_student)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create student", "error": str(e)}), 500

# Get All Students
@api_bp.route('/students', methods=['GET'])
def get_students():
    students = Student.query.all()
    students_data = []
    for student in students:
        student_data = {
            "id": student.id,
            "name": student.name,
            "admission_number": student.admission_number,
            "class_id": student.class_id,
            "class_name": student.school_class.name,  # Use the relationship to get the class name
            "subjects": [subject.subject_name for subject in student.subjects]  # Use the relationship to get subject names
        }
        students_data.append(student_data)
    return jsonify(students_data)

# Get Student by ID
@api_bp.route('/students/<int:id>', methods=['GET'])
def get_student_by_id(id):
    student = Student.query.get(id)
    if student:
        student_data = {
            "id": student.id,
            "name": student.name,
            "admission_number": student.admission_number,
            "class_id": student.class_id,
            "class_name": student.school_class.name,  # Use the relationship to get the class name
            "subjects": [subject.subject_name for subject in student.subjects]  # Use the relationship to get subject names
        }
        return jsonify(student_data)
    return jsonify({"message": "Student not found"}), 404

# Get Subjects for a Specific Student
@api_bp.route('/students/<int:student_id>/subjects', methods=['GET'])
def get_student_subjects(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    subjects = [{"id": subject.id, "name": subject.subject_name} for subject in student.subjects]
    return jsonify(subjects), 200

# Update Student
@api_bp.route('/students/<int:id>', methods=['PUT'])
def update_student(id):
    student = Student.query.get(id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    try:
        student.name = data.get('name', student.name)
        student.class_id = data.get('class_id', student.class_id)
        student.parent_id = data.get('parent_id', student.parent_id)
        db.session.commit()
        return jsonify(StudentSchema().dump(student))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update student", "error": str(e)}), 500

# Delete Student
@api_bp.route('/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    student = Student.query.get(id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    try:
        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Student deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete student", "error": str(e)}), 500

# Class Routes

# Create Class
@api_bp.route('/classes', methods=['POST'])
def create_class():
    data = request.get_json()
    if not data or 'name' not in data or 'teacher_name' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    teacher = User.query.filter_by(username=data['teacher_name'], role='teacher').first()
    if not teacher:
        return jsonify({"message": "Teacher not found"}), 404

    try:
        new_class = SchoolClass(name=data['name'], class_teacher_id=teacher.id)
        db.session.add(new_class)
        db.session.commit()
        return jsonify(SchoolClassSchema().dump(new_class)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create class", "error": str(e)}), 500

# Get All Classes
@api_bp.route('/classes', methods=['GET'])
def get_classes():
    classes = SchoolClass.query.all()
    return jsonify(SchoolClassSchema(many=True).dump(classes))

# Get Class by ID
@api_bp.route('/classes/<int:id>', methods=['GET'])
def get_class_by_id(id):
    class_obj = SchoolClass.query.get(id)
    if class_obj:
        return jsonify(SchoolClassSchema().dump(class_obj))
    return jsonify({"message": "Class not found"}), 404

# Update Class
@api_bp.route('/classes/<int:id>', methods=['PUT'])
def update_class(id):
    class_obj = SchoolClass.query.get(id)
    if not class_obj:
        return jsonify({"message": "Class not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    try:
        if 'teacher_name' in data:
            teacher = User.query.filter_by(username=data['teacher_name'], role='teacher').first()
            if not teacher:
                return jsonify({"message": "Teacher not found"}), 404
            class_obj.class_teacher_id = teacher.id

        class_obj.name = data.get('name', class_obj.name)
        db.session.commit()
        return jsonify(SchoolClassSchema().dump(class_obj))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update class", "error": str(e)}), 500

# Delete Class
@api_bp.route('/classes/<int:id>', methods=['DELETE'])
def delete_class(id):
    class_obj = SchoolClass.query.get(id)
    if not class_obj:
        return jsonify({"message": "Class not found"}), 404

    try:
        # Update students associated with this class
        students = Student.query.filter_by(class_id=id).all()
        for student in students:
            student.class_id = None  # Or assign to another valid class ID
            db.session.add(student)

        db.session.delete(class_obj)
        db.session.commit()
        return jsonify({"message": "Class deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete class", "error": str(e)}), 500

# Subject Routes

# Create Subject
@api_bp.route('/subjects', methods=['POST'])
def create_subject():
    data = request.get_json()
    if not data or 'subject_name' not in data or 'exam_id' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        new_subject = Subject(subject_name=data['subject_name'], exam_id=data['exam_id'])
        db.session.add(new_subject)
        db.session.commit()
        return jsonify(SubjectSchema().dump(new_subject)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create subject", "error": str(e)}), 500

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
    if not subject:
        return jsonify({"message": "Subject not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    try:
        subject.subject_name = data.get('subject_name', subject.subject_name)
        subject.exam_id = data.get('exam_id', subject.exam_id)
        db.session.commit()
        return jsonify(SubjectSchema().dump(subject))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update subject", "error": str(e)}), 500

# Delete Subject
@api_bp.route('/subjects/<int:id>', methods=['DELETE'])
def delete_subject(id):
    subject = Subject.query.get(id)
    if not subject:
        return jsonify({"message": "Subject not found"}), 404

    try:
        db.session.delete(subject)
        db.session.commit()
        return jsonify({"message": "Subject deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete subject", "error": str(e)}), 500

# Exam Routes

# Create Exam
@api_bp.route('/exams', methods=['POST'])
def create_exam():
    data = request.get_json()
    if not data or 'name' not in data or 'term' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        new_exam = Exam(name=data['name'], term=data['term'])
        db.session.add(new_exam)
        db.session.commit()
        return jsonify(ExamSchema().dump(new_exam)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create exam", "error": str(e)}), 500

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
    if not exam:
        return jsonify({"message": "Exam not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    try:
        exam.name = data.get('name', exam.name)
        exam.term = data.get('term', exam.term)
        db.session.commit()
        return jsonify(ExamSchema().dump(exam))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update exam", "error": str(e)}), 500

# Delete Exam
@api_bp.route('/exams/<int:id>', methods=['DELETE'])
def delete_exam(id):
    exam = Exam.query.get(id)
    if not exam:
        return jsonify({"message": "Exam not found"}), 404

    try:
        db.session.delete(exam)
        db.session.commit()
        return jsonify({"message": "Exam deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete exam", "error": str(e)}), 500

# Result Routes

# Create Result
@api_bp.route('/results', methods=['POST'])
def create_result():
    data = request.get_json()
    if not data or 'student_id' not in data or 'subject_id' not in data or 'exam_id' not in data or 'score' not in data or 'teacher_id' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        new_result = Result(
            student_id=data['student_id'],
            subject_id=data['subject_id'],
            exam_id=data['exam_id'],
            score=data['score'],
            teacher_id=data['teacher_id']
        )
        db.session.add(new_result)
        db.session.commit()
        return jsonify(ResultSchema().dump(new_result)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create result", "error": str(e)}), 500

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

# Get Results for a Specific Student
@api_bp.route('/students/<int:student_id>/results', methods=['GET'])
def get_results_for_student(student_id):
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({"message": "Student not found"}), 404

        results = Result.query.filter_by(student_id=student_id).all()
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.id,
                "student_id": result.student_id,
                "subject_id": result.subject_id,
                "subject_name": result.subject.subject_name,  # Use the relationship to get subject name
                "exam_id": result.exam_id,
                "exam_name": result.exam.name,  # Use the relationship to get exam name
                "score": result.score,
                "teacher_id": result.teacher_id,
                "date": result.date.isoformat()  # Convert datetime to string
            })

        return jsonify(formatted_results), 200
    except Exception as e:
        return jsonify({"message": "Failed to fetch results", "error": str(e)}), 500

# Update Result
@api_bp.route('/results/<int:id>', methods=['PUT'])
def update_result(id):
    result = Result.query.get(id)
    if not result:
        return jsonify({"message": "Result not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    try:
        result.score = data.get('score', result.score)
        db.session.commit()
        return jsonify(ResultSchema().dump(result))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update result", "error": str(e)}), 500

# Delete Result
@api_bp.route('/results/<int:id>', methods=['DELETE'])
def delete_result(id):
    result = Result.query.get(id)
    if not result:
        return jsonify({"message": "Result not found"}), 404

    try:
        db.session.delete(result)
        db.session.commit()
        return jsonify({"message": "Result deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete result", "error": str(e)}), 500

# Welfare Report Routes

# Create Welfare Report
@api_bp.route('/welfare_reports', methods=['POST'])
def create_welfare_report():
    data = request.get_json()
    if not data or 'student_id' not in data or 'teacher_id' not in data or 'remarks' not in data or 'category' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        new_report = WelfareReport(
            student_id=data['student_id'],
            teacher_id=data['teacher_id'],
            remarks=data['remarks'],
            category=data['category']
        )
        db.session.add(new_report)
        db.session.commit()
        return jsonify(WelfareReportSchema().dump(new_report)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create welfare report", "error": str(e)}), 500

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

# Get Welfare Reports for a Specific Student
@api_bp.route('/students/<int:student_id>/welfare_reports', methods=['GET'])
def get_welfare_reports_for_student(student_id):
    category = request.args.get('category')  # Optional filter by category
    query = WelfareReport.query.filter_by(student_id=student_id)
    if category:
        if category not in ['Health', 'Discipline', 'Academic']:
            return jsonify({"message": "Invalid category"}), 400
        query = query.filter_by(category=category)
    reports = query.all()
    return jsonify(WelfareReportSchema(many=True).dump(reports))

# Update Welfare Report
@api_bp.route('/welfare_reports/<int:id>', methods=['PUT'])
def update_welfare_report(id):
    report = WelfareReport.query.get(id)
    if not report:
        return jsonify({"message": "Welfare Report not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    try:
        if 'remarks' in data:
            report.remarks = data['remarks']
        if 'category' in data:
            if data['category'] not in ['Health', 'Discipline', 'Academic']:
                return jsonify({"message": "Invalid category"}), 400
            report.category = data['category']
        db.session.commit()
        return jsonify(WelfareReportSchema().dump(report))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update welfare report", "error": str(e)}), 500

# Delete Welfare Report
@api_bp.route('/welfare_reports/<int:id>', methods=['DELETE'])
def delete_welfare_report(id):
    report = WelfareReport.query.get(id)
    if not report:
        return jsonify({"message": "Welfare Report not found"}), 404

    try:
        db.session.delete(report)
        db.session.commit()
        return jsonify({"message": "Welfare Report deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete welfare report", "error": str(e)}), 500

# Teacher Routes

# Get All Teachers
@api_bp.route('/teachers', methods=['GET'])
def get_teachers():
    teachers = User.query.filter_by(role='teacher').all()
    return jsonify(UserSchema(many=True).dump(teachers))

# Get Teacher by ID
@api_bp.route('/teachers/<int:id>', methods=['GET'])
def get_teacher_by_id(id):
    teacher = User.query.filter_by(id=id, role='teacher').first()
    if teacher:
        return jsonify(UserSchema().dump(teacher))
    return jsonify({"message": "Teacher not found"}), 404

# Create Teacher
@api_bp.route('/teachers', methods=['POST'])
def create_teacher():
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=hashed_password,
            role='teacher'
        )
        db.session.add(new_user)
        db.session.commit()

        # Create a corresponding Teacher entry
        new_teacher = Teacher(user_id=new_user.id)
        db.session.add(new_teacher)
        db.session.commit()

        return jsonify(UserSchema().dump(new_user)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create teacher", "error": str(e)}), 500

# Update Teacher
@api_bp.route('/teachers/<int:id>', methods=['PUT'])
def update_teacher(id):
    teacher = User.query.filter_by(id=id, role='teacher').first()
    if not teacher:
        return jsonify({"message": "Teacher not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    try:
        teacher.username = data.get('username', teacher.username)
        teacher.email = data.get('email', teacher.email)
        if 'password' in data:
            teacher.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        db.session.commit()
        return jsonify(UserSchema().dump(teacher))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update teacher", "error": str(e)}), 500

# Delete Teacher
@api_bp.route('/teachers/<int:id>', methods=['DELETE'])
def delete_teacher(id):
    teacher = User.query.filter_by(id=id, role='teacher').first()
    if not teacher:
        return jsonify({"message": "Teacher not found"}), 404

    try:
        # Delete the corresponding Teacher entry
        teacher_entry = Teacher.query.filter_by(user_id=id).first()
        if teacher_entry:
            db.session.delete(teacher_entry)

        db.session.delete(teacher)
        db.session.commit()
        return jsonify({"message": "Teacher deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete teacher", "error": str(e)}), 500