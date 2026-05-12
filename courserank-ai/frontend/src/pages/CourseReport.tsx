import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, Link, useSearchParams } from "react-router-dom";
import { getCourse, getReviews, API_BASE } from "../api/courses";
import type { CourseDetail } from "../types/course";
import type { ReviewOut } from "../types/review";
import GradingBreakdown from "../components/GradingBreakdown";
import SentimentSummary from "../components/SentimentSummary";
import ScorePill from "../components/ScorePill";
import TagBadge from "../components/TagBadge";
import SyllabusUpload from "../components/SyllabusUpload";
import ReviewStats from "../components/ReviewStats";
import ReviewsList from "../components/ReviewsList";

const SCORE_LABELS: [keyof NonNullable<CourseDetail["scores"]>, string][] = [
  ["difficulty_score", "Difficulty"],
  ["workload_score", "Workload"],
  ["organization_score", "Organization"],
  ["assessment_fairness_score", "Fairness"],
  ["usefulness_score", "Usefulness"],
];

export default function CourseReport() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [reviews, setReviews] = useState<ReviewOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [justReviewed] = useState(searchParams.get("reviewed") === "1");

  const fetchCourse = useCallback(() => {
    if (!id) return;
    getCourse(Number(id))
      .then(setCourse)
      .catch(() => setError("Course not found."))
      .finally(() => setLoading(false));
  }, [id]);

  const fetchReviews = useCallback(() => {
    if (!id) return;
    getReviews(Number(id)).then(setReviews).catch(() => {});
  }, [id]);

  useEffect(() => { fetchCourse(); fetchReviews(); }, [fetchCourse, fetchReviews]);

  const handleFlag = (reviewId: number) => {
    setReviews((prev) => prev.filter((r) => r.id !== reviewId));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        Loading…
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">{error || "Course not found."}</p>
          <Link to="/" className="text-western-purple font-medium hover:underline">← Back to search</Link>
        </div>
      </div>
    );
  }

  const tags = computeTags(course);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-western-purple text-white">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="font-bold text-lg tracking-tight">CourseRank AI</Link>
          <Link to="/compare" className="text-sm text-purple-200 hover:text-white transition">
            Compare Courses →
          </Link>
        </div>
      </header>

      {/* Course header */}
      <div className="bg-western-purple text-white pb-10 pt-8">
        <div className="max-w-4xl mx-auto px-6">
          <Link to="/" className="text-purple-300 text-sm hover:text-white transition mb-3 inline-block">
            ← Back to search
          </Link>
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <p className="text-purple-300 text-sm font-semibold uppercase tracking-widest mb-1">
                {course.course_code} · {course.department}
              </p>
              <h1 className="text-3xl font-extrabold">{course.course_name}</h1>
              {course.description && (
                <p className="text-purple-200 text-sm mt-3 max-w-2xl leading-relaxed">
                  {course.description}
                </p>
              )}
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-4">
                  {tags.map((t) => <TagBadge key={t} tag={t} />)}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        {/* Scores */}
        {course.scores && (
          <Section title="Course Scores">
            <div className="flex flex-wrap gap-3">
              {SCORE_LABELS.map(([key, label]) => {
                const val = course.scores![key];
                return val !== null && val !== undefined ? (
                  <ScorePill key={key} label={label} value={Number(val)} size="lg" />
                ) : null;
              })}
            </div>
            {course.scores.explanation && (
              <p className="text-sm text-gray-600 mt-4 leading-relaxed bg-gray-50 border border-gray-200 rounded-lg p-4">
                {course.scores.explanation}
              </p>
            )}
          </Section>
        )}

        {/* Grading breakdown */}
        <Section title="Grading Breakdown">
          <GradingBreakdown components={course.grading_components} />
          <div className="mt-5 pt-4 border-t border-gray-100">
            <SyllabusUpload courseId={course.id} onSuccess={fetchCourse} />
          </div>
        </Section>

        {/* Sentiment */}
        <Section title="Student Sentiment">
          {course.sentiment ? (
            <SentimentSummary sentiment={course.sentiment} />
          ) : (
            <p className="text-sm text-gray-500">
              No sentiment data yet — pull from r/uwo to analyze.
            </p>
          )}
          <div className="mt-4 pt-4 border-t border-gray-100">
            <AnalyzeSentimentButton courseId={course.id} onSuccess={fetchCourse} />
          </div>
        </Section>

        {/* Prerequisites */}
        {(course.prerequisites.length > 0 || course.antirequisites.length > 0) && (
          <Section title="Prerequisites & Antirequisites">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              {course.prerequisites.length > 0 && (
                <div>
                  <p className="font-semibold text-gray-600 mb-1">Prerequisites</p>
                  <div className="flex flex-wrap gap-1.5">
                    {course.prerequisites.map((p) => (
                      <span key={p} className="bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-0.5 rounded-full text-xs font-medium">
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {course.antirequisites.length > 0 && (
                <div>
                  <p className="font-semibold text-gray-600 mb-1">Antirequisites</p>
                  <div className="flex flex-wrap gap-1.5">
                    {course.antirequisites.map((a) => (
                      <span key={a} className="bg-red-50 text-red-600 border border-red-200 px-2.5 py-0.5 rounded-full text-xs font-medium">
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Section>
        )}

        {/* Student reviews */}
        <Section title={`Student Reviews${reviews.length ? ` (${reviews.length})` : ""}`}>
          {justReviewed && (
            <div className="mb-4 bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg px-4 py-3">
              Your review was submitted — thank you!
            </div>
          )}
          {reviews.length > 0 && (
            <div className="mb-6">
              <ReviewStats reviews={reviews} />
            </div>
          )}
          <ReviewsList
            reviews={reviews}
            courseId={course.id}
            onFlag={handleFlag}
          />
        </Section>

        {/* Source transparency */}
        <Section title="Sources">
          <div className="flex flex-wrap gap-2 text-xs">
            {["Western Academic Calendar", "Course Outline / Syllabus", "Anonymous CourseRank Reviews"].map((s) => (
              <span key={s} className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full border border-gray-200">
                {s}
              </span>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-3">
            CourseRank AI provides unofficial course summaries. Not affiliated with Western University.
          </p>
        </Section>

        {/* Submit review CTA */}
        <div className="bg-western-purple text-white rounded-2xl p-8 text-center">
          <h3 className="text-xl font-bold mb-2">Taken this course?</h3>
          <p className="text-purple-200 text-sm mb-5">
            Help future students by submitting an anonymous review.
          </p>
          <Link
            to={`/courses/${course.id}/review`}
            className="inline-block bg-white text-western-purple font-semibold px-6 py-2.5 rounded-lg hover:bg-purple-50 transition"
          >
            Submit a Review
          </Link>
        </div>
      </main>
    </div>
  );
}

function AnalyzeSentimentButton({ courseId, onSuccess }: { courseId: number; onSuccess: () => void }) {
  const [state, setState] = useState<"idle" | "running" | "done" | "error">("idle");
  const timerRef = useRef<number | null>(null);

  const run = async () => {
    setState("running");
    try {
      const res = await fetch(`${API_BASE}/admin/analyze-sentiment/${courseId}`, { method: "POST" });
      if (!res.ok) throw new Error("failed");
      // Wait ~30s for the background task to complete, then refetch
      timerRef.current = window.setTimeout(() => {
        onSuccess();
        setState("done");
      }, 30000);
    } catch {
      setState("error");
    }
  };

  if (state === "running") {
    return <p className="text-xs text-gray-500">Scraping r/uwo and analyzing… (~30s)</p>;
  }
  if (state === "done") {
    return <p className="text-xs text-green-600">Sentiment updated. Refreshing…</p>;
  }
  if (state === "error") {
    return <p className="text-xs text-red-500">Failed. Try again later.</p>;
  }
  return (
    <button
      onClick={run}
      className="text-xs font-medium text-blue-600 hover:underline flex items-center gap-1"
    >
      <span>🔍</span> Analyze student sentiment from r/uwo
    </button>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6">
      <h2 className="text-base font-bold text-gray-900 mb-4">{title}</h2>
      {children}
    </div>
  );
}

function computeTags(course: CourseDetail): string[] {
  const tags: string[] = [];
  const components = course.grading_components;

  const examWeight = components
    .filter((c) => /exam|midterm|test|final/i.test(c.component_name))
    .reduce((s, c) => s + Number(c.weight), 0);
  const assignmentWeight = components
    .filter((c) => /assignment|homework|project/i.test(c.component_name))
    .reduce((s, c) => s + Number(c.weight), 0);
  const labWeight = components
    .filter((c) => /lab/i.test(c.component_name))
    .reduce((s, c) => s + Number(c.weight), 0);

  if (examWeight >= 60) tags.push("exam-heavy");
  if (assignmentWeight >= 40) tags.push("assignment-heavy");
  if (labWeight >= 20) tags.push("lab-heavy");

  const text = [
    course.description ?? "",
    ...(course.sentiment?.positive_themes ?? []),
    ...(course.sentiment?.negative_themes ?? []),
  ].join(" ").toLowerCase();

  if (/coding|programming|code|python|java|c\+\+/i.test(text)) tags.push("coding-heavy");
  if (/proof|calculus|linear algebra|theorem|math/i.test(text)) tags.push("math-heavy");
  if (/technical interview|leetcode/i.test(text)) tags.push("technical-interview-relevant");

  return tags;
}
