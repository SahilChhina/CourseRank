import { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { submitReview } from "../api/courses";

const RATING_FIELDS: { key: string; label: string; desc: string }[] = [
  { key: "difficulty_rating", label: "Difficulty", desc: "How hard was this course overall?" },
  { key: "workload_rating", label: "Workload", desc: "How much time did it demand per week?" },
  { key: "organization_rating", label: "Organization", desc: "Was the course well-structured?" },
  { key: "assessment_fairness_rating", label: "Assessment Fairness", desc: "Were the grading and assessments fair?" },
  { key: "usefulness_rating", label: "Usefulness", desc: "How useful is this course for your career/program?" },
];

export default function SubmitReview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [form, setForm] = useState<Record<string, string | number | boolean>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const set = (key: string, value: string | number | boolean) =>
    setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setSubmitting(true);
    setError("");
    try {
      await submitReview(Number(id), {
        professor_name: (form.professor_name as string) || undefined,
        term_taken: (form.term_taken as string) || undefined,
        difficulty_rating: form.difficulty_rating ? Number(form.difficulty_rating) : undefined,
        workload_rating: form.workload_rating ? Number(form.workload_rating) : undefined,
        hours_per_week: form.hours_per_week ? Number(form.hours_per_week) : undefined,
        organization_rating: form.organization_rating ? Number(form.organization_rating) : undefined,
        assessment_fairness_rating: form.assessment_fairness_rating ? Number(form.assessment_fairness_rating) : undefined,
        usefulness_rating: form.usefulness_rating ? Number(form.usefulness_rating) : undefined,
        review_text: (form.review_text as string) || undefined,
        would_recommend: form.would_recommend !== undefined ? Boolean(form.would_recommend) : undefined,
      });
      navigate(`/courses/${id}?reviewed=1`);
    } catch {
      setError("Submission failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-western-purple text-white">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <Link to="/" className="font-bold text-lg tracking-tight">CourseRank AI</Link>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-10">
        <Link to={`/courses/${id}`} className="text-western-purple text-sm hover:underline mb-6 inline-block">
          ← Back to course
        </Link>
        <h1 className="text-2xl font-extrabold text-gray-900 mb-1">Submit a Review</h1>
        <p className="text-sm text-gray-500 mb-8">Your review is anonymous. It helps future students make better decisions.</p>

        <form onSubmit={handleSubmit} className="space-y-6 bg-white border border-gray-200 rounded-2xl p-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Professor / Instructor</label>
              <input
                className="input"
                placeholder="Optional"
                value={(form.professor_name as string) ?? ""}
                onChange={(e) => set("professor_name", e.target.value)}
              />
            </div>
            <div>
              <label className="label">Term Taken</label>
              <input
                className="input"
                placeholder="e.g. Fall 2024"
                value={(form.term_taken as string) ?? ""}
                onChange={(e) => set("term_taken", e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="label">Hours per week</label>
            <input
              type="number"
              className="input w-32"
              placeholder="e.g. 7"
              min={0}
              max={40}
              value={(form.hours_per_week as string) ?? ""}
              onChange={(e) => set("hours_per_week", e.target.value)}
            />
          </div>

          {RATING_FIELDS.map(({ key, label, desc }) => (
            <div key={key}>
              <label className="label">{label} <span className="text-gray-400 font-normal">({desc})</span></label>
              <div className="flex gap-1.5 mt-1.5">
                {[1,2,3,4,5,6,7,8,9,10].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => set(key, n)}
                    className={`w-8 h-8 text-sm rounded font-semibold border transition ${
                      form[key] === n
                        ? "bg-western-purple text-white border-western-purple"
                        : "bg-white text-gray-600 border-gray-200 hover:border-western-purple"
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
          ))}

          <div>
            <label className="label">Written Review</label>
            <textarea
              className="input h-28 resize-none"
              placeholder="Share your experience with this course (optional)"
              value={(form.review_text as string) ?? ""}
              onChange={(e) => set("review_text", e.target.value)}
            />
          </div>

          <div>
            <label className="label">Would you recommend this course?</label>
            <div className="flex gap-3 mt-1.5">
              {["Yes", "No"].map((opt) => {
                const val = opt === "Yes";
                return (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => set("would_recommend", val)}
                    className={`px-5 py-2 rounded-lg text-sm font-semibold border transition ${
                      form.would_recommend === val
                        ? "bg-western-purple text-white border-western-purple"
                        : "bg-white text-gray-600 border-gray-200 hover:border-western-purple"
                    }`}
                  >
                    {opt}
                  </button>
                );
              })}
            </div>
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-western-purple text-white font-semibold py-3 rounded-lg hover:bg-purple-900 transition disabled:opacity-60"
          >
            {submitting ? "Submitting…" : "Submit Anonymous Review"}
          </button>

          <p className="text-xs text-gray-400 text-center">
            No personal information is stored. Reviews may be moderated.
          </p>
        </form>
      </main>
    </div>
  );
}
