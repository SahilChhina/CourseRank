# CourseRank AI — Developer-Ready PRD & Build Specification

## 0. LLM Coding Context

You are helping build **CourseRank AI**, a web app for Western University students. The app lets a user search for a Western course code, then generates a structured course intelligence report using course outlines/syllabi, public student discussion summaries, and user-submitted reviews.

The app should be designed as a real product, not just a demo. The initial target is **Western University only**. The long-term goal is to expand to other universities.

The project should showcase:
- Python
- Machine learning / NLP
- PDF parsing
- Data pipelines
- PostgreSQL database design
- API development
- React frontend
- Data visualization
- Deployable full-stack architecture

Primary user problem:

> Students choose courses using scattered information from Reddit, old syllabi, group chats, professor review sites, and word of mouth. CourseRank AI turns this scattered information into a structured, source-backed course report.

---

# 1. Product Summary

## Product Name

**CourseRank AI**

## One-Line Description

An AI-powered course intelligence platform that helps Western University students understand course difficulty, workload, grading schemes, and student sentiment before enrolling.

## Initial Market

Western University undergraduate students.

## Core User Flow

1. User enters a course code, such as `CS 2210`.
2. App finds or processes the course information.
3. App extracts grading breakdown from syllabi/course outlines.
4. App summarizes student sentiment and common themes.
5. App generates difficulty, workload, and assessment-style scores.
6. User can compare courses or submit anonymous feedback.

---

# 2. Problem Statement

Western students often struggle to choose courses because the useful information is fragmented across:

- Western academic calendar pages
- old course outlines/syllabi
- Reddit threads
- group chats
- Rate My Professor-style professor reviews
- word of mouth
- student-submitted opinions

Students want to know:

- How is the course graded?
- Is it exam-heavy, assignment-heavy, project-based, or participation-heavy?
- How difficult is the course?
- How much weekly workload should I expect?
- What do other students say about it?
- Is the professor/course organized?
- Is it useful for internships, careers, grad school, or prerequisites?
- Should I take this course based on my learning style?

CourseRank AI solves this by creating a structured course report with extracted grading information, summarized feedback, workload indicators, and explainable course scores.

---

# 3. Target Users

## Primary Users

Western University undergraduate students choosing courses.

## Secondary Users

- First-year students planning electives
- Upper-year students comparing technical electives
- Students balancing school with part-time work
- Transfer students
- Academic clubs or peer mentors
- Students planning summer school

---

# 4. User Personas

## Persona 1: First-Year Student

**Goal:** Avoid accidentally taking an extremely difficult elective.  
**Pain Point:** Does not know how to interpret course outlines or Reddit comments.  
**Needs:** Difficulty score, workload summary, grading breakdown, and student sentiment.

## Persona 2: Upper-Year CS Student

**Goal:** Compare technical electives.  
**Pain Point:** Wants to know which courses are project-heavy, coding-heavy, theory-heavy, or exam-heavy.  
**Needs:** Assessment breakdown, tags, professor/course feedback, workload estimate.

## Persona 3: Working Student

**Goal:** Pick courses that fit around a part-time job.  
**Pain Point:** Cannot take courses with excessive weekly assignments or unpredictable deadlines.  
**Needs:** Estimated hours per week, number of assessments, deadline density, and exam weight.

---

# 5. Product Goals

## User Goals

- Help students choose courses more confidently.
- Reduce time spent manually searching Reddit and syllabi.
- Make course information easier to compare.
- Provide source-backed and explainable summaries.
- Help students find courses that match their learning style.

## Technical / Portfolio Goals

- Demonstrate Python-based data pipelines.
- Demonstrate NLP and ML skills.
- Demonstrate PDF parsing and information extraction.
- Demonstrate full-stack app development.
- Demonstrate database and API design.
- Demonstrate a real product with potential users.

---

# 6. MVP Scope

## MVP Must-Have Features

1. Course search by Western course code.
2. Course report page.
3. Syllabus/course-outline ingestion.
4. Grading scheme extraction.
5. Assessment style tagging.
6. Student sentiment summary.
7. Difficulty and workload scores.
8. Anonymous user review submission.
9. Basic course comparison.
10. Admin/data dashboard.

## MVP Should Not Include

- All universities.
- Official academic advising.
- Mobile app.
- Real-time enrollment data.
- Grade prediction.
- Professor ranking leaderboard.
- Aggressive scraping of restricted platforms.
- Login-required features unless needed later.

---

# 7. Data Sources

## 7.1 Western Course Outlines / Syllabi

Use for:
- grading breakdown
- assessment types
- course topics
- prerequisites
- textbook requirements
- weekly schedule
- course objectives

Implementation:
- Start with manually uploaded PDFs or known public URLs.
- Parse PDFs using `pdfplumber`, `PyMuPDF`, or similar tools.
- Store raw text and extracted fields.

## 7.2 Western Academic Calendar

Use for:
- official course name
- course description
- prerequisites
- antirequisites
- department
- credit weight

Implementation:
- Use public course calendar pages if permitted.
- Cache official course metadata.

## 7.3 Reddit

Use for:
- student opinions
- workload discussion
- course comparisons
- difficulty themes

Implementation:
- Prefer official Reddit API or compliant access methods.
- Do not store usernames.
- Store only anonymized, summarized, or transformed content.
- Avoid showing individual comments directly unless allowed.

## 7.4 Rate My Professor / Professor Review Sites

Important constraint:
- Do not make RMP scraping a core dependency.
- Check robots.txt and platform terms before any automated crawling.
- Safer MVP approach:
  - Allow users to submit their own feedback.
  - Let users paste a source link manually.
  - Summarize only if content is provided by the user.
  - Use RMP as an external reference link rather than scraped data.

## 7.5 User-Submitted Reviews

This should become the most important long-term dataset.

User-submitted fields:
- course code
- professor/instructor name
- term taken
- difficulty rating
- workload rating
- hours per week
- grading fairness rating
- organization rating
- usefulness rating
- written review
- would recommend? yes/no

---

# 8. Core Features

## 8.1 Course Search

Users should be able to search by:
- course code, e.g. `CS 2210`
- course name
- subject
- professor name, optional later

Expected behavior:
- Search should normalize course code formats.
- Examples:
  - `CS2210`
  - `CS 2210`
  - `Computer Science 2210`
  - `Data Structures and Algorithms`

## 8.2 Course Report Page

Each course page should include:

- Course title
- Course code
- Department
- Official description
- Prerequisites / antirequisites
- Terms offered, if available
- AI-generated overall summary
- Grading breakdown
- Difficulty score
- Workload score
- Sentiment summary
- Assessment style tags
- Common positive themes
- Common negative themes
- Source transparency
- User-submitted review summary

## 8.3 Grading Scheme Extractor

Goal:
Extract grading components from syllabi/course outlines.

Example output:

```json
{
  "course_code": "CS 2210",
  "grading_components": [
    { "component": "Assignments", "weight": 30 },
    { "component": "Midterm", "weight": 25 },
    { "component": "Final Exam", "weight": 40 },
    { "component": "Participation/Labs", "weight": 5 }
  ],
  "confidence_score": 0.91
}
```

Potential extraction techniques:
- regex
- PDF text extraction
- table extraction
- rule-based parsing
- LLM validation layer
- manual override in admin panel

Common grading keywords:
- assignment
- assignments
- quiz
- quizzes
- midterm
- test
- final
- final exam
- lab
- labs
- tutorial
- participation
- project
- presentation
- essay
- report
- exam
- attendance

## 8.4 Assessment Style Tags

Automatically classify course as:

- exam-heavy
- assignment-heavy
- project-based
- participation-heavy
- reading-heavy
- writing-heavy
- coding-heavy
- math-heavy
- memorization-heavy
- presentation-heavy
- lab-heavy
- group-work-heavy
- technical-interview-relevant

Tag logic examples:
- If final exam + midterms >= 60%, label `exam-heavy`.
- If assignments/projects >= 40%, label `assignment-heavy`.
- If labs >= 20%, label `lab-heavy`.
- If course text contains many coding/programming terms, label `coding-heavy`.
- If review themes mention “proofs,” “calculus,” “stats,” or “math,” label `math-heavy`.

## 8.5 Student Sentiment Summary

Use Reddit summaries and user reviews to generate:

- overall sentiment
- positive themes
- negative themes
- mixed themes
- workload comments
- difficulty comments
- professor/course organization themes

Example output:

```json
{
  "overall_sentiment": "mixed-positive",
  "positive_themes": [
    "useful assignments",
    "important foundational course",
    "good for technical interviews"
  ],
  "negative_themes": [
    "heavy workload",
    "fast pacing",
    "challenging exams"
  ],
  "summary": "Students generally find the course useful but demanding. The course is often described as manageable with consistent practice, but difficult if students fall behind."
}
```

## 8.6 Difficulty and Workload Scores

Scores should be explainable.

Example:

```json
{
  "difficulty_score": 7.8,
  "workload_score": 8.2,
  "organization_score": 6.9,
  "assessment_fairness_score": 7.1,
  "usefulness_score": 8.5,
  "confidence_score": 0.76
}
```

Explainability example:

> Difficulty is high because many comments mention challenging assignments, fast pacing, and heavy exam preparation. The course also has a high final exam weight and multiple technical assessments.

## 8.7 Source Transparency

Every course report should show source categories, such as:

- Official Western calendar
- Course outline
- Public student discussions
- Anonymous CourseRank reviews

Do not show scraped usernames or personal details.

## 8.8 User Review Submission

Users can submit anonymous feedback.

Form fields:
- course code
- professor
- term
- difficulty rating, 1–10
- workload rating, 1–10
- hours per week
- organization rating, 1–10
- assessment fairness rating, 1–10
- usefulness rating, 1–10
- written review
- would recommend? yes/no

Moderation:
- filter profanity
- block personal attacks
- allow report button
- summarize aggregate themes instead of highlighting harmful comments

---

# 9. Example Course Report

## Course

**CS 2210 — Data Structures and Algorithms**

## Overall Summary

CS 2210 is a foundational computer science course focused on data structures, algorithms, and problem-solving. Students commonly describe it as useful and important for technical interviews, but demanding if they fall behind.

## Grading Breakdown

| Component | Weight |
|---|---:|
| Assignments | 30% |
| Midterm | 25% |
| Final Exam | 40% |
| Participation/Labs | 5% |

## Scores

| Category | Score |
|---|---:|
| Difficulty | 7.8 / 10 |
| Workload | 8.2 / 10 |
| Organization | 6.9 / 10 |
| Assessment Fairness | 7.1 / 10 |
| Usefulness | 8.5 / 10 |

## Student Sentiment

| Theme | Summary |
|---|---|
| Difficulty | Many students describe the course as challenging but fair. |
| Workload | Assignments may take significant time. |
| Usefulness | Students often view it as important for internships and interviews. |
| Teaching | Feedback varies depending on instructor. |

## Tags

`coding-heavy` `assignment-heavy` `exam-heavy` `technical-interview-relevant` `core-cs`

---

# 10. User Stories

## Course Search

As a student, I want to search a course code so that I can quickly understand whether the course fits my schedule and learning style.

## Grading Breakdown

As a student, I want to see the grading scheme so that I know whether the course is exam-heavy, assignment-heavy, project-based, or participation-heavy.

## Student Discussion Summary

As a student, I want to see summarized student opinions so that I do not have to read many Reddit threads manually.

## Difficulty Score

As a student, I want to see an explainable difficulty score so that I can compare courses more easily.

## Anonymous Review

As a student, I want to submit anonymous feedback so that future students can benefit from my experience.

## Course Comparison

As a student, I want to compare two courses so that I can decide which one better fits my workload and goals.

---

# 11. Frontend Pages

## 11.1 Home Page

Components:
- hero section
- search bar
- popular courses
- recently analyzed courses
- explanation of how it works

Main CTA:
- “Analyze a course”

## 11.2 Search Results Page

Components:
- list of matching courses
- course code
- course title
- department
- quick tags
- difficulty/workload preview if available

## 11.3 Course Report Page

Components:
- course header
- overall AI summary
- grading breakdown chart
- difficulty/workload score cards
- assessment style tags
- sentiment summary
- common themes
- source list
- review submission CTA

## 11.4 Compare Courses Page

Inputs:
- course A
- course B

Outputs:
- grading comparison
- workload comparison
- difficulty comparison
- sentiment comparison
- recommendation summary

## 11.5 Submit Review Page

Components:
- rating sliders
- text review
- professor field
- term field
- privacy notice
- submit button

## 11.6 Admin/Data Dashboard

For developer/admin:
- courses indexed
- reviews collected
- syllabi processed
- extraction success rate
- extraction confidence
- most searched courses
- flagged reviews

---

# 12. Technical Architecture

## Recommended Stack

Frontend:
- React
- TypeScript
- Tailwind CSS
- Recharts or Chart.js

Backend:
- Python
- FastAPI recommended, Flask acceptable
- SQLAlchemy
- Pydantic

Database:
- PostgreSQL
- Supabase is acceptable for fast setup

ML/NLP:
- Pandas
- NumPy
- scikit-learn
- spaCy
- NLTK or VADER
- sentence-transformers, optional
- BERTopic, optional later

PDF Processing:
- pdfplumber
- PyMuPDF
- python-docx if DOCX outlines are used

Deployment:
- Frontend: Vercel
- Backend: Render, Railway, Fly.io, or AWS
- Database: Supabase/PostgreSQL
- File storage: Supabase Storage or S3
- Background jobs: cron, Celery, or simple scheduled tasks later

---

# 13. Backend API Design

## Core Endpoints

```txt
GET /health
GET /courses/search?query={query}
GET /courses/{course_id}
GET /courses/{course_id}/grading
GET /courses/{course_id}/sentiment
GET /courses/{course_id}/themes
GET /courses/{course_id}/scores
POST /courses/compare
POST /courses/{course_id}/reviews
POST /admin/ingest-syllabus
POST /admin/reprocess-course/{course_id}
```

## Example: GET /courses/{course_id}

Response:

```json
{
  "id": 1,
  "course_code": "CS 2210",
  "course_name": "Data Structures and Algorithms",
  "department": "Computer Science",
  "description": "A course covering data structures, algorithms, and problem solving.",
  "prerequisites": ["CS 1027"],
  "antirequisites": [],
  "summary": "Students describe this as a useful but demanding course.",
  "tags": ["coding-heavy", "assignment-heavy", "exam-heavy"],
  "scores": {
    "difficulty": 7.8,
    "workload": 8.2,
    "organization": 6.9,
    "usefulness": 8.5
  }
}
```

## Example: POST /courses/{course_id}/reviews

Request:

```json
{
  "professor_name": "Jane Doe",
  "term_taken": "Fall 2025",
  "difficulty_rating": 8,
  "workload_rating": 9,
  "hours_per_week": 7,
  "organization_rating": 7,
  "assessment_fairness_rating": 6,
  "usefulness_rating": 9,
  "review_text": "Useful course but assignments took a lot of time.",
  "would_recommend": true
}
```

---

# 14. Database Schema

## courses

```sql
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    department TEXT,
    description TEXT,
    prerequisites TEXT[],
    antirequisites TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## course_outlines

```sql
CREATE TABLE course_outlines (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id),
    source_url TEXT,
    file_path TEXT,
    raw_text TEXT,
    term TEXT,
    year INTEGER,
    extraction_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## grading_components

```sql
CREATE TABLE grading_components (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id),
    component_name TEXT NOT NULL,
    weight NUMERIC NOT NULL,
    source_document TEXT,
    confidence_score NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## reviews

```sql
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id),
    professor_name TEXT,
    term_taken TEXT,
    difficulty_rating INTEGER,
    workload_rating INTEGER,
    hours_per_week NUMERIC,
    organization_rating INTEGER,
    assessment_fairness_rating INTEGER,
    usefulness_rating INTEGER,
    review_text TEXT,
    would_recommend BOOLEAN,
    is_flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## sentiment_results

```sql
CREATE TABLE sentiment_results (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id),
    overall_sentiment TEXT,
    sentiment_score NUMERIC,
    positive_themes TEXT[],
    negative_themes TEXT[],
    neutral_themes TEXT[],
    summary TEXT,
    confidence_score NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## course_scores

```sql
CREATE TABLE course_scores (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id),
    difficulty_score NUMERIC,
    workload_score NUMERIC,
    organization_score NUMERIC,
    assessment_fairness_score NUMERIC,
    usefulness_score NUMERIC,
    confidence_score NUMERIC,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## search_logs

```sql
CREATE TABLE search_logs (
    id SERIAL PRIMARY KEY,
    query TEXT,
    matched_course_id INTEGER REFERENCES courses(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

# 15. ML / NLP Pipeline

## 15.1 Syllabus Parsing Pipeline

Input:
- PDF or HTML course outline

Steps:
1. Extract text using `pdfplumber` or `PyMuPDF`.
2. Clean text.
3. Identify grading section.
4. Extract component names and percentages.
5. Normalize component names.
6. Validate that total weight is close to 100%.
7. Store results in database with confidence score.

Pseudo-code:

```python
def extract_grading_scheme(raw_text: str) -> dict:
    cleaned_text = clean_text(raw_text)
    grading_section = find_grading_section(cleaned_text)
    components = parse_percentage_lines(grading_section)
    normalized = normalize_components(components)
    confidence = calculate_confidence(normalized)
    return {
        "components": normalized,
        "confidence_score": confidence
    }
```

## 15.2 Sentiment Analysis Pipeline

Input:
- user reviews
- public discussion snippets
- manually provided source text

Steps:
1. Clean text.
2. Remove usernames/personal identifiers.
3. Split into sentences.
4. Score sentiment.
5. Extract key phrases.
6. Group into themes.
7. Generate summary.

Possible tools:
- VADER for social-media-style sentiment
- scikit-learn baseline classifier
- sentence-transformers for embeddings
- NMF/LDA for topic modeling

## 15.3 Topic Modeling Pipeline

Goal:
Identify recurring themes.

Potential themes:
- workload
- exams
- assignments
- professor clarity
- course organization
- usefulness
- difficulty
- group work
- coding
- math
- memorization

## 15.4 Scoring Logic

Suggested formula:

```txt
difficulty_score =
    0.35 * normalized_user_difficulty_rating
  + 0.20 * negative_sentiment_score
  + 0.15 * workload_mentions_score
  + 0.15 * exam_weight_score
  + 0.15 * assignment_complexity_score
```

```txt
workload_score =
    0.40 * average_reported_hours_per_week
  + 0.20 * assignment_weight_score
  + 0.20 * number_of_assessments_score
  + 0.20 * workload_theme_frequency
```

The score should always include:
- numeric score
- confidence score
- plain-English explanation

---

# 16. Ethical, Legal, and Privacy Constraints

Important:
- Do not store Reddit usernames.
- Do not display personal comments without permission.
- Do not scrape websites that disallow crawling.
- Respect robots.txt and platform terms.
- Do not position the app as official academic advice.
- Avoid defamatory or personal claims about instructors.
- Focus summaries on course structure and student experience.
- Add report/flag functionality.
- Show sample size and confidence where possible.
- Prefer user-submitted reviews and official syllabi over restricted scraping.

Recommended disclaimer:

> CourseRank AI provides unofficial, student-centered course summaries based on available course materials and aggregated feedback. It is not affiliated with Western University and should not replace official academic advising.

---

# 17. MVP Build Phases

## Phase 1: Foundation

Build:
- React frontend
- FastAPI backend
- PostgreSQL database
- course search
- course report page
- manually seeded course data

Deliverable:
- User can search a course and view a basic course page.

## Phase 2: Syllabus Parser

Build:
- PDF upload endpoint
- PDF text extraction
- grading breakdown extractor
- grading table UI
- confidence score

Deliverable:
- Admin can upload syllabus and grading scheme appears on course page.

## Phase 3: Review System

Build:
- anonymous review form
- ratings aggregation
- written review storage
- review moderation flag
- average score display

Deliverable:
- Users can submit reviews and scores update.

## Phase 4: NLP Sentiment + Themes

Build:
- text cleaning pipeline
- sentiment analysis
- topic/theme extraction
- course summary generation

Deliverable:
- Course report displays positive/negative themes and sentiment summary.

## Phase 5: Course Comparison

Build:
- compare two courses
- side-by-side grading
- side-by-side workload/difficulty
- recommendation summary

Deliverable:
- Users can compare courses before enrollment.

## Phase 6: Deployment + Real Users

Build:
- deploy frontend
- deploy backend
- deploy database
- add analytics
- collect feedback from Western students

Deliverable:
- Public MVP with real users.

---

# 18. Suggested Folder Structure

```txt
courserank-ai/
  backend/
    app/
      main.py
      database.py
      models/
        course.py
        review.py
        grading.py
        sentiment.py
      schemas/
        course_schema.py
        review_schema.py
      routes/
        courses.py
        reviews.py
        admin.py
      services/
        syllabus_parser.py
        grading_extractor.py
        sentiment_analyzer.py
        topic_modeler.py
        scoring_engine.py
      utils/
        text_cleaning.py
        course_code_normalizer.py
    requirements.txt
    Dockerfile

  frontend/
    src/
      components/
        SearchBar.tsx
        CourseCard.tsx
        ScoreCard.tsx
        GradingBreakdown.tsx
        SentimentSummary.tsx
        CourseComparison.tsx
      pages/
        Home.tsx
        CourseReport.tsx
        CompareCourses.tsx
        SubmitReview.tsx
        AdminDashboard.tsx
      api/
        courses.ts
        reviews.ts
      types/
        course.ts
        review.ts
    package.json

  docs/
    PRD.md
    API_SPEC.md
    DATA_MODEL.md

  README.md
```

---

# 19. Starter Implementation Priorities

Start with these files:

1. `backend/app/main.py`
2. `backend/app/database.py`
3. `backend/app/models/course.py`
4. `backend/app/models/review.py`
5. `backend/app/routes/courses.py`
6. `backend/app/routes/reviews.py`
7. `backend/app/services/grading_extractor.py`
8. `frontend/src/pages/Home.tsx`
9. `frontend/src/pages/CourseReport.tsx`
10. `frontend/src/components/SearchBar.tsx`

---

# 20. LLM Coding Prompts

Use these prompts with an LLM when coding.

## Prompt 1: Generate Backend Starter

```txt
Build the backend for CourseRank AI using FastAPI, SQLAlchemy, Pydantic, and PostgreSQL.

Create:
- main.py
- database.py
- SQLAlchemy models for courses, reviews, grading_components, course_scores, sentiment_results
- Pydantic schemas
- routes for course search, course detail, review submission, grading retrieval, and course comparison
- seed data for 5 Western University courses

Follow this PRD:
[PASTE RELEVANT PRD SECTION]
```

## Prompt 2: Generate Syllabus Parser

```txt
Build a Python service called syllabus_parser.py for CourseRank AI.

Requirements:
- Accept PDF file path or raw text
- Extract text using pdfplumber
- Find the grading/evaluation/assessment section
- Extract grading components and weights
- Normalize component names
- Validate that weights approximately total 100
- Return components with confidence score
- Include unit tests with sample syllabus text
```

## Prompt 3: Generate Sentiment Pipeline

```txt
Build a Python NLP pipeline for CourseRank AI.

Requirements:
- Clean student review text
- Remove usernames and unnecessary personal identifiers
- Run sentiment analysis using VADER or scikit-learn
- Extract positive and negative themes
- Return overall sentiment, theme lists, and explanation
- Design it so it can later be upgraded to sentence-transformers or BERTopic
```

## Prompt 4: Generate React Course Report Page

```txt
Build a React + TypeScript + Tailwind CourseReport page for CourseRank AI.

The page should show:
- course title and code
- overall AI summary
- grading breakdown table/chart
- difficulty and workload score cards
- assessment tags
- sentiment summary
- positive and negative themes
- source transparency
- submit review button

Use clean startup-style UI with responsive layout.
```

## Prompt 5: Generate Database Seed Data

```txt
Create seed data for CourseRank AI with 5 fictional Western University courses.

Each course should include:
- course code
- course title
- department
- description
- prerequisites
- grading breakdown
- scores
- 3 sample anonymous reviews

Do not use real professor names unless publicly and safely sourced.
```

---

# 21. Interview Pitch

Use this explanation in interviews:

> I built CourseRank AI because students often choose courses using scattered information from Reddit, old syllabi, and word of mouth. I wanted to create a data-driven platform that collects course information, extracts grading structures from syllabi, analyzes student sentiment, and turns everything into a structured course report. The project gave me experience with Python NLP pipelines, PDF parsing, sentiment analysis, topic modeling, PostgreSQL database design, React development, and deploying a real product for students at Western.

---

# 22. Resume Bullets

## CourseRank AI — ML-Powered Course Intelligence Platform

- Built a full-stack course intelligence platform for Western students using Python, React, PostgreSQL, and NLP to summarize course outlines, grading schemes, and student feedback.
- Developed PDF and text-processing pipelines with Python to extract grading breakdowns, assessment types, prerequisites, and workload indicators from course syllabi.
- Implemented sentiment analysis and topic modeling on student discussion data to identify recurring themes related to course difficulty, workload, teaching clarity, and assessment fairness.
- Designed an explainable scoring system that generates course difficulty, workload, and assessment-style tags, helping students compare courses before enrollment.

---

# 23. Definition of Done for MVP

The MVP is complete when:

- A user can search for a Western course.
- A course report page loads successfully.
- At least 20 courses are seeded.
- At least 5 syllabi can be processed.
- Grading breakdowns can be extracted and displayed.
- Users can submit anonymous reviews.
- Scores update based on reviews and extracted data.
- Sentiment/themes are generated from review text.
- Two courses can be compared.
- App is deployed with a public URL.
- README includes setup, architecture, and demo instructions.
- A 60-second demo video is recorded for portfolio/interviews.

---

# 24. Suggested README Summary

```txt
CourseRank AI is an AI-powered course intelligence platform for Western University students. The app helps students understand course difficulty, workload, grading structure, and student sentiment before enrolling.

The project uses Python, FastAPI, PostgreSQL, React, and NLP pipelines to parse syllabi, extract grading schemes, analyze reviews, and generate structured course reports.
```

---

# 25. Initial MVP Recommendation

Build in this order:

1. Static seeded data for 5–10 Western courses.
2. React course search and report page.
3. FastAPI backend and PostgreSQL schema.
4. Review submission and aggregation.
5. Syllabus upload and grading extractor.
6. Sentiment analysis from user reviews.
7. Course comparison.
8. Deployment.
9. Real user feedback from Western students.
