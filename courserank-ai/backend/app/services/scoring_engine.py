"""
Recomputes CourseScore from all non-flagged reviews for a given course.

Formula (PRD §15.4, simplified for Phase 3 — no NLP signals yet):

  difficulty_score  = 0.70 * avg(difficulty_rating)
                    + 0.15 * hours_factor          (hours/week normalized to 10)
                    + 0.15 * exam_weight_factor     (from grading components)

  workload_score    = 0.50 * avg(workload_rating)
                    + 0.30 * hours_factor
                    + 0.20 * assignment_weight_factor

  organization_score        = avg(organization_rating)
  assessment_fairness_score = avg(assessment_fairness_rating)
  usefulness_score          = avg(usefulness_rating)

Confidence grows with review count and shrinks when ratings spread is high.
Scores are on a 1–10 scale.
"""
from sqlalchemy.orm import Session
from app.models.review import Review
from app.models.grading import GradingComponent
from app.models.sentiment import CourseScore


def recompute_scores(course_id: int, db: Session) -> CourseScore:
    reviews = (
        db.query(Review)
        .filter(Review.course_id == course_id, Review.is_flagged == False)
        .all()
    )

    grading = db.query(GradingComponent).filter(
        GradingComponent.course_id == course_id
    ).all()

    n = len(reviews)

    if n == 0:
        return _upsert_score(course_id, db, {
            "difficulty_score": None,
            "workload_score": None,
            "organization_score": None,
            "assessment_fairness_score": None,
            "usefulness_score": None,
            "confidence_score": 0.0,
            "explanation": "No reviews submitted yet.",
        })

    def avg(values):
        vals = [v for v in values if v is not None]
        return sum(vals) / len(vals) if vals else None

    avg_diff  = avg([r.difficulty_rating for r in reviews])
    avg_work  = avg([r.workload_rating for r in reviews])
    avg_org   = avg([r.organization_rating for r in reviews])
    avg_fair  = avg([r.assessment_fairness_rating for r in reviews])
    avg_use   = avg([r.usefulness_rating for r in reviews])
    avg_hours = avg([float(r.hours_per_week) for r in reviews if r.hours_per_week])

    # Normalize hours/week to a 1–10 scale (capped at 20 hrs → 10)
    hours_factor = min((avg_hours / 20) * 10, 10.0) if avg_hours else None

    # Grading weight factors (0–10 scale)
    exam_weight = sum(
        float(g.weight) for g in grading
        if any(k in g.component_name.lower() for k in ["exam", "midterm", "test", "final"])
    )
    assignment_weight = sum(
        float(g.weight) for g in grading
        if any(k in g.component_name.lower() for k in ["assignment", "homework", "project"])
    )
    exam_factor       = (exam_weight / 100) * 10
    assignment_factor = (assignment_weight / 100) * 10

    # Composite scores
    if avg_diff is not None:
        diff_score = (
            0.70 * avg_diff
            + 0.15 * (hours_factor if hours_factor else avg_diff)
            + 0.15 * exam_factor
        )
    else:
        diff_score = None

    if avg_work is not None:
        work_score = (
            0.50 * avg_work
            + 0.30 * (hours_factor if hours_factor else avg_work)
            + 0.20 * assignment_factor
        )
    else:
        work_score = None

    confidence = _confidence(n, reviews)

    explanation = _build_explanation(
        n, avg_diff, avg_work, avg_hours, exam_weight, assignment_weight
    )

    return _upsert_score(course_id, db, {
        "difficulty_score": round(diff_score, 2) if diff_score else None,
        "workload_score": round(work_score, 2) if work_score else None,
        "organization_score": round(avg_org, 2) if avg_org else None,
        "assessment_fairness_score": round(avg_fair, 2) if avg_fair else None,
        "usefulness_score": round(avg_use, 2) if avg_use else None,
        "confidence_score": confidence,
        "explanation": explanation,
    })


def _confidence(n: int, reviews: list) -> float:
    # Base confidence from review count
    if n >= 20:
        base = 0.90
    elif n >= 10:
        base = 0.75
    elif n >= 5:
        base = 0.60
    elif n >= 3:
        base = 0.45
    else:
        base = 0.25

    # Penalise high spread in difficulty ratings (suggests polarising course)
    diff_ratings = [r.difficulty_rating for r in reviews if r.difficulty_rating]
    if len(diff_ratings) >= 3:
        spread = max(diff_ratings) - min(diff_ratings)
        if spread >= 6:
            base -= 0.05

    return round(min(base, 1.0), 2)


def _build_explanation(n, avg_diff, avg_work, avg_hours, exam_weight, assignment_weight) -> str:
    parts = [f"Based on {n} student review{'s' if n != 1 else ''}."]

    if avg_diff is not None:
        level = "high" if avg_diff >= 7.5 else "moderate" if avg_diff >= 5 else "low"
        parts.append(f"Students rate difficulty as {level} (avg {avg_diff:.1f}/10).")

    if avg_work is not None:
        level = "heavy" if avg_work >= 7.5 else "moderate" if avg_work >= 5 else "light"
        parts.append(f"Workload is reported as {level} (avg {avg_work:.1f}/10).")

    if avg_hours:
        parts.append(f"Average reported time commitment: {avg_hours:.1f} hours/week.")

    if exam_weight >= 60:
        parts.append(f"Exam weight is high ({exam_weight:.0f}%), contributing to difficulty.")
    if assignment_weight >= 40:
        parts.append(f"Assignment weight is significant ({assignment_weight:.0f}%).")

    return " ".join(parts)


def _upsert_score(course_id: int, db: Session, fields: dict) -> CourseScore:
    score = db.query(CourseScore).filter(CourseScore.course_id == course_id).first()
    if score:
        for k, v in fields.items():
            setattr(score, k, v)
    else:
        score = CourseScore(course_id=course_id, **fields)
        db.add(score)
    db.flush()
    return score
