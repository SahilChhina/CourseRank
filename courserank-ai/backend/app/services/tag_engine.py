from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.grading import GradingComponent


def compute_tags(grading_components: list["GradingComponent"], review_texts: list[str] = []) -> list[str]:
    tags = []

    exam_weight = sum(
        float(c.weight) for c in grading_components
        if any(kw in c.component_name.lower() for kw in ["exam", "midterm", "test", "final"])
    )
    assignment_weight = sum(
        float(c.weight) for c in grading_components
        if any(kw in c.component_name.lower() for kw in ["assignment", "homework", "project"])
    )
    lab_weight = sum(
        float(c.weight) for c in grading_components
        if "lab" in c.component_name.lower()
    )
    participation_weight = sum(
        float(c.weight) for c in grading_components
        if any(kw in c.component_name.lower() for kw in ["participation", "attendance"])
    )

    if exam_weight >= 60:
        tags.append("exam-heavy")
    if assignment_weight >= 40:
        tags.append("assignment-heavy")
    if lab_weight >= 20:
        tags.append("lab-heavy")
    if participation_weight >= 15:
        tags.append("participation-heavy")

    combined_text = " ".join(review_texts).lower()
    if any(kw in combined_text for kw in ["coding", "programming", "code", "python", "java", "c++"]):
        tags.append("coding-heavy")
    if any(kw in combined_text for kw in ["proof", "calculus", "linear algebra", "math", "theorem"]):
        tags.append("math-heavy")
    if any(kw in combined_text for kw in ["technical interview", "leetcode", "interview prep"]):
        tags.append("technical-interview-relevant")
    if any(kw in combined_text for kw in ["group work", "group project", "team"]):
        tags.append("group-work-heavy")

    return tags
