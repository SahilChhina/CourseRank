"""
Run this script once to populate the database with starter Western University course data.
Usage: python -m app.seed
"""
from app.database import SessionLocal, engine
from app.models import Course, GradingComponent, Review
from app.models.sentiment import CourseScore, SentimentResult

COURSES = [
    {
        "course_code": "CS 2210",
        "course_name": "Data Structures and Algorithms",
        "department": "Computer Science",
        "description": "Introduction to data structures and algorithms. Topics include arrays, linked lists, stacks, queues, trees, heaps, hash tables, sorting, and graph algorithms.",
        "prerequisites": ["CS 1027"],
        "antirequisites": ["SE 2205"],
        "grading": [
            ("Assignments", 30, 0.95),
            ("Midterm Exam", 25, 0.95),
            ("Final Exam", 40, 0.95),
            ("Participation/Labs", 5, 0.90),
        ],
        "scores": (7.8, 8.2, 6.9, 7.1, 8.5, 0.82,
                   "Difficulty driven by challenging assignments and high exam weight. Usefulness is high due to interview relevance."),
        "sentiment": ("mixed-positive", 0.62,
                      ["useful for technical interviews", "good foundational course", "engaging assignments"],
                      ["heavy workload", "fast pacing", "exams are challenging"],
                      [],
                      "Students generally find CS 2210 demanding but rewarding. Most describe it as essential for software engineering careers, though the pace can be intense.",
                      0.78),
        "reviews": [
            ("Fall 2024", 8, 9, 7, 7, 6, 9, "Assignments take a long time but are very useful for understanding the material. Exams are tough — start studying early.", True),
            ("Winter 2024", 7, 8, 6, 6, 7, 8, "Important course for CS students. The tree and graph sections are difficult. Office hours help a lot.", True),
            ("Fall 2023", 9, 9, 8, 8, 6, 9, "One of the harder second-year courses. Very relevant for internships.", True),
        ],
    },
    {
        "course_code": "CS 2211",
        "course_name": "Software Tools and Systems Programming",
        "department": "Computer Science",
        "description": "Introduction to Unix/Linux operating systems, shell scripting, C programming, system calls, and low-level programming concepts.",
        "prerequisites": ["CS 1027"],
        "antirequisites": [],
        "grading": [
            ("Labs", 25, 0.92),
            ("Assignments", 30, 0.92),
            ("Midterm Exam", 20, 0.92),
            ("Final Exam", 25, 0.92),
        ],
        "scores": (7.2, 7.5, 7.4, 7.3, 8.0, 0.80,
                   "Moderate difficulty. Lab-heavy with strong practical focus on Unix and C programming."),
        "sentiment": ("positive", 0.70,
                      ["practical skills", "useful for industry", "good intro to systems programming"],
                      ["C syntax is tricky at first", "labs can be time-consuming"],
                      [],
                      "Students appreciate the practical focus on Unix and C. Many find the lab work manageable once they get the hang of C syntax.",
                      0.74),
        "reviews": [
            ("Fall 2024", 7, 7, 5, 7, 7, 8, "Very hands-on. Labs are reasonable if you start early. C takes getting used to but it's a great skill.", True),
            ("Winter 2024", 6, 7, 5, 8, 8, 8, "Good practical course. The shell scripting section is really useful for future internships.", True),
        ],
    },
    {
        "course_code": "CS 3305",
        "course_name": "Operating Systems",
        "department": "Computer Science",
        "description": "Principles and design of operating systems. Topics include processes, threads, scheduling, memory management, file systems, and concurrency.",
        "prerequisites": ["CS 2211", "CS 2210"],
        "antirequisites": [],
        "grading": [
            ("Assignments", 35, 0.93),
            ("Midterm Exam", 25, 0.93),
            ("Final Exam", 35, 0.93),
            ("Participation", 5, 0.85),
        ],
        "scores": (8.5, 8.8, 7.0, 7.2, 8.3, 0.79,
                   "High difficulty. Concurrency and memory management concepts are notoriously tricky. Assignments are complex."),
        "sentiment": ("mixed", 0.52,
                      ["deep understanding of systems", "great for systems roles", "challenging and rewarding"],
                      ["very hard assignments", "concurrency is confusing", "steep learning curve"],
                      ["content is interesting but dense"],
                      "OS is consistently rated as one of the most difficult CS courses. Students who push through it report high satisfaction.",
                      0.75),
        "reviews": [
            ("Fall 2024", 9, 9, 10, 6, 7, 9, "Hardest course I've taken. Assignments on threading and memory management are brutal but you learn a ton.", True),
            ("Winter 2024", 8, 8, 8, 7, 7, 8, "Dense material. If you want to work in systems or backend, this course is worth the pain.", True),
        ],
    },
    {
        "course_code": "CS 3350",
        "course_name": "Machine Learning",
        "department": "Computer Science",
        "description": "Fundamentals of machine learning including supervised and unsupervised learning, neural networks, model evaluation, and practical implementation.",
        "prerequisites": ["CS 2210", "STATS 2244"],
        "antirequisites": [],
        "grading": [
            ("Assignments", 40, 0.94),
            ("Midterm Exam", 20, 0.94),
            ("Final Project", 25, 0.94),
            ("Final Exam", 15, 0.94),
        ],
        "scores": (7.0, 7.8, 7.5, 7.8, 9.2, 0.85,
                   "High usefulness score. Project-heavy with strong real-world application. Math background required."),
        "sentiment": ("positive", 0.74,
                      ["very useful for careers in AI/data", "interesting projects", "hands-on learning"],
                      ["requires strong math background", "assignments are time-consuming"],
                      [],
                      "Students highly value CS 3350 for career preparation. The project component is engaging, and most find it worth the workload.",
                      0.80),
        "reviews": [
            ("Fall 2024", 7, 8, 8, 8, 8, 9, "One of the most valuable CS courses. The final project is really fun if you pick a good topic.", True),
            ("Winter 2024", 6, 8, 7, 7, 8, 9, "Great course. You need a decent understanding of linear algebra and stats going in.", True),
        ],
    },
    {
        "course_code": "CS 3357",
        "course_name": "Computer Networks",
        "department": "Computer Science",
        "description": "Fundamentals of computer networking including the TCP/IP stack, routing protocols, network security, and socket programming.",
        "prerequisites": ["CS 2211"],
        "antirequisites": [],
        "grading": [
            ("Labs/Assignments", 40, 0.91),
            ("Midterm Exam", 25, 0.91),
            ("Final Exam", 35, 0.91),
        ],
        "scores": (6.8, 7.0, 7.2, 7.5, 8.0, 0.77,
                   "Moderate difficulty. Lab-heavy with practical socket programming components."),
        "sentiment": ("mixed-positive", 0.63,
                      ["useful for backend and infrastructure roles", "socket programming labs are great"],
                      ["lots of memorization for protocols", "exams cover a lot of material"],
                      [],
                      "Students find Computer Networks practical and useful for industry, though exam coverage is broad.",
                      0.72),
        "reviews": [
            ("Fall 2024", 7, 7, 6, 7, 7, 8, "Really enjoyed the socket programming labs. Networking concepts can feel like memorization at times.", True),
        ],
    },
    {
        "course_code": "SE 2203",
        "course_name": "Software Design",
        "department": "Software Engineering",
        "description": "Software design principles and patterns including object-oriented design, UML, design patterns, and architectural styles.",
        "prerequisites": ["CS 1027"],
        "antirequisites": [],
        "grading": [
            ("Group Project", 40, 0.90),
            ("Assignments", 25, 0.90),
            ("Midterm Exam", 15, 0.90),
            ("Final Exam", 20, 0.90),
        ],
        "scores": (6.2, 6.5, 7.8, 7.9, 7.6, 0.76,
                   "Moderate difficulty. Heavy group project component. Organization rated well by students."),
        "sentiment": ("positive", 0.68,
                      ["group project teaches real teamwork", "design patterns are very useful"],
                      ["group work can be frustrating if teammates are unresponsive", "UML diagrams feel tedious"],
                      [],
                      "Students appreciate the practical software design skills but note group project coordination can be challenging.",
                      0.70),
        "reviews": [
            ("Fall 2024", 6, 7, 6, 8, 8, 8, "Good course overall. The project is the main focus and it teaches you a lot about working in teams.", True),
            ("Winter 2024", 5, 6, 5, 8, 8, 7, "UML and design patterns are useful concepts but the course can feel slow at times.", True),
        ],
    },
    {
        "course_code": "STATS 2244",
        "course_name": "Statistics for Science",
        "department": "Statistical and Actuarial Sciences",
        "description": "Introduction to statistical methods for science students. Topics include probability, distributions, hypothesis testing, confidence intervals, and regression.",
        "prerequisites": ["MATH 1229"],
        "antirequisites": ["STATS 2035", "STATS 2141"],
        "grading": [
            ("Assignments", 20, 0.93),
            ("Labs", 15, 0.93),
            ("Midterm Exam", 30, 0.93),
            ("Final Exam", 35, 0.93),
        ],
        "scores": (6.5, 6.0, 7.0, 7.2, 7.5, 0.78,
                   "Moderate difficulty. Exam-heavy course. Foundational for ML and data science courses."),
        "sentiment": ("mixed-positive", 0.60,
                      ["essential for data science and ML", "good foundation in probability"],
                      ["exam-heavy", "concepts can feel abstract", "final exam covers a lot"],
                      [],
                      "Students recognize STATS 2244 as important groundwork for future courses but find it dry and exam-focused.",
                      0.72),
        "reviews": [
            ("Fall 2024", 6, 6, 4, 7, 7, 7, "Important course but the material is dry. The final is a significant portion of the grade so don't slack.", True),
        ],
    },
    {
        "course_code": "MATH 2155",
        "course_name": "Methods of Calculus",
        "department": "Mathematics",
        "description": "Multivariable calculus including partial derivatives, multiple integrals, vector calculus, line and surface integrals, and theorems of Green, Stokes, and Gauss.",
        "prerequisites": ["MATH 1229"],
        "antirequisites": ["MATH 2156", "MATH 2276"],
        "grading": [
            ("Assignments", 15, 0.94),
            ("Midterm 1", 20, 0.94),
            ("Midterm 2", 20, 0.94),
            ("Final Exam", 45, 0.94),
        ],
        "scores": (8.0, 7.2, 7.0, 7.0, 7.0, 0.80,
                   "High difficulty, exam-heavy. Final exam is 45% of the grade. Strong calculus foundation needed."),
        "sentiment": ("mixed", 0.50,
                      ["foundational for physics and engineering", "profs are knowledgeable"],
                      ["very exam-heavy", "concepts are abstract", "final is very challenging"],
                      [],
                      "MATH 2155 is considered one of the more challenging required math courses. Students recommend consistent practice throughout the term.",
                      0.73),
        "reviews": [
            ("Fall 2024", 8, 7, 4, 7, 7, 7, "Hard course. The final exam is worth 45% which is stressful. Practice problems are essential.", True),
            ("Winter 2024", 9, 7, 4, 6, 6, 7, "If you're not strong in calculus this will be rough. Lecture attendance is important.", True),
        ],
    },
    {
        "course_code": "ECO 1021",
        "course_name": "Principles of Microeconomics",
        "department": "Economics",
        "description": "Introduction to microeconomic principles including supply and demand, consumer theory, firm behaviour, market structures, and welfare economics.",
        "prerequisites": [],
        "antirequisites": ["ECO 1020"],
        "grading": [
            ("Online Quizzes", 15, 0.92),
            ("Midterm Exam", 30, 0.92),
            ("Final Exam", 45, 0.92),
            ("Participation", 10, 0.85),
        ],
        "scores": (5.5, 5.0, 6.5, 7.0, 7.0, 0.76,
                   "Relatively accessible introductory course. Exam-heavy but content is not highly technical."),
        "sentiment": ("positive", 0.72,
                      ["accessible introduction to economics", "useful for business understanding", "quizzes keep you on track"],
                      ["final exam is a large portion", "some concepts feel repetitive"],
                      [],
                      "Most students find ECO 1021 manageable and a good general elective. Regular studying for the large final exam is key.",
                      0.75),
        "reviews": [
            ("Fall 2024", 5, 5, 3, 7, 7, 7, "Good elective. Not too hard if you keep up with readings. The final is worth a lot so don't cram.", True),
        ],
    },
    {
        "course_code": "CS 3342",
        "course_name": "Organization of Programming Languages",
        "department": "Computer Science",
        "description": "Study of programming language design and implementation including syntax, semantics, type systems, functional programming, logic programming, and language paradigms.",
        "prerequisites": ["CS 2210"],
        "antirequisites": [],
        "grading": [
            ("Assignments", 35, 0.91),
            ("Midterm Exam", 25, 0.91),
            ("Final Exam", 35, 0.91),
            ("Participation", 5, 0.85),
        ],
        "scores": (7.5, 7.0, 7.3, 7.5, 7.8, 0.77,
                   "Moderate-high difficulty. Requires abstract thinking for type systems and functional programming."),
        "sentiment": ("mixed-positive", 0.61,
                      ["eye-opening for programming paradigms", "functional programming is very useful", "broadens how you think about code"],
                      ["type theory is abstract", "assignments require deep thinking"],
                      [],
                      "Students who embrace the abstract nature of the course find it very rewarding. Functional programming concepts are frequently mentioned as valuable.",
                      0.70),
        "reviews": [
            ("Fall 2024", 7, 7, 6, 7, 7, 8, "This course changed how I think about programming. The Haskell section was tough but fascinating.", True),
        ],
    },
]


def seed():
    from app.models import Course, GradingComponent, Review
    from app.models.sentiment import CourseScore, SentimentResult

    db = SessionLocal()
    try:
        if db.query(Course).count() > 0:
            print("Database already seeded. Skipping.")
            return

        for data in COURSES:
            course = Course(
                course_code=data["course_code"],
                course_name=data["course_name"],
                department=data["department"],
                description=data["description"],
                prerequisites=data["prerequisites"],
                antirequisites=data["antirequisites"],
            )
            db.add(course)
            db.flush()

            for name, weight, confidence in data["grading"]:
                db.add(GradingComponent(
                    course_id=course.id,
                    component_name=name,
                    weight=weight,
                    confidence_score=confidence,
                    source_document="seed_data",
                ))

            diff, work, org, fair, use, conf, explanation = data["scores"]
            db.add(CourseScore(
                course_id=course.id,
                difficulty_score=diff,
                workload_score=work,
                organization_score=org,
                assessment_fairness_score=fair,
                usefulness_score=use,
                confidence_score=conf,
                explanation=explanation,
            ))

            sentiment_label, s_score, pos, neg, neutral, summary, s_conf = data["sentiment"]
            db.add(SentimentResult(
                course_id=course.id,
                overall_sentiment=sentiment_label,
                sentiment_score=s_score,
                positive_themes=pos,
                negative_themes=neg,
                neutral_themes=neutral,
                summary=summary,
                confidence_score=s_conf,
            ))

            for term, diff_r, work_r, hrs, org_r, fair_r, use_r, text, recommend in data["reviews"]:
                db.add(Review(
                    course_id=course.id,
                    term_taken=term,
                    difficulty_rating=diff_r,
                    workload_rating=work_r,
                    hours_per_week=hrs,
                    organization_rating=org_r,
                    assessment_fairness_rating=fair_r,
                    usefulness_rating=use_r,
                    review_text=text,
                    would_recommend=recommend,
                ))

        db.commit()
        print(f"Seeded {len(COURSES)} courses successfully.")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    from app.database import engine
    from app.models import Course  # noqa: ensure all models are imported before create_all
    from app.models.grading import GradingComponent
    from app.models.review import Review
    from app.models.sentiment import CourseScore, SentimentResult
    from app.database import Base

    Base.metadata.create_all(bind=engine)
    seed()
