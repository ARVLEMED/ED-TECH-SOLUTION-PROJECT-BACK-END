from faker import Faker
from datetime import datetime
from app import create_app, db  # Import create_app and db
from app.models import User, Student, SchoolClass, Subject, Exam, Result, WelfareReport, Teacher, TeacherSubject, StudentSubject

# Initialize Faker
fake = Faker()

# Create the Flask app
app = create_app()  # Use create_app to initialize the app

# Create an application context
with app.app_context():
    # Clear existing data
    print("Clearing existing data...")
    db.session.query(StudentSubject).delete()  # Clear StudentSubject table
    db.session.query(TeacherSubject).delete()
    db.session.query(Teacher).delete()
    db.session.query(WelfareReport).delete()
    db.session.query(Result).delete()
    db.session.query(Subject).delete()
    db.session.query(Exam).delete()
    db.session.query(Student).delete()
    db.session.query(SchoolClass).delete()
    db.session.query(User).delete()
    db.session.commit()
    print("Existing data cleared.")

    # Seed Users
    print("Seeding users...")
    users = []
    for _ in range(10):
        user = User(
            username=fake.unique.user_name(),
            email=fake.unique.email(),
            password=fake.password(),
            role=fake.random_element(elements=("admin", "teacher", "parent")),
        )
        users.append(user)
        db.session.add(user)
    db.session.commit()
    print("Users seeded.")

    # Seed Teachers
    print("Seeding teachers...")
    teachers = []
    for user in users:
        if user.role == "teacher":
            teacher = Teacher(user_id=user.id)
            teachers.append(teacher)
            db.session.add(teacher)
    db.session.commit()
    print("Teachers seeded.")

    # Seed Subjects
    print("Seeding subjects...")
    subjects = []
    for _ in range(5):
        subject = Subject(subject_name=fake.word())
        subjects.append(subject)
        db.session.add(subject)
    db.session.commit()
    print("Subjects seeded.")

    # Seed Teacher-Subject Relationships
    print("Seeding teacher-subject relationships...")
    for teacher in teachers:
        assigned_subjects = set()  # Track assigned subjects for this teacher
        for _ in range(2):  # Each teacher teaches 2 subjects
            subject_id = fake.random_element(elements=[s.id for s in subjects])
            while subject_id in assigned_subjects:  # Ensure the subject is unique for this teacher
                subject_id = fake.random_element(elements=[s.id for s in subjects])
            assigned_subjects.add(subject_id)

            teacher_subject = TeacherSubject(
                teacher_id=teacher.id,
                subject_id=subject_id,
            )
            db.session.add(teacher_subject)
    db.session.commit()
    print("Teacher-subject relationships seeded.")

    # Seed Classes
    print("Seeding classes...")
    classes = []
    for _ in range(5):
        school_class = SchoolClass(
            name=fake.random_element(elements=("Math", "Science", "History", "English", "Art")),
            class_teacher_id=fake.random_element(elements=[t.id for t in teachers]),
        )
        classes.append(school_class)
        db.session.add(school_class)
    db.session.commit()
    print("Classes seeded.")

    # Seed Students
    print("Seeding students...")
    students = []
    for _ in range(20):
        student = Student(
            name=fake.name(),
            class_id=fake.random_element(elements=[c.id for c in classes]),
            parent_id=fake.random_element(elements=[u.id for u in users if u.role == "parent"]),
            admission_number=fake.unique.bothify("ADM#####"),
        )
        students.append(student)
        db.session.add(student)
    db.session.commit()
    print("Students seeded.")

    # Seed Student-Subject Relationships
    print("Seeding student-subject relationships...")
    for student in students:
        assigned_subjects = set()  # Track assigned subjects for this student
        for _ in range(3):  # Each student takes 3 subjects
            subject_id = fake.random_element(elements=[s.id for s in subjects])
            while subject_id in assigned_subjects:  # Ensure the subject is unique for this student
                subject_id = fake.random_element(elements=[s.id for s in subjects])
            assigned_subjects.add(subject_id)

            student_subject = StudentSubject(
                student_id=student.id,
                subject_id=subject_id,
            )
            db.session.add(student_subject)
    db.session.commit()
    print("Student-subject relationships seeded.")

    # Seed Exams
    print("Seeding exams...")
    exams = []
    for _ in range(3):
        exam = Exam(
            name=fake.random_element(elements=("Midterm", "Final", "Quiz")),
            term=fake.random_element(elements=("Term 1", "Term 2", "Term 3")),
        )
        exams.append(exam)
        db.session.add(exam)
    db.session.commit()
    print("Exams seeded.")

    # Seed Results
    print("Seeding results...")
    for student in students:
        # Get the subjects the student is enrolled in
        student_subjects = StudentSubject.query.filter_by(student_id=student.id).all()
        for exam in exams:
            for student_subject in student_subjects:
                result = Result(
                    student_id=student.id,
                    subject_id=student_subject.subject_id,
                    exam_id=exam.id,
                    score=fake.random_int(min=0, max=100),
                    teacher_id=fake.random_element(elements=[t.id for t in teachers]),
                )
                db.session.add(result)
    db.session.commit()
    print("Results seeded.")

    # Seed Welfare Reports
    print("Seeding welfare reports...")
    for student in students:
        for _ in range(3):  # Add 3 welfare reports per student
            welfare_report = WelfareReport(
                student_id=student.id,
                teacher_id=fake.random_element(elements=[t.id for t in teachers]),
                remarks=fake.sentence(),
                category=fake.random_element(elements=("Discipline", "Academic", "Health")),  # Add category
                date=datetime.utcnow(),  # Add date
            )
            db.session.add(welfare_report)
    db.session.commit()
    print("Welfare reports seeded.")

    print("Database seeding completed successfully!")