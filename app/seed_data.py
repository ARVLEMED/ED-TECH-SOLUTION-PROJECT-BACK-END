from app import db
from datetime import datetime
from app.models import User, Student, Class, Subject, Exam, Result, WelfareReport, Teacher, TeacherSubject

# Helper function to add mock data
def seed_data():
    # Check if users already exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', password='password', role='admin')

    parent = User.query.filter_by(username='parent').first()
    if not parent:
        parent = User(username='parent', email='parent@example.com', password='password', role='parent')

    class_teacher = User.query.filter_by(username='class_teacher').first()
    if not class_teacher:
        class_teacher = User(username='class_teacher', email='class_teacher@example.com', password='password', role='class teacher')

    subject_teacher = User.query.filter_by(username='subject_teacher').first()
    if not subject_teacher:
        subject_teacher = User(username='subject_teacher', email='subject_teacher@example.com', password='password', role='subject teacher')

    # Add users to the session if they don't exist already
    db.session.add(admin)
    db.session.add(parent)
    db.session.add(class_teacher)
    db.session.add(subject_teacher)
    
    # Commit so that the users get their IDs
    db.session.commit()

    # Create a class
    class_1 = Class.query.filter_by(name='Class 1').first()
    if not class_1:
        class_1 = Class(name='Class 1', class_teacher_id=class_teacher.id)
        db.session.add(class_1)
        db.session.commit()  # Commit to get class ID

    # Create subjects
    subject_1 = Subject.query.filter_by(subject_name='Mathematics').first()
    if not subject_1:
        subject_1 = Subject(subject_name='Mathematics', exam_id=1)  # We will create exam after subjects
        db.session.add(subject_1)

    subject_2 = Subject.query.filter_by(subject_name='Science').first()
    if not subject_2:
        subject_2 = Subject(subject_name='Science', exam_id=1)

    db.session.add(subject_2)
    db.session.commit()  # Commit to get subject IDs

    # Create an exam
    exam_1 = Exam.query.filter_by(name='Mid Term Exam').first()
    if not exam_1:
        exam_1 = Exam(name='Mid Term Exam', term='First Term', created_at=datetime.utcnow())
        db.session.add(exam_1)
        db.session.commit()  # Commit to get exam ID
    
    # Update the subjects with the correct exam ID
    subject_1.exam_id = exam_1.id
    subject_2.exam_id = exam_1.id

    # Commit the changes to update the subjects with the exam ID
    db.session.commit()

    # Create students
    student_1 = Student.query.filter_by(admission_number='S001').first()
    if not student_1:
        student_1 = Student(name='John Doe', class_id=class_1.id, parent_id=parent.id, admission_number='S001')
        db.session.add(student_1)
    student_2 = Student.query.filter_by(admission_number='S002').first()
    if not student_2:
        student_2 = Student(name='Jane Doe', class_id=class_1.id, parent_id=parent.id, admission_number='S002')

    db.session.add(student_2)
    db.session.commit()  # Commit to get student IDs

    # Create results
    result_1 = Result.query.filter_by(student_id=student_1.id, subject_id=subject_1.id).first()
    if not result_1:
        result_1 = Result(student_id=student_1.id, subject_id=subject_1.id, exam_id=exam_1.id, score=95.0, teacher_id=subject_teacher.id)
        db.session.add(result_1)

    result_2 = Result.query.filter_by(student_id=student_2.id, subject_id=subject_2.id).first()
    if not result_2:
        result_2 = Result(student_id=student_2.id, subject_id=subject_2.id, exam_id=exam_1.id, score=85.0, teacher_id=subject_teacher.id)

    db.session.add(result_2)
    db.session.commit()  # Commit results to ensure no integrity errors

    # Create welfare reports
    welfare_report_1 = WelfareReport.query.filter_by(student_id=student_1.id).first()
    if not welfare_report_1:
        welfare_report_1 = WelfareReport(student_id=student_1.id, teacher_id=class_teacher.id, remarks='Good performance', date=datetime.utcnow())
        db.session.add(welfare_report_1)

    welfare_report_2 = WelfareReport.query.filter_by(student_id=student_2.id).first()
    if not welfare_report_2:
        welfare_report_2 = WelfareReport(student_id=student_2.id, teacher_id=class_teacher.id, remarks='Needs improvement in science', date=datetime.utcnow())

    db.session.add(welfare_report_2)

    # Commit welfare reports
    db.session.commit()

    # Create teacher and teacher-subject relationships
    teacher_1 = Teacher.query.filter_by(user_id=subject_teacher.id).first()
    if not teacher_1:
        teacher_1 = Teacher(user_id=subject_teacher.id)
        db.session.add(teacher_1)
        db.session.commit()  # Commit to get teacher ID

    teacher_subject_1 = TeacherSubject.query.filter_by(teacher_id=teacher_1.id, subject_id=subject_1.id).first()
    if not teacher_subject_1:
        teacher_subject_1 = TeacherSubject(teacher_id=teacher_1.id, subject_id=subject_1.id)
        db.session.add(teacher_subject_1)

    teacher_subject_2 = TeacherSubject.query.filter_by(teacher_id=teacher_1.id, subject_id=subject_2.id).first()
    if not teacher_subject_2:
        teacher_subject_2 = TeacherSubject(teacher_id=teacher_1.id, subject_id=subject_2.id)

    db.session.add(teacher_subject_2)
    
    # Commit all changes
    db.session.commit()
    print("Mock data seeded!")