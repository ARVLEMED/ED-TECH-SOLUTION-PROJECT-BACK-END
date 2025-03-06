from app import db, create_app
from app.models import User, Teacher, Form, SchoolClass, Student, Subject, Exam, Result, WelfareReport, TeacherSubject
import random
from datetime import datetime

# Create the Flask app
app = create_app()

def clear_existing_data():
    print("Clearing existing data...")
    with app.app_context():
        # Clear data in reverse dependency order to avoid foreign key violations
        db.session.query(WelfareReport).delete()
        db.session.query(Result).delete()
        db.session.query(TeacherSubject).delete()
        # Clear student_subject relationships
        for student in Student.query.all():
            student.subjects = []
        db.session.commit()
        db.session.query(Student).delete()
        db.session.query(SchoolClass).delete()
        db.session.query(Teacher).delete()
        db.session.query(Subject).delete()
        db.session.query(Exam).delete()
        db.session.query(Form).delete()
        db.session.query(User).delete()
        db.session.commit()
    print("Existing data cleared.")

def seed_forms():
    print("Seeding forms...")
    with app.app_context():
        forms = [
            Form(name="Form 1", deleted_at=None),
            Form(name="Form 2", deleted_at=None),
            Form(name="Form 3", deleted_at=None),
            Form(name="Form 4", deleted_at=None),
        ]
        db.session.bulk_save_objects(forms)
        db.session.commit()
    print("Forms seeded.")

def seed_users():
    print("Seeding users...")
    with app.app_context():
        users = [
            User(username="admin", email="admin@example.com", password="adminpassword", role="admin", deleted_at=None),
            *[User(username=f"parent{i}", email=f"parent{i}@example.com", password="parentpassword", role="parent", deleted_at=None) for i in range(1, 11)],
            *[User(username=f"teacher{i}", email=f"teacher{i}@example.com", password="teacherpassword", role="teacher", deleted_at=None) for i in range(1, 6)],
        ]
        db.session.bulk_save_objects(users)
        db.session.commit()
    print("Users seeded.")

def seed_teachers():
    print("Seeding teachers...")
    with app.app_context():
        teacher_users = User.query.filter_by(role='teacher').all()
        if not teacher_users:
            raise ValueError("No teacher users found.")
        teachers = [Teacher(user_id=user.id, deleted_at=None) for user in teacher_users]
        db.session.bulk_save_objects(teachers)
        db.session.commit()
    print("Teachers seeded.")

def seed_subjects():
    print("Seeding subjects...")
    with app.app_context():
        subjects = [
            Subject(name="Mathematics", deleted_at=None),
            Subject(name="Physics", deleted_at=None),
            Subject(name="Chemistry", deleted_at=None),
            Subject(name="Biology", deleted_at=None),
            Subject(name="English", deleted_at=None),
            Subject(name="History", deleted_at=None),
            Subject(name="Geography", deleted_at=None),
            Subject(name="Computer Science", deleted_at=None),
        ]
        db.session.bulk_save_objects(subjects)
        db.session.commit()
    print("Subjects seeded.")

def seed_classes():
    print("Seeding classes...")
    with app.app_context():
        forms = Form.query.all()
        teachers = User.query.filter_by(role='teacher').all()
        if not forms or not teachers:
            raise ValueError("Forms or teachers not seeded.")
        
        classes = [
            SchoolClass(name=f"Form {form.name.split()[1]} {direction}", form_id=form.id, class_teacher_id=random.choice(teachers).id, deleted_at=None)
            for form in forms
            for direction in ["North", "East", "South", "West"]
        ]
        db.session.bulk_save_objects(classes)
        db.session.commit()
    print("Classes seeded.")

def seed_students():
    print("Seeding students...")
    with app.app_context():
        classes = SchoolClass.query.all()
        parents = User.query.filter_by(role='parent').all()
        if not classes or not parents:
            raise ValueError("Classes or parents not seeded.")
        
        students = [
            Student(
                name=f"Student {i}",
                school_class_id=random.choice(classes).id,
                admission_number=f"ADM{i:04d}",
                parent_id=random.choice(parents).id,
                deleted_at=None
            )
            for i in range(1, 51)  # Increased to 50 students
        ]
        db.session.bulk_save_objects(students)
        db.session.commit()
    print("Students seeded.")

def seed_student_subjects():
    print("Seeding student-subject relationships...")
    with app.app_context():
        students = Student.query.all()
        subjects = Subject.query.all()
        if not students or not subjects:
            raise ValueError("Students or subjects not seeded.")
        
        for student in students:
            if len(subjects) < 3:
                raise ValueError("Not enough subjects to assign to students.")
            sampled_subjects = random.sample(subjects, random.randint(3, min(5, len(subjects))))
            for subject in sampled_subjects:
                student.subjects.append(subject)
        db.session.commit()
    print("Student-subject relationships seeded.")

def seed_exams():
    print("Seeding exams...")
    with app.app_context():
        forms = Form.query.all()
        if not forms:
            raise ValueError("Forms not seeded.")
        
        exam_types = ["CAT 1", "Midterm", "End Term"]
        terms = ["Term 1", "Term 2", "Term 3"]
        years = [2023, 2024, 2025]
        
        exams = []
        for form in forms:
            for term in terms:
                for exam_type in exam_types:
                    for year in years:
                        month = random.randint(1, 12)
                        day = random.randint(1, 28)
                        exam_date = datetime(year, month, day)
                        
                        exams.append(Exam(
                            name=exam_type,
                            form_id=form.id,
                            term=term,
                            date=exam_date,
                            deleted_at=None
                        ))
        
        db.session.bulk_save_objects(exams)
        db.session.commit()
    print("Exams seeded.")

def seed_teacher_subjects():
    print("Seeding teacher-subject relationships...")
    with app.app_context():
        teachers = Teacher.query.all()
        subjects = Subject.query.all()
        if not teachers or not subjects:
            raise ValueError("Teachers or subjects not seeded.")
        
        teacher_subjects = []
        for teacher in teachers:
            sampled_subjects = random.sample(subjects, random.randint(2, 4))
            for subject in sampled_subjects:
                teacher_subjects.append(TeacherSubject(teacher_id=teacher.id, subject_id=subject.id, deleted_at=None))
        db.session.bulk_save_objects(teacher_subjects)
        db.session.commit()
    print("Teacher-subject relationships seeded.")

def seed_results():
    print("Seeding results...")
    with app.app_context():
        students = Student.query.all()
        subjects = Subject.query.all()
        exams = Exam.query.all()
        teachers = Teacher.query.all()
        teacher_subjects = TeacherSubject.query.all()
        
        if not students or not subjects or not exams or not teachers or not teacher_subjects:
            raise ValueError("Students, subjects, exams, teachers, or teacher_subjects not seeded.")
        
        # Create a mapping of subject_id to teacher_id for efficiency
        subject_to_teacher = {ts.subject_id: ts.teacher_id for ts in teacher_subjects}
        
        results = []
        for student in students:
            student_form_id = student.school_class.form_id
            form_exams = [e for e in exams if e.form_id == student_form_id]
            sampled_exams = random.sample(form_exams, min(3, len(form_exams)))
            for exam in sampled_exams:
                sampled_subjects = random.sample(subjects, random.randint(3, 5))
                for subject in sampled_subjects:
                    # Assign teacher_id based on TeacherSubject relationship, fallback to random teacher
                    teacher_id = subject_to_teacher.get(subject.id, random.choice(teachers).id)
                    results.append(Result(
                        student_id=student.id,
                        subject_id=subject.id,
                        exam_id=exam.id,
                        teacher_id=teacher_id,  # New field
                        score=random.uniform(0, 100),
                        deleted_at=None
                    ))
        db.session.bulk_save_objects(results)
        db.session.commit()
    print("Results seeded.")

def seed_welfare_reports():
    print("Seeding welfare reports...")
    with app.app_context():
        students = Student.query.all()
        if not students:
            raise ValueError("Students not seeded.")
        
        categories = ["Health", "Discipline", "Academic"]
        reports = [
            WelfareReport(
                student_id=student.id,
                remarks=f"Report for {student.name} - {category} issue",
                category=category,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                deleted_at=None
            )
            for student in random.sample(students, 20)  # 20 reports
            for category in random.sample(categories, random.randint(1, 2))  # 1-2 reports per student
        ]
        db.session.bulk_save_objects(reports)
        db.session.commit()
    print("Welfare reports seeded.")

def seed_data():
    clear_existing_data()
    seed_forms()
    seed_users()
    seed_teachers()
    seed_subjects()
    seed_classes()
    seed_students()
    seed_student_subjects()
    seed_exams()
    seed_teacher_subjects()  # Moved before seed_results
    seed_results()
    seed_welfare_reports()

if __name__ == "__main__":
    seed_data()