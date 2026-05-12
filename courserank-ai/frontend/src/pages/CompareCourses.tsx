import { useState } from "react";
import { Link } from "react-router-dom";
import { searchCourses, compareCourses } from "../api/courses";
import type { CourseSearchResult, CompareResult, CourseSummary } from "../types/course";
import TagBadge from "../components/TagBadge";

const SCORE_LABELS: { key: keyof CourseSummary["scores"]; label: string }[] = [
  { key: "difficulty_score", label: "Difficulty" },
  { key: "workload_score", label: "Workload" },
  { key: "organization_score", label: "Organization" },
  { key: "usefulness_score", label: "Usefulness" },
];

function ScoreBar({ value, max = 10 }: { value: number; max?: number }) {
  const pct = (value / max) * 100;
  const color = value >= 8 ? "bg-red-400" : value >= 6 ? "bg-orange-400" : "bg-green-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-semibold w-8 text-right">{value.toFixed(1)}</span>
    </div>
  );
}

function CoursePickerInput({ label, onSelect }: { label: string; onSelect: (c: CourseSearchResult) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CourseSearchResult[]>([]);

  const search = async () => {
    if (!query.trim()) return;
    const r = await searchCourses(query).catch(() => []);
    setResults(r);
  };

  return (
    <div>
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{label}</p>
      <div className="flex gap-2 mb-2">
        <input
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-western-purple"
          placeholder="e.g. CS 2210"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
        />
        <button
          onClick={search}
          className="bg-western-purple text-white text-sm px-4 py-2 rounded-lg hover:bg-purple-900 transition"
        >
          Find
        </button>
      </div>
      {results.length > 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          {results.slice(0, 5).map((r) => (
            <button
              key={r.id}
              onClick={() => { onSelect(r); setResults([]); setQuery(r.course_code); }}
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-0"
            >
              <span className="font-semibold">{r.course_code}</span> — {r.course_name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function CompareCourses() {
  const [courseA, setCourseA] = useState<CourseSearchResult | null>(null);
  const [courseB, setCourseB] = useState<CourseSearchResult | null>(null);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCompare = async () => {
    if (!courseA || !courseB) return;
    setLoading(true);
    setError("");
    try {
      const r = await compareCourses(courseA.id, courseB.id);
      setResult(r);
    } catch {
      setError("Comparison failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-western-purple text-white">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="font-bold text-lg tracking-tight">CourseRank AI</Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10">
        <Link to="/" className="text-western-purple text-sm hover:underline mb-6 inline-block">← Back to search</Link>
        <h1 className="text-2xl font-extrabold text-gray-900 mb-8">Compare Courses</h1>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
            <CoursePickerInput label="Course A" onSelect={setCourseA} />
            <CoursePickerInput label="Course B" onSelect={setCourseB} />
          </div>
          <button
            onClick={handleCompare}
            disabled={!courseA || !courseB || loading}
            className="bg-western-purple text-white font-semibold px-8 py-2.5 rounded-lg hover:bg-purple-900 transition disabled:opacity-50"
          >
            {loading ? "Comparing…" : "Compare"}
          </button>
          {error && <p className="text-red-500 text-sm mt-3">{error}</p>}
        </div>

        {result && (
          <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
            {/* Course headers */}
            <div className="grid grid-cols-2 border-b border-gray-200">
              {[result.course_a, result.course_b].map((c) => (
                <div key={c.id} className="p-5 border-r last:border-r-0 border-gray-200">
                  <p className="text-xs font-semibold text-western-purple uppercase tracking-wider">{c.course_code}</p>
                  <p className="font-bold text-gray-900 mt-0.5">{c.course_name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{c.department}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {c.tags.map((t) => <TagBadge key={t} tag={t} />)}
                  </div>
                </div>
              ))}
            </div>

            {/* Scores */}
            <div className="p-5 border-b border-gray-200">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4">Scores</p>
              <div className="space-y-4">
                {SCORE_LABELS.map(({ key, label }) => {
                  const va = result.course_a.scores[key];
                  const vb = result.course_b.scores[key];
                  return (
                    <div key={key}>
                      <p className="text-xs font-medium text-gray-600 mb-1.5">{label}</p>
                      <div className="grid grid-cols-2 gap-4">
                        {[va, vb].map((v, i) => (
                          <div key={i}>
                            {v !== undefined && v !== null ? <ScoreBar value={Number(v)} /> : <span className="text-xs text-gray-400">N/A</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Grading */}
            <div className="p-5">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-4">Grading Breakdown</p>
              <div className="grid grid-cols-2 gap-4">
                {[result.course_a, result.course_b].map((c) => (
                  <div key={c.id} className="space-y-1">
                    {c.grading_components.map((g) => (
                      <div key={g.component_name} className="flex justify-between text-sm">
                        <span className="text-gray-700">{g.component_name}</span>
                        <span className="font-semibold">{g.weight}%</span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
