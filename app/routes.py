from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token # Added JWT imports
from datetime import datetime
from app import db
from app.models import User, Student, SchoolClass, Subject, Exam, Result, WelfareReport, Teacher, Form, TeacherSubject
from app.schemas import UserSchema, StudentSchema, SchoolClassSchema, SubjectSchema, ExamSchema, ResultSchema, WelfareReportSchema, FormSchema
from sqlalchemy.orm import joinedload
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)
bcrypt = Bcrypt()
jwt = JWTManager()  # Initialize JWTManager (ensure it's configured in your app)

# --- Helper Function for Soft Deletes ---
def is_soft_deleted(model_instance):
    """Check if a model instance is soft-deleted by checking the deleted_at field."""
    return getattr(model_instance, 'deleted_at', None) is not None

# --- Authentication Routes ---

@api_bp.route('/login', methods=['POST'])
def login():
    """Handle user login and return user data with JWT token."""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"message": "Email and password are required"}), 400

    email = data['email']
    password = data['password']

    user = User.query.filter_by(email=email, deleted_at=None).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Invalid email or password"}), 401

    from flask_jwt_extended import create_access_token  # Import here or globally
    access_token = create_access_token(identity=user.id)  # Generate JWT token
    user_data = UserSchema().dump(user)

    return jsonify({
        "user": user_data,
        "token": access_token  # Return token to frontend
    }), 200

# --- User Routes ---

@api_bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user (public registration, typically for parents)."""
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data or 'password' not in data or 'role' not in data:
        return jsonify({"message": "Missing required fields"}), 400
    
    if User.query.filter_by(email=data['email'], deleted_at=None).first():
        return jsonify({"message": "Email already registered"}), 409

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
@jwt_required()
def get_users():
    """Retrieve all users (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    users = User.query.filter(User.deleted_at.is_(None)).all()
    return jsonify(UserSchema(many=True).dump(users))

@api_bp.route('/user/roles', methods=['GET'])
@jwt_required()
def get_user_roles():
    """Get additional roles for a user (admin or self)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    target_user_id = request.args.get('user_id')
    target_user = User.query.filter_by(id=target_user_id, deleted_at=None).first()
    
    if not target_user:
        return jsonify({"error": "User not found"}), 404
    if user.role != 'admin' and str(user.id) != target_user_id:
        return jsonify({"message": "Unauthorized: Can only view own roles or requires admin"}), 401

    roles = []
    if SchoolClass.query.filter_by(class_teacher_id=target_user_id, deleted_at=None).first():
        roles.append("class_teacher")
    if Teacher.query.filter_by(user_id=target_user_id, deleted_at=None).first():
        roles.append("subject_teacher")
    return jsonify({"roles": roles}), 200

@api_bp.route('/users/by-role', methods=['GET'])
@jwt_required()
def get_users_by_role():
    """Retrieve users by role (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    role = request.args.get('role')
    if not role:
        return jsonify({"message": "Role parameter is required"}), 400
    users = User.query.filter_by(role=role, deleted_at=None).all()
    return jsonify(UserSchema(many=True).dump(users))

@api_bp.route('/users/search', methods=['GET'])
@jwt_required()
def search_user():
    """Search for a user by username (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    username = request.args.get('username')
    if not username:
        return jsonify({"message": "Username is required"}), 400
    target_user = User.query.filter_by(username=username, deleted_at=None).first()
    if target_user:
        return jsonify(UserSchema().dump(target_user))
    return jsonify({"message": "User not found"}), 404

@api_bp.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    """Update a user (admin or self)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    target_user = User.query.filter_by(id=id, deleted_at=None).first()
    if not target_user:
        return jsonify({"message": "User not found"}), 404
    if user.role != 'admin' and user.id != id:
        return jsonify({"message": "Unauthorized: Can only update own profile or requires admin"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    try:
        target_user.username = data.get('username', target_user.username)
        target_user.email = data.get('email', target_user.email)
        if 'password' in data:
            target_user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        if 'role' in data and user.role == 'admin':  # Only admin can change role
            target_user.role = data['role']
        db.session.commit()
        return jsonify(UserSchema().dump(target_user))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update user", "error": str(e)}), 500

@api_bp.route('/users/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    """Soft-delete a user (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    target_user = User.query.filter_by(id=id, deleted_at=None).first()
    if not target_user:
        return jsonify({"message": "User not found"}), 404
    try:
        target_user.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "User soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete user", "error": str(e)}), 500

# --- Student Routes ---

@api_bp.route('/students', methods=['POST'])
@jwt_required()
def create_student():
    """Create a student (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
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
        if 'subjects' in data and data['subjects']:
            subjects = data['subjects'] if isinstance(data['subjects'], list) else data['subjects'].split(",")
            for subject_name in subjects:
                subject = Subject.query.filter_by(name=subject_name.strip(), deleted_at=None).first()
                if subject:
                    new_student.subjects.append(subject)
        db.session.commit()
        return jsonify(StudentSchema().dump(new_student)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create student", "error": str(e)}), 500

@api_bp.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    """Retrieve students (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Unauthorized: Teacher or Admin access required"}), 401
    
    if user.role == 'teacher':
        classes = SchoolClass.query.filter_by(class_teacher_id=current_user_id, deleted_at=None).all()
        class_ids = [cls.id for cls in classes]
        students = Student.query.filter(Student.school_class_id.in_(class_ids), Student.deleted_at.is_(None)).all()
    else:  # admin
        students = Student.query.filter(Student.deleted_at.is_(None)).all()

    students_data = [
        {
            "id": student.id,
            "name": student.name,
            "admission_number": student.admission_number,
            "school_class_id": student.school_class_id,
            "class_name": student.school_class.name if student.school_class and not is_soft_deleted(student.school_class) else "N/A",
            "parent_id": student.parent_id,
            "subjects": [subject.name for subject in student.subjects if not is_soft_deleted(subject)]
        }
        for student in students
    ]
    return jsonify(students_data)

@api_bp.route('/parents/<int:parent_id>/students', methods=['GET'])
@jwt_required()
def get_students_by_parent(parent_id):
    """Retrieve students for a parent (parent only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'parent' or user.id != parent_id:
        return jsonify({"message": "Unauthorized: Can only view own students"}), 401
    students = Student.query.filter_by(parent_id=parent_id, deleted_at=None).all()
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
@jwt_required()
def get_student_by_id(id):
    """Retrieve a student (parent, teacher, or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    student = Student.query.filter_by(id=id, deleted_at=None).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    if user.role == 'parent' and student.parent_id != current_user_id:
        return jsonify({"message": "Unauthorized: Not your student"}), 401
    elif user.role == 'teacher':
        classes = SchoolClass.query.filter_by(class_teacher_id=current_user_id, deleted_at=None).all()
        class_ids = [cls.id for cls in classes]
        if student.school_class_id not in class_ids:
            return jsonify({"message": "Unauthorized: Not in your class"}), 401
    
    class_teacher = student.school_class.class_teacher if student.school_class and not is_soft_deleted(student.school_class) else None
    student_data = {
        "id": student.id,
        "name": student.name,
        "admission_number": student.admission_number,
        "school_class_id": student.school_class_id,
        "class_name": student.school_class.name if student.school_class and not is_soft_deleted(student.school_class) else "N/A",
        "parent_id": student.parent_id,
        "class_teacher_email": class_teacher.email if class_teacher and not is_soft_deleted(class_teacher) else "N/A",
        "subjects": [subject.name for subject in student.subjects if not is_soft_deleted(subject)]
    }
    return jsonify(student_data)

@api_bp.route('/students/<int:student_id>/subjects', methods=['GET'])
@jwt_required()
def get_student_subjects(student_id):
    """Retrieve subjects for a student (parent, teacher, or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    student = Student.query.filter_by(id=student_id, deleted_at=None).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    if user.role == 'parent' and student.parent_id != current_user_id:
        return jsonify({"message": "Unauthorized: Not your student"}), 401
    elif user.role == 'teacher':
        classes = SchoolClass.query.filter_by(class_teacher_id=current_user_id, deleted_at=None).all()
        class_ids = [cls.id for cls in classes]
        if student.school_class_id not in class_ids:
            return jsonify({"message": "Unauthorized: Not in your class"}), 401
    
    subjects = student.subjects
    subjects_data = [{"id": subject.id, "name": subject.name} for subject in subjects if not is_soft_deleted(subject)]
    return jsonify(subjects_data), 200

@api_bp.route('/students/<int:id>', methods=['PUT'])
@jwt_required()
def update_student(id):
    """Update a student (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
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
            student.subjects = []
            subjects = data['subjects'] if isinstance(data['subjects'], list) else data['subjects'].split(",")
            for subject_name in subjects:
                subject = Subject.query.filter_by(name=subject_name.strip(), deleted_at=None).first()
                if subject:
                    student.subjects.append(subject)
        db.session.commit()
        return jsonify(StudentSchema().dump(student))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update student", "error": str(e)}), 500

@api_bp.route('/students/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_student(id):
    """Soft-delete a student (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    student = Student.query.filter_by(id=id, deleted_at=None).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    try:
        student.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Student soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete student", "error": str(e)}), 500

@api_bp.route('/students/promote', methods=['POST'])
@jwt_required()
def promote_students():
    """Promote students (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    data = request.get_json()
    if not data or 'student_ids' not in data or 'target_form' not in data:
        return jsonify({"message": "Missing required fields: student_ids and target_form"}), 400

    student_ids = data['student_ids']
    target_form_name = data['target_form']

    try:
        target_form = Form.query.filter_by(name=target_form_name, deleted_at=None).first()
        if not target_form:
            return jsonify({"message": f"Form '{target_form_name}' not found"}), 404

        target_class = SchoolClass.query.filter_by(form_id=target_form.id, deleted_at=None).first()
        if not target_class:
            target_class = SchoolClass(
                name=f"{target_form_name}A",
                form_id=target_form.id,
                class_teacher_id=None,
                deleted_at=None
            )
            db.session.add(target_class)
            db.session.commit()

        students = Student.query.filter(Student.id.in_(student_ids), Student.deleted_at.is_(None)).all()
        if not students:
            return jsonify({"message": "No valid students found"}), 404

        for student in students:
            current_class = SchoolClass.query.filter_by(id=student.school_class_id, deleted_at=None).first()
            if current_class and current_class.form.name == target_form_name:
                continue
            student.school_class_id = target_class.id

        db.session.commit()
        updated_students = StudentSchema(many=True).dump(students)
        return jsonify({
            "message": f"Students promoted to {target_form_name}",
            "students": updated_students
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to promote students", "error": str(e)}), 500

# --- Class Routes ---

@api_bp.route('/classes', methods=['POST'])
@jwt_required()
def create_class():
    """Create a class (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
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
@jwt_required()
def get_classes():
    """Retrieve classes (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Unauthorized: Teacher or Admin access required"}), 401
    
    if user.role == 'teacher':
        class_teacher_id = request.args.get('class_teacher_id')
        if class_teacher_id and int(class_teacher_id) != current_user_id:
            return jsonify({"message": "Unauthorized: Can only view own classes"}), 401
        classes = SchoolClass.query.filter_by(class_teacher_id=current_user_id, deleted_at=None).all()
    else:  # admin
        classes = SchoolClass.query.filter(SchoolClass.deleted_at.is_(None)).all()

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
@jwt_required()
def get_class_by_id(id):
    """Retrieve a class (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    class_obj = SchoolClass.query.filter_by(id=id, deleted_at=None).first()
    if not class_obj:
        return jsonify({"message": "Class not found"}), 404
    if user.role == 'teacher' and class_obj.class_teacher_id != current_user_id:
        return jsonify({"message": "Unauthorized: Not your class"}), 401
    return jsonify({
        "id": class_obj.id,
        "name": class_obj.name,
        "form_id": class_obj.form_id,
        "form_name": class_obj.form.name if class_obj.form and not is_soft_deleted(class_obj.form) else "N/A",
        "class_teacher_id": class_obj.class_teacher_id,
        "class_teacher_email": class_obj.class_teacher.email if class_obj.class_teacher and not is_soft_deleted(class_obj.class_teacher) else "N/A"
    })

@api_bp.route('/classes/<int:id>', methods=['PUT'])
@jwt_required()
def update_class(id):
    """Update a class (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
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
@jwt_required()
def delete_class(id):
    """Soft-delete a class (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    class_obj = SchoolClass.query.filter_by(id=id, deleted_at=None).first()
    if not class_obj:
        return jsonify({"message": "Class not found"}), 404
    try:
        class_obj.deleted_at = datetime.utcnow()
        students = Student.query.filter_by(school_class_id=id, deleted_at=None).all()
        for student in students:
            student.school_class_id = None
        db.session.commit()
        return jsonify({"message": "Class soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete class", "error": str(e)}), 500

# --- Subject Routes ---

@api_bp.route('/subjects', methods=['POST'])
@jwt_required()
def create_subject():
    """Create a subject (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
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
@jwt_required()
def get_subjects():
    """Retrieve subjects (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Unauthorized: Teacher or Admin access required"}), 401
    subjects = Subject.query.filter(Subject.deleted_at.is_(None)).all()
    return jsonify(SubjectSchema(many=True).dump(subjects))

@api_bp.route('/subjects/<int:id>', methods=['GET'])
@jwt_required()
def get_subject_by_id(id):
    """Retrieve a subject (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Unauthorized: Teacher or Admin access required"}), 401
    subject = Subject.query.filter_by(id=id, deleted_at=None).first()
    if subject:
        return jsonify(SubjectSchema().dump(subject))
    return jsonify({"message": "Subject not found"}), 404

@api_bp.route('/subjects/<int:id>', methods=['PUT'])
@jwt_required()
def update_subject(id):
    """Update a subject (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
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
@jwt_required()
def delete_subject(id):
    """Soft-delete a subject (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    subject = Subject.query.filter_by(id=id, deleted_at=None).first()
    if not subject:
        return jsonify({"message": "Subject not found"}), 404
    try:
        subject.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Subject soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete subject", "error": str(e)}), 500

# --- Exam Routes ---

@api_bp.route('/exams', methods=['POST'])
@jwt_required()
def create_exam():
    """Create an exam (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    data = request.get_json()
    logger.debug(f"Received data for creating exam: {data}")
    required_fields = ['name', 'form_name']
    if not data or any(field not in data for field in required_fields):
        logger.debug("Missing required fields detected")
        return jsonify({"message": "Missing required fields"}), 400
    form = Form.query.filter_by(name=data['form_name'], deleted_at=None).first()
    if not form:
        logger.debug(f"Form not found for name: {data['form_name']}")
        return jsonify({"message": "Form not found"}), 404
    try:
        date_value = None
        if data.get('date'):
            try:
                date_value = datetime.strptime(data['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError as e:
                logger.debug(f"Invalid date format: {data['date']}, error: {str(e)}")
                return jsonify({"message": "Invalid date format", "error": str(e)}), 400

        new_exam = Exam(
            name=data['name'],
            form_id=form.id,
            term=data.get('term', ''),
            date=date_value,
            deleted_at=None
        )
        db.session.add(new_exam)
        db.session.commit()
        return jsonify(ExamSchema().dump(new_exam)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create exam", "error": str(e)}), 500

@api_bp.route('/exams', methods=['GET'])
@jwt_required()
def get_exams():
    """Retrieve exams (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Unauthorized: Teacher or Admin access required"}), 401
    exams = Exam.query.filter(Exam.deleted_at.is_(None)).all()
    return jsonify(ExamSchema(many=True).dump(exams))

@api_bp.route('/exams/<int:id>', methods=['GET'])
@jwt_required()
def get_exam_by_id(id):
    """Retrieve an exam (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Unauthorized: Teacher or Admin access required"}), 401
    exam = Exam.query.filter_by(id=id, deleted_at=None).first()
    if exam:
        return jsonify(ExamSchema().dump(exam))
    return jsonify({"message": "Exam not found"}), 404

@api_bp.route('/exams/<int:id>', methods=['PUT'])
@jwt_required()
def update_exam(id):
    """Update an exam (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
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
@jwt_required()
def delete_exam(id):
    """Soft-delete an exam (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    exam = Exam.query.filter_by(id=id, deleted_at=None).first()
    if not exam:
        return jsonify({"message": "Exam not found"}), 404
    try:
        exam.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Exam soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete exam", "error": str(e)}), 500

# --- Result Routes ---

@api_bp.route('/results', methods=['POST'])
@jwt_required()
def create_result():
    """Create a result (teacher only)."""
    print("DEBUG: create_result called")  # Debug log
    current_user_id = get_jwt_identity()  # User.id from JWT
    user = User.query.get(current_user_id)
    if not user or user.role != 'teacher':
        return jsonify({"message": "Unauthorized: Teacher access required"}), 401

    data = request.get_json()
    required_fields = ['student_id', 'subject_id', 'exam_id', 'score', 'teacher_id']
    if not data or any(field not in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    # Verify the teacher_id matches the current user's Teacher record
    teacher = Teacher.query.filter_by(id=data['teacher_id'], user_id=current_user_id, deleted_at=None).first()
    if not teacher:
        return jsonify({"message": "Unauthorized: Invalid teacher ID or not your profile"}), 401

    try:
        student = Student.query.filter_by(id=data['student_id'], deleted_at=None).first()
        subject = Subject.query.filter_by(id=data['subject_id'], deleted_at=None).first()
        exam = Exam.query.filter_by(id=data['exam_id'], deleted_at=None).first()
        if not student or not subject or not exam:
            return jsonify({"message": "Invalid student, subject, or exam ID"}), 404

        classes = SchoolClass.query.filter_by(class_teacher_id=current_user_id, deleted_at=None).all()
        class_ids = [cls.id for cls in classes]
        if student.school_class_id not in class_ids:
            return jsonify({"message": "Unauthorized: Student not in your class"}), 401

        new_result = Result(
            student_id=data['student_id'],
            subject_id=data['subject_id'],
            exam_id=data['exam_id'],
            score=data['score'],
            teacher_id=data['teacher_id'],
            deleted_at=None
        )
        db.session.add(new_result)
        db.session.commit()
        return jsonify(ResultSchema().dump(new_result)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create result", "error": str(e)}), 500

@api_bp.route('/results', methods=['GET'])
@jwt_required()
def get_results():
    """Retrieve results (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Unauthorized: Teacher or Admin access required"}), 401
    
    if user.role == 'teacher':
        results = Result.query.filter_by(teacher_id=current_user_id, deleted_at=None).all()
    else:  # admin
        results = Result.query.filter(Result.deleted_at.is_(None)).all()
    
    return jsonify(ResultSchema(many=True).dump(results))

@api_bp.route('/results/<int:id>', methods=['GET'])
@jwt_required()
def get_result_by_id(id):
    """Retrieve a result (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    result = Result.query.filter_by(id=id, deleted_at=None).first()
    if not result:
        return jsonify({"message": "Result not found"}), 404
    if user.role == 'teacher' and result.teacher_id != current_user_id:
        return jsonify({"message": "Unauthorized: Not your result"}), 401
    return jsonify(ResultSchema().dump(result))

@api_bp.route('/students/<int:student_id>/results', methods=['GET'])
@jwt_required()
def get_results_for_student(student_id):
    """Retrieve results for a student (parent, teacher, or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    student = Student.query.filter_by(id=student_id, deleted_at=None).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    if user.role == 'parent' and student.parent_id != current_user_id:
        return jsonify({"message": "Unauthorized: Not your student"}), 401
    elif user.role == 'teacher':
        classes = SchoolClass.query.filter_by(class_teacher_id=current_user_id, deleted_at=None).all()
        class_ids = [cls.id for cls in classes]
        if student.school_class_id not in class_ids:
            return jsonify({"message": "Unauthorized: Not in your class"}), 401
    
    form = request.args.get('form')
    term = request.args.get('term')
    if not form or not term:
        return jsonify({"message": "Form and term parameters are required"}), 400

    results = student.results
    filtered_results = [
        r for r in results
        if r.exam and form.lower() in r.exam.form.name.lower() and r.exam.term and term.lower() in r.exam.term.lower()
    ]

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
        for result in filtered_results if not is_soft_deleted(result)
    ]
    return jsonify(results_data), 200

@api_bp.route('/results/<int:id>', methods=['PUT'])
@jwt_required()
def update_result(id):
    """Update a result (teacher only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'teacher':
        return jsonify({"message": "Unauthorized: Teacher access required"}), 401
    result = Result.query.filter_by(id=id, teacher_id=current_user_id, deleted_at=None).first()
    if not result:
        return jsonify({"message": "Result not found or not authorized"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    try:
        result.score = data.get('score', result.score)
        result.student_id = data.get('student_id', result.student_id)
        result.subject_id = data.get('subject_id', result.subject_id)
        result.exam_id = data.get('exam_id', result.exam_id)
        result.teacher_id = data.get('teacher_id', result.teacher_id)
        db.session.commit()
        return jsonify(ResultSchema().dump(result))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update result", "error": str(e)}), 500

@api_bp.route('/results/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_result(id):
    """Soft-delete a result (teacher only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'teacher':
        return jsonify({"message": "Unauthorized: Teacher access required"}), 401
    result = Result.query.filter_by(id=id, teacher_id=current_user_id, deleted_at=None).first()
    if not result:
        return jsonify({"message": "Result not found or not authorized"}), 404
    try:
        result.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Result soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete result", "error": str(e)}), 500

# --- Welfare Report Routes ---

@api_bp.route('/welfare_reports', methods=['POST'])
@jwt_required()
def create_welfare_report():
    """Create a welfare report (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Unauthorized: Teacher or Admin access required"}), 401
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
        
        # Only check class assignment for teachers, not admins
        if user.role == 'teacher':
            classes = SchoolClass.query.filter_by(class_teacher_id=current_user_id, deleted_at=None).all()
            class_ids = [cls.id for cls in classes]
            if student.school_class_id not in class_ids:
                return jsonify({"message": "Unauthorized: Student not in your class"}), 401
        
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
@jwt_required()
def get_welfare_reports():
    """Retrieve welfare reports (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Unauthorized: Teacher or Admin access required"}), 401
    
    if user.role == 'teacher':
        reports = WelfareReport.query.filter_by(created_by=current_user_id, deleted_at=None).all()
    else:  # admin
        reports = WelfareReport.query.filter(WelfareReport.deleted_at.is_(None)).all()
    
    return jsonify(WelfareReportSchema(many=True).dump(reports))

@api_bp.route('/welfare_reports/<int:id>', methods=['GET'])
@jwt_required()
def get_welfare_report_by_id(id):
    """Retrieve a welfare report (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    report = WelfareReport.query.filter_by(id=id, deleted_at=None).first()
    if not report:
        return jsonify({"message": "Welfare Report not found"}), 404
    if user.role == 'teacher' and report.created_by != current_user_id:
        return jsonify({"message": "Unauthorized: Not your report"}), 401
    return jsonify(WelfareReportSchema().dump(report))

@api_bp.route('/students/<int:student_id>/welfare_reports', methods=['GET'])
@jwt_required()
def get_welfare_reports_for_student(student_id):
    """Retrieve welfare reports for a student (parent, teacher, or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    student = Student.query.filter_by(id=student_id, deleted_at=None).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    if user.role == 'parent' and student.parent_id != current_user_id:
        return jsonify({"message": "Unauthorized: Not your student"}), 401
    elif user.role == 'teacher':
        classes = SchoolClass.query.filter_by(class_teacher_id=current_user_id, deleted_at=None).all()
        class_ids = [cls.id for cls in classes]
        if student.school_class_id not in class_ids:
            return jsonify({"message": "Unauthorized: Not in your class"}), 401
    
    category = request.args.get('category')
    query = WelfareReport.query.filter_by(student_id=student_id, deleted_at=None)
    if category:
        if category not in ['Discipline', 'Health', 'Academic']:
            return jsonify({"message": "Invalid category"}), 400
        query = query.filter(WelfareReport.category == category)
    
    reports = query.all()
    reports_data = [
        {
            "id": r.id,
            "student_id": r.student_id,
            "category": r.category,
            "remarks": r.remarks,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat() if r.updated_at else None
        }
        for r in reports
    ]
    return jsonify(reports_data), 200

@api_bp.route('/welfare_reports/<int:id>', methods=['PUT'])
@jwt_required()
def update_welfare_report(id):
    """Update a welfare report (teacher only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'teacher':
        return jsonify({"message": "Unauthorized: Teacher access required"}), 401
    report = WelfareReport.query.filter_by(id=id, created_by=current_user_id, deleted_at=None).first()
    if not report:
        return jsonify({"message": "Welfare Report not found or not authorized"}), 404
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
@jwt_required()
def delete_welfare_report(id):
    """Soft-delete a welfare report (teacher only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'teacher':
        return jsonify({"message": "Unauthorized: Teacher access required"}), 401
    report = WelfareReport.query.filter_by(id=id, created_by=current_user_id, deleted_at=None).first()
    if not report:
        return jsonify({"message": "Welfare Report not found or not authorized"}), 404
    try:
        report.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Welfare Report soft-deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to soft-delete welfare report", "error": str(e)}), 500

# --- Teacher Routes ---

@api_bp.route('/teachers', methods=['GET'])
@jwt_required()
def get_teachers():
    """Retrieve teachers (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    teachers = User.query.filter_by(role='teacher', deleted_at=None).options(joinedload(User.teacher).joinedload(Teacher.subjects)).all()
    teacher_data = [
        {
            "id": teacher.id,
            "username": teacher.username,
            "email": teacher.email,
            "subjects": [subject.name for subject in teacher.teacher.subjects if not is_soft_deleted(subject)] if teacher.teacher else [],
            "managed_class": {"id": cls.id, "name": cls.name} if (cls := SchoolClass.query.filter_by(class_teacher_id=teacher.id, deleted_at=None).first()) else None
        }
        for teacher in teachers
    ]
    return jsonify(teacher_data)

#get teacher id for teacher exams page
@api_bp.route('/me/teacher', methods=['GET'])
@jwt_required()
def get_current_teacher():
    """Retrieve the authenticated teacher's profile (teacher only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'teacher':
        return jsonify({"message": "Unauthorized: Teacher access required"}), 401

    teacher = Teacher.query.filter_by(user_id=current_user_id, deleted_at=None).first()
    if not teacher:
        return jsonify({"message": "Teacher profile not found"}), 404

    teacher_data = {
        "id": teacher.id,
        "user_id": teacher.user_id,
        "username": user.username,
        "email": user.email,
        # Add more fields if needed, e.g., subjects or classes
    }
    return jsonify(teacher_data), 200

@api_bp.route('/teachers/<int:id>', methods=['GET'])
@jwt_required()
def get_teacher_by_id(id):
    """Retrieve a teacher (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    teacher = User.query.filter_by(id=id, role='teacher', deleted_at=None).first()
    if teacher:
        return jsonify(UserSchema().dump(teacher))
    return jsonify({"message": "Teacher not found"}), 404

@api_bp.route('/teachers', methods=['POST'])
@jwt_required()
def create_teacher():
    """Create a teacher (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
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
                    db.session.add(teacher_subject)
        db.session.commit()
        return jsonify(UserSchema().dump(new_user)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create teacher", "error": str(e)}), 500

@api_bp.route('/teachers/<int:id>', methods=['PUT'])
@jwt_required()
def update_teacher(id):
    """Update a teacher (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
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
                    db.session.add(teacher_subject)
        db.session.commit()
        return jsonify(UserSchema().dump(teacher))
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update teacher", "error": str(e)}), 500

@api_bp.route('/teachers/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_teacher(id):
    """Soft-delete a teacher (admin only)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"message": "Unauthorized: Admin access required"}), 401
    teacher = User.query.filter_by(id=id, role='teacher', deleted_at=None).first()
    if not teacher:
        return jsonify({"message": "Teacher not found"}), 404
    try:
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
@jwt_required()
def get_forms():
    """Retrieve forms (teacher or admin)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Unauthorized: Teacher or Admin access required"}), 401
    forms = Form.query.filter(Form.deleted_at.is_(None)).all()
    return jsonify([{"id": f.id, "name": f.name} for f in forms])