from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from datetime import datetime
from app import db
from app.models import User, Student, SchoolClass, Subject, Exam, Result, WelfareReport, Teacher, Form, TeacherSubject
from app.schemas import UserSchema, StudentSchema, SchoolClassSchema, SubjectSchema, ExamSchema, ResultSchema, WelfareReportSchema, FormSchema
from sqlalchemy.orm import joinedload

api_bp = Blueprint('api', __name__)
bcrypt = Bcrypt()

# --- Helper Function for Soft Deletes ---
def is_soft_deleted(model_instance):
    return getattr(model_instance, 'deleted_at', None) is not None

# --- User Routes ---

@api_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data or 'password' not in data or 'role' not in data:
        return jsonify({"message": "Missing required fields"}), 400
    try:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], email=data['email'], password=hashed_password, role=data['role'], deleted_at=None)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(UserSchema().dump(new_user)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create user", "error": str(e)}), 500

@api_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.filter(User.deleted_at.is_(None)).all()  # Exclude soft-deleted users
    return jsonify(UserSchema(many=True).dump(users))

@api_bp.route('/user/roles', methods=['GET'])
def get_user_roles():
    user_id = request.args.get('user_id')
    user = User.query.filter_by(id=user_id, deleted_at=None).first()
    if user:
        roles = []
        if SchoolClass.query.filter_by(class_teacher_id=user_id, deleted_at=None).first():
            roles.append("class_teacher")
        if Teacher.query.filter_by(user_id=user_id, deleted_at=None).first():
            roles.append("subject_teacher")
        return jsonify({"roles": roles}), 200
    return jsonify({"error": "User not found"}), 404

@api_bp.route('/users/by-role', methods=['GET'])
def get_users_by_role():
    role = request.args.get('role')
    if not role:
        return jsonify({"message": "Role parameter is required"}), 400
    users = User.query.filter_by(role=role, deleted_at=None).all()  # Exclude soft-deleted users
    return jsonify(UserSchema(many=True).dump(users))

@api_bp.route('/users/search', methods=['GET'])
def search_user():
    username = request.args.get('username')
    if not username:
        return jsonify({"message": "Username is required"}), 400
    user = User.query.filter_by(username=username, deleted_at=None).first()  # Exclude soft-deleted users
    if user:
        return jsonify(UserSchema().dump(user))
    return jsonify({"message": "User not found"}), 404

@api_bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.filter_by(id=id, deleted_at=None).first()
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

@api_bp.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.filter_by(id=id, deleted_at=None).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    try:
        # Soft delete instead of hard delete
        user.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "User soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete user", "error": str(e)}), 500

# --- Student Routes ---

@api_bp.route('/students', methods=['POST'])
def create_student():
    data = request.get_json()
    required_fields = ['name', 'school_class_id', 'admission_number', 'parent_email']
    if not data or any(field not in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    try:
        parent = User.query.filter_by(email=data['parent_email'], role='parent', deleted_at=None).first()
        if not parent:
            return jsonify({"message": "Parent email not found or not a parent role"}), 404
        school_class = SchoolClass.query.filter_by(id=data['school_class_id'], deleted_at=None).first()
        if not school_class:
            return jsonify({"message": "School class not found"}), 404
        new_student = Student(
            name=data['name'],
            school_class_id=data['school_class_id'],
            admission_number=data['admission_number'],
            parent_id=parent.id,
            deleted_at=None
        )
        db.session.add(new_student)
        db.session.commit()
        # Seed student-subject relationships (optional, based on input or default)
        if 'subjects' in data and data['subjects']:
            subjects = data['subjects'] if isinstance(data['subjects'], list) else data['subjects'].split(",")
            for subject_name in subjects:
                subject = Subject.query.filter_by(name=subject_name.strip(), deleted_at=None).first()
                if subject:
                    new_student.subjects.append(subject)  # Use back_populates: student.subjects -> subject.enrolled_students
        db.session.commit()
        return jsonify(StudentSchema().dump(new_student)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create student", "error": str(e)}), 500

@api_bp.route('/students', methods=['GET'])
def get_students():
    students = Student.query.filter(Student.deleted_at.is_(None)).all()  # Exclude soft-deleted students
    students_data = [
        {
            "id": student.id,
            "name": student.name,
            "admission_number": student.admission_number,
            "school_class_id": student.school_class_id,
            "class_name": student.school_class.name if student.school_class and not is_soft_deleted(student.school_class) else "N/A",
            "parent_email": student.parent.email if student.parent and not is_soft_deleted(student.parent) else "N/A",
            "subjects": [subject.name for subject in student.subjects if not is_soft_deleted(subject)]  # Use back_populates: student.subjects -> subject.enrolled_students
        }
        for student in students
    ]
    return jsonify(students_data)

@api_bp.route('/parents/<int:parent_id>/students', methods=['GET'])
def get_students_by_parent(parent_id):
    parent = User.query.filter_by(id=parent_id, role='parent', deleted_at=None).first()
    if not parent:
        return jsonify({"message": "Parent not found"}), 404
    students = Student.query.filter_by(parent_id=parent_id, deleted_at=None).all()  # Exclude soft-deleted students
    students_data = [
        {
            "id": student.id,
            "name": student.name,
            "admission_number": student.admission_number,
            "school_class_id": student.school_class_id,
            "class_name": student.school_class.name if student.school_class and not is_soft_deleted(student.school_class) else "N/A"
        }
        for student in students
    ]
    return jsonify(students_data), 200

@api_bp.route('/students/<int:id>', methods=['GET'])
def get_student_by_id(id):
    student = Student.query.filter_by(id=id, deleted_at=None).first()  # Exclude soft-deleted students
    if student:
        class_teacher = student.school_class.class_teacher if student.school_class and not is_soft_deleted(student.school_class) else None
        student_data = {
            "id": student.id,
            "name": student.name,
            "admission_number": student.admission_number,
            "school_class_id": student.school_class_id,
            "class_name": student.school_class.name if student.school_class and not is_soft_deleted(student.school_class) else "N/A",
            "parent_email": student.parent.email if student.parent and not is_soft_deleted(student.parent) else "N/A",
            "class_teacher_email": class_teacher.email if class_teacher and not is_soft_deleted(class_teacher) else "N/A",
            "subjects": [subject.name for subject in student.subjects if not is_soft_deleted(subject)]  # Use back_populates: student.subjects -> subject.enrolled_students
        }
        return jsonify(student_data)
    return jsonify({"message": "Student not found"}), 404

# Get subjects for a student (via student_subject)
@api_bp.route('/students/<int:student_id>/subjects', methods=['GET'])
def get_student_subjects(student_id):
    student = Student.query.filter_by(id=student_id, deleted_at=None).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    subjects = student.subjects  # Use back_populates: student.subjects -> subject.enrolled_students
    subjects_data = [{"id": subject.id, "name": subject.name} for subject in subjects if not is_soft_deleted(subject)]
    return jsonify(subjects_data), 200

@api_bp.route('/students/<int:id>', methods=['PUT'])
def update_student(id):
    student = Student.query.filter_by(id=id, deleted_at=None).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    try:
        student.name = data.get('name', student.name)
        if 'school_class_id' in data:
            school_class = SchoolClass.query.filter_by(id=data['school_class_id'], deleted_at=None).first()
            if not school_class:
                return jsonify({"message": "School class not found"}), 404
            student.school_class_id = data['school_class_id']
        student.admission_number = data.get('admission_number', student.admission_number)
        if 'parent_email' in data:
            parent = User.query.filter_by(email=data['parent_email'], role='parent', deleted_at=None).first()
            if not parent:
                return jsonify({"message": "Parent email not found or not a parent role"}), 404
            student.parent_id = parent.id
        if 'subjects' in data:
            # Clear existing subjects and add new ones using back_populates
            student.subjects = []  # Clear existing subjects via back_populates
            subjects = data['subjects'] if isinstance(data['subjects'], list) else data['subjects'].split(",")
            for subject_name in subjects:
                subject = Subject.query.filter_by(name=subject_name.strip(), deleted_at=None).first()
                if subject:
                    student.subjects.append(subject)  # Use back_populates: student.subjects -> subject.enrolled_students
        db.session.commit()
        return jsonify(StudentSchema().dump(student))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update student", "error": str(e)}), 500

@api_bp.route('/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    student = Student.query.filter_by(id=id, deleted_at=None).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    try:
        # Soft delete instead of hard delete
        student.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Student soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete student", "error": str(e)}), 500

# --- Class Routes ---

@api_bp.route('/classes', methods=['POST'])
def create_class():
    data = request.get_json()
    required_fields = ['name', 'form_id']
    if not data or any(field not in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    form = Form.query.filter_by(id=data['form_id'], deleted_at=None).first()
    if not form:
        return jsonify({"message": "Form not found"}), 404
    try:
        class_teacher = None
        if 'class_teacher_id' in data:
            class_teacher = User.query.filter_by(id=data['class_teacher_id'], role='teacher', deleted_at=None).first()
            if not class_teacher:
                return jsonify({"message": "Class teacher not found or not a teacher"}), 404
        new_class = SchoolClass(
            name=data['name'],
            form_id=data['form_id'],
            class_teacher_id=class_teacher.id if class_teacher else None,
            deleted_at=None
        )
        db.session.add(new_class)
        db.session.commit()
        return jsonify({
            "id": new_class.id,
            "name": new_class.name,
            "form_id": new_class.form_id,
            "form_name": form.name,
            "class_teacher_id": new_class.class_teacher_id,
            "class_teacher_email": class_teacher.email if class_teacher else "N/A"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create class", "error": str(e)}), 500

@api_bp.route('/classes', methods=['GET'])
def get_classes():
    classes = SchoolClass.query.filter(SchoolClass.deleted_at.is_(None)).all()  # Exclude soft-deleted classes
    class_list = [
        {
            "id": cls.id,
            "name": cls.name,
            "form_id": cls.form_id,
            "form_name": cls.form.name if cls.form and not is_soft_deleted(cls.form) else "N/A",
            "class_teacher_id": cls.class_teacher_id,
            "class_teacher_email": cls.class_teacher.email if cls.class_teacher and not is_soft_deleted(cls.class_teacher) else "N/A"
        }
        for cls in classes
    ]
    return jsonify(class_list)

@api_bp.route('/classes/<int:id>', methods=['GET'])
def get_class_by_id(id):
    class_obj = SchoolClass.query.filter_by(id=id, deleted_at=None).first()  # Exclude soft-deleted classes
    if class_obj:
        return jsonify({
            "id": class_obj.id,
            "name": class_obj.name,
            "form_id": class_obj.form_id,
            "form_name": class_obj.form.name if class_obj.form and not is_soft_deleted(class_obj.form) else "N/A",
            "class_teacher_id": class_obj.class_teacher_id,
            "class_teacher_email": class_obj.class_teacher.email if class_obj.class_teacher and not is_soft_deleted(class_obj.class_teacher) else "N/A"
        })
    return jsonify({"message": "Class not found"}), 404

@api_bp.route('/classes/<int:id>', methods=['PUT'])
def update_class(id):
    class_obj = SchoolClass.query.filter_by(id=id, deleted_at=None).first()
    if not class_obj:
        return jsonify({"message": "Class not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    try:
        if 'form_id' in data:
            form = Form.query.filter_by(id=data['form_id'], deleted_at=None).first()
            if not form:
                return jsonify({"message": "Form not found"}), 404
            class_obj.form_id = data['form_id']
        if 'class_teacher_id' in data:
            class_teacher = User.query.filter_by(id=data['class_teacher_id'], role='teacher', deleted_at=None).first()
            if not class_teacher and data['class_teacher_id'] is not None:
                return jsonify({"message": "Class teacher not found or not a teacher"}), 404
            class_obj.class_teacher_id = class_teacher.id if class_teacher else None
        class_obj.name = data.get('name', class_obj.name)
        db.session.commit()
        return jsonify({
            "id": class_obj.id,
            "name": class_obj.name,
            "form_id": class_obj.form_id,
            "form_name": class_obj.form.name if class_obj.form and not is_soft_deleted(class_obj.form) else "N/A",
            "class_teacher_id": class_obj.class_teacher_id,
            "class_teacher_email": class_obj.class_teacher.email if class_obj.class_teacher and not is_soft_deleted(class_obj.class_teacher) else "N/A"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update class", "error": str(e)}), 500

@api_bp.route('/classes/<int:id>', methods=['DELETE'])
def delete_class(id):
    class_obj = SchoolClass.query.filter_by(id=id, deleted_at=None).first()
    if not class_obj:
        return jsonify({"message": "Class not found"}), 404
    try:
        # Soft delete instead of hard delete
        class_obj.deleted_at = datetime.utcnow()
        # Update students to remove reference to this class (soft delete or set to None)
        students = Student.query.filter_by(school_class_id=id, deleted_at=None).all()
        for student in students:
            student.school_class_id = None  # Optionally soft delete students or set to a default class
        db.session.commit()
        return jsonify({"message": "Class soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete class", "error": str(e)}), 500

# --- Subject Routes ---

@api_bp.route('/subjects', methods=['POST'])
def create_subject():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"message": "Missing required fields"}), 400
    try:
        new_subject = Subject(name=data['name'], deleted_at=None)
        db.session.add(new_subject)
        db.session.commit()
        return jsonify(SubjectSchema().dump(new_subject)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create subject", "error": str(e)}), 500

@api_bp.route('/subjects', methods=['GET'])
def get_subjects():
    subjects = Subject.query.filter(Subject.deleted_at.is_(None)).all()  # Exclude soft-deleted subjects
    return jsonify(SubjectSchema(many=True).dump(subjects))

@api_bp.route('/subjects/<int:id>', methods=['GET'])
def get_subject_by_id(id):
    subject = Subject.query.filter_by(id=id, deleted_at=None).first()  # Exclude soft-deleted subjects
    if subject:
        return jsonify(SubjectSchema().dump(subject))
    return jsonify({"message": "Subject not found"}), 404

@api_bp.route('/subjects/<int:id>', methods=['PUT'])
def update_subject(id):
    subject = Subject.query.filter_by(id=id, deleted_at=None).first()
    if not subject:
        return jsonify({"message": "Subject not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    try:
        subject.name = data.get('name', subject.name)
        db.session.commit()
        return jsonify(SubjectSchema().dump(subject))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update subject", "error": str(e)}), 500

@api_bp.route('/subjects/<int:id>', methods=['DELETE'])
def delete_subject(id):
    subject = Subject.query.filter_by(id=id, deleted_at=None).first()
    if not subject:
        return jsonify({"message": "Subject not found"}), 404
    try:
        # Soft delete instead of hard delete
        subject.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Subject soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete subject", "error": str(e)}), 500

# --- Exam Routes ---

@api_bp.route('/exams', methods=['POST'])
def create_exam():
    data = request.get_json()
    if not data or 'name' not in data or 'form_id' not in data:
        return jsonify({"message": "Missing required fields"}), 400
    form = Form.query.filter_by(id=data['form_id'], deleted_at=None).first()
    if not form:
        return jsonify({"message": "Form not found"}), 404
    try:
        new_exam = Exam(name=data['name'], form_id=data['form_id'], deleted_at=None)
        db.session.add(new_exam)
        db.session.commit()
        return jsonify(ExamSchema().dump(new_exam)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create exam", "error": str(e)}), 500

@api_bp.route('/exams', methods=['GET'])
def get_exams():
    exams = Exam.query.filter(Exam.deleted_at.is_(None)).all()  # Exclude soft-deleted exams
    return jsonify(ExamSchema(many=True).dump(exams))

@api_bp.route('/exams/<int:id>', methods=['GET'])
def get_exam_by_id(id):
    exam = Exam.query.filter_by(id=id, deleted_at=None).first()  # Exclude soft-deleted exams
    if exam:
        return jsonify(ExamSchema().dump(exam))
    return jsonify({"message": "Exam not found"}), 404

@api_bp.route('/exams/<int:id>', methods=['PUT'])
def update_exam(id):
    exam = Exam.query.filter_by(id=id, deleted_at=None).first()
    if not exam:
        return jsonify({"message": "Exam not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    try:
        exam.name = data.get('name', exam.name)
        if 'form_id' in data:
            form = Form.query.filter_by(id=data['form_id'], deleted_at=None).first()
            if not form:
                return jsonify({"message": "Form not found"}), 404
            exam.form_id = data['form_id']
        db.session.commit()
        return jsonify(ExamSchema().dump(exam))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update exam", "error": str(e)}), 500

@api_bp.route('/exams/<int:id>', methods=['DELETE'])
def delete_exam(id):
    exam = Exam.query.filter_by(id=id, deleted_at=None).first()
    if not exam:
        return jsonify({"message": "Exam not found"}), 404
    try:
        # Soft delete instead of hard delete
        exam.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Exam soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete exam", "error": str(e)}), 500

# --- Result Routes ---

@api_bp.route('/results', methods=['POST'])
def create_result():
    data = request.get_json()
    required_fields = ['student_id', 'subject_id', 'exam_id', 'score']
    if not data or any(field not in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    try:
        student = Student.query.filter_by(id=data['student_id'], deleted_at=None).first()
        subject = Subject.query.filter_by(id=data['subject_id'], deleted_at=None).first()
        exam = Exam.query.filter_by(id=data['exam_id'], deleted_at=None).first()
        if not student or not subject or not exam:
            return jsonify({"message": "Invalid student, subject, or exam ID"}), 404
        new_result = Result(
            student_id=data['student_id'],
            subject_id=data['subject_id'],
            exam_id=data['exam_id'],
            score=data['score'],
            deleted_at=None
        )
        db.session.add(new_result)
        db.session.commit()
        return jsonify(ResultSchema().dump(new_result)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create result", "error": str(e)}), 500

@api_bp.route('/results', methods=['GET'])
def get_results():
    results = Result.query.filter(Result.deleted_at.is_(None)).all()  # Exclude soft-deleted results
    return jsonify(ResultSchema(many=True).dump(results))

@api_bp.route('/results/<int:id>', methods=['GET'])
def get_result_by_id(id):
    result = Result.query.filter_by(id=id, deleted_at=None).first()  # Exclude soft-deleted results
    if result:
        return jsonify(ResultSchema().dump(result))
    return jsonify({"message": "Result not found"}), 404

@api_bp.route('/students/<int:student_id>/results', methods=['GET'])
def get_results_for_student(student_id):
    student = Student.query.filter_by(id=student_id, deleted_at=None).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    results = student.results  # Use back_populates: student.results -> Result.student
    results_data = [
        {
            "id": result.id,
            "student_id": result.student_id,
            "subject_id": result.subject_id,
            "subject_name": result.subject.name if result.subject and not is_soft_deleted(result.subject) else "N/A",
            "exam_id": result.exam_id,
            "exam_name": result.exam.name if result.exam and not is_soft_deleted(result.exam) else "N/A",
            "score": result.score,
            "created_at": result.created_at.isoformat()
        }
        for result in results if not is_soft_deleted(result)
    ]
    return jsonify(results_data), 200

@api_bp.route('/results/<int:id>', methods=['PUT'])
def update_result(id):
    result = Result.query.filter_by(id=id, deleted_at=None).first()
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

@api_bp.route('/results/<int:id>', methods=['DELETE'])
def delete_result(id):
    result = Result.query.filter_by(id=id, deleted_at=None).first()
    if not result:
        return jsonify({"message": "Result not found"}), 404
    try:
        # Soft delete instead of hard delete
        result.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Result soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete result", "error": str(e)}), 500

# --- Welfare Report Routes ---

@api_bp.route('/welfare_reports', methods=['POST'])
def create_welfare_report():
    data = request.get_json()
    required_fields = ['student_id', 'category', 'remarks']
    if not data or any(field not in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    if data['category'] not in ['Discipline', 'Health', 'Academic']:
        return jsonify({"message": "Invalid category"}), 400
    try:
        student = Student.query.filter_by(id=data['student_id'], deleted_at=None).first()
        if not student:
            return jsonify({"message": "Student not found"}), 404
        new_report = WelfareReport(
            student_id=data['student_id'],
            category=data['category'],
            remarks=data['remarks'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            deleted_at=None
        )
        db.session.add(new_report)
        db.session.commit()
        return jsonify(WelfareReportSchema().dump(new_report)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create welfare report", "error": str(e)}), 500

@api_bp.route('/welfare_reports', methods=['GET'])
def get_welfare_reports():
    reports = WelfareReport.query.filter(WelfareReport.deleted_at.is_(None)).all()  # Exclude soft-deleted reports
    return jsonify(WelfareReportSchema(many=True).dump(reports))

@api_bp.route('/welfare_reports/<int:id>', methods=['GET'])
def get_welfare_report_by_id(id):
    report = WelfareReport.query.filter_by(id=id, deleted_at=None).first()  # Exclude soft-deleted reports
    if report:
        return jsonify(WelfareReportSchema().dump(report))
    return jsonify({"message": "Welfare Report not found"}), 404

@api_bp.route('/students/<int:student_id>/welfare_reports', methods=['GET'])
def get_welfare_reports_for_student(student_id):
    category = request.args.get('category')
    student = Student.query.filter_by(id=student_id, deleted_at=None).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    reports = student.welfare_reports  # Use back_populates: student.welfare_reports -> WelfareReport.student
    if category:
        if category not in ['Discipline', 'Health', 'Academic']:
            return jsonify({"message": "Invalid category"}), 400
        reports = [r for r in reports if r.category == category and not is_soft_deleted(r)]
    return jsonify(WelfareReportSchema(many=True).dump(reports))

@api_bp.route('/welfare_reports/<int:id>', methods=['PUT'])
def update_welfare_report(id):
    report = WelfareReport.query.filter_by(id=id, deleted_at=None).first()
    if not report:
        return jsonify({"message": "Welfare Report not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    try:
        if 'remarks' in data:
            report.remarks = data['remarks']
        if 'category' in data:
            if data['category'] not in ['Discipline', 'Health', 'Academic']:
                return jsonify({"message": "Invalid category"}), 400
            report.category = data['category']
        report.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify(WelfareReportSchema().dump(report))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update welfare report", "error": str(e)}), 500

@api_bp.route('/welfare_reports/<int:id>', methods=['DELETE'])
def delete_welfare_report(id):
    report = WelfareReport.query.filter_by(id=id, deleted_at=None).first()
    if not report:
        return jsonify({"message": "Welfare Report not found"}), 404
    try:
        # Soft delete instead of hard delete
        report.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Welfare Report soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete welfare report", "error": str(e)}), 500

# --- Teacher Routes ---

@api_bp.route('/teachers', methods=['GET'])
def get_teachers():
    teachers = User.query.filter_by(role='teacher', deleted_at=None).options(joinedload(User.teacher).joinedload(Teacher.subjects)).all()  # Exclude soft-deleted teachers
    teacher_data = [
        {
            "id": teacher.id,
            "username": teacher.username,
            "email": teacher.email,
            "subjects": [subject.name for subject in teacher.teacher.subjects if not is_soft_deleted(subject)] if teacher.teacher else [],  # Use back_populates: teacher.subjects -> subject.teaching_teachers
            "managed_class": {"id": cls.id, "name": cls.name} if (cls := SchoolClass.query.filter_by(class_teacher_id=teacher.id, deleted_at=None).first()) else None
        }
        for teacher in teachers
    ]
    return jsonify(teacher_data)

@api_bp.route('/teachers/<int:id>', methods=['GET'])
def get_teacher_by_id(id):
    teacher = User.query.filter_by(id=id, role='teacher', deleted_at=None).first()  # Exclude soft-deleted teachers
    if teacher:
        return jsonify(UserSchema().dump(teacher))
    return jsonify({"message": "Teacher not found"}), 404

@api_bp.route('/teachers', methods=['POST'])
def create_teacher():
    data = request.get_json()
    required_fields = ['username', 'email', 'password']
    if not data or any(field not in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    try:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], email=data['email'], password=hashed_password, role='teacher', deleted_at=None)
        db.session.add(new_user)
        db.session.commit()
        new_teacher = Teacher(user_id=new_user.id, deleted_at=None)
        db.session.add(new_teacher)
        if 'subjects' in data and data['subjects']:
            subjects = data['subjects'] if isinstance(data['subjects'], list) else data['subjects'].split(",")
            for subject_name in subjects:
                subject = Subject.query.filter_by(name=subject_name.strip(), deleted_at=None).first()
                if subject:
                    teacher_subject = TeacherSubject(teacher_id=new_teacher.id, subject_id=subject.id, deleted_at=None)
                    db.session.add(teacher_subject)  # Use TeacherSubject for many-to-many, which updates teacher.subjects and subject.teaching_teachers via back_populates
        db.session.commit()
        return jsonify(UserSchema().dump(new_user)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create teacher", "error": str(e)}), 500

@api_bp.route('/teachers/<int:id>', methods=['PUT'])
def update_teacher(id):
    teacher = User.query.filter_by(id=id, role='teacher', deleted_at=None).first()
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
        if 'subjects' in data:
            TeacherSubject.query.filter_by(teacher_id=teacher.teacher.id, deleted_at=None).delete()
            subjects = data['subjects'] if isinstance(data['subjects'], list) else data['subjects'].split(",")
            for subject_name in subjects:
                subject = Subject.query.filter_by(name=subject_name.strip(), deleted_at=None).first()
                if subject:
                    teacher_subject = TeacherSubject(teacher_id=teacher.teacher.id, subject_id=subject.id, deleted_at=None)
                    db.session.add(teacher_subject)  # Use TeacherSubject for many-to-many, which updates teacher.subjects and subject.teaching_teachers via back_populates
        db.session.commit()
        return jsonify(UserSchema().dump(teacher))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update teacher", "error": str(e)}), 500

@api_bp.route('/teachers/<int:id>', methods=['DELETE'])
def delete_teacher(id):
    teacher = User.query.filter_by(id=id, role='teacher', deleted_at=None).first()
    if not teacher:
        return jsonify({"message": "Teacher not found"}), 404
    try:
        # Soft delete instead of hard delete
        if teacher.teacher:
            teacher.teacher.deleted_at = datetime.utcnow()
        teacher.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Teacher soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete teacher", "error": str(e)}), 500

# --- Form Routes ---

@api_bp.route('/forms', methods=['GET'])
def get_forms():
    forms = Form.query.filter(Form.deleted_at.is_(None)).all()  # Exclude soft-deleted forms
    return jsonify([{"id": f.id, "name": f.name} for f in forms])