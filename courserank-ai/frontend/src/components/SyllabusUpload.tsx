import { useState, useRef } from "react";
import { API_BASE } from "../api/courses";

interface ExtractionResult {
  status: "success" | "no_grading_found";
  confidence_score: number;
  components: { component_name: string; weight: number }[];
  total_weight?: number;
  notes: string[];
  message?: string;
}

interface Props {
  courseId: number;
  onSuccess: () => void;
}

export default function SyllabusUpload({ courseId, onSuccess }: Props) {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [term, setTerm] = useState("");
  const [uploading, setUploading] = useState(false);
  const [autoSearching, setAutoSearching] = useState(false);
  const [autoStatus, setAutoStatus] = useState<"idle" | "searching" | "done" | "not_found">("idle");
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleAutoFind = async () => {
    setAutoSearching(true);
    setAutoStatus("searching");
    setError("");
    try {
      const res = await fetch(`${API_BASE}/admin/find-syllabus/${courseId}`, { method: "POST" });
      if (!res.ok) throw new Error("Search failed");
      setAutoStatus("done");
      // Poll for results after a delay — background task needs ~10-30s
      setTimeout(() => {
        onSuccess();
        setAutoStatus("idle");
        setAutoSearching(false);
      }, 20000);
    } catch {
      setAutoStatus("not_found");
      setAutoSearching(false);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    setResult(null);

    const form = new FormData();
    form.append("course_id", String(courseId));
    form.append("file", file);
    if (term) form.append("term", term);

    try {
      const res = await fetch(`${API_BASE}/admin/ingest-syllabus`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? "Upload failed");
      }
      const data: ExtractionResult = await res.json();
      setResult(data);
      if (data.status === "success") onSuccess();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const confidenceColor = (score: number) => {
    if (score >= 0.8) return "text-green-600 bg-green-50 border-green-200";
    if (score >= 0.55) return "text-yellow-700 bg-yellow-50 border-yellow-200";
    return "text-red-600 bg-red-50 border-red-200";
  };

  if (!open) {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={() => setOpen(true)}
          className="text-xs font-medium text-western-purple hover:underline flex items-center gap-1"
        >
          <span>↑</span> Upload Syllabus PDF
        </button>
        <span className="text-gray-300 text-xs">or</span>
        <button
          onClick={handleAutoFind}
          disabled={autoSearching}
          className="text-xs font-medium text-blue-600 hover:underline flex items-center gap-1 disabled:opacity-50"
        >
          {autoSearching ? (
            autoStatus === "searching"
              ? "Searching the web… (this takes ~20s)"
              : autoStatus === "done"
              ? "Found — refreshing…"
              : "Not found"
          ) : (
            <><span>🔍</span> Auto-Find Syllabus</>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="border border-dashed border-gray-300 rounded-xl p-5 bg-gray-50 space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-gray-700">Upload Syllabus PDF</p>
        <button onClick={() => { setOpen(false); setResult(null); setFile(null); }}
          className="text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
      </div>

      {/* File picker */}
      <div
        onClick={() => inputRef.current?.click()}
        className="border border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-western-purple transition bg-white"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => { setFile(e.target.files?.[0] ?? null); setResult(null); }}
        />
        {file ? (
          <p className="text-sm font-medium text-western-purple">{file.name}</p>
        ) : (
          <>
            <p className="text-sm text-gray-500">Click to select a PDF syllabus</p>
            <p className="text-xs text-gray-400 mt-1">Max 20 MB</p>
          </>
        )}
      </div>

      {/* Term (optional) */}
      <input
        className="input"
        placeholder="Term (optional) — e.g. Fall 2024"
        value={term}
        onChange={(e) => setTerm(e.target.value)}
      />

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="w-full bg-western-purple text-white text-sm font-semibold py-2.5 rounded-lg hover:bg-purple-900 transition disabled:opacity-50"
      >
        {uploading ? "Extracting grading scheme…" : "Upload & Extract"}
      </button>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      {/* Results */}
      {result && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${confidenceColor(result.confidence_score)}`}>
              {result.status === "success" ? "Extracted" : "Not found"}
            </span>
            {result.status === "success" && (
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${confidenceColor(result.confidence_score)}`}>
                Confidence: {Math.round(result.confidence_score * 100)}%
              </span>
            )}
          </div>

          {result.status === "no_grading_found" && (
            <p className="text-sm text-gray-500">{result.message}</p>
          )}

          {result.components.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <th className="text-left px-3 py-2 font-semibold text-gray-600">Component</th>
                    <th className="text-right px-3 py-2 font-semibold text-gray-600">Weight</th>
                  </tr>
                </thead>
                <tbody>
                  {result.components.map((c) => (
                    <tr key={c.component_name} className="border-b border-gray-50 last:border-0">
                      <td className="px-3 py-2">{c.component_name}</td>
                      <td className="px-3 py-2 text-right font-semibold">{c.weight}%</td>
                    </tr>
                  ))}
                </tbody>
                {result.total_weight !== undefined && (
                  <tfoot>
                    <tr className="bg-gray-50 border-t border-gray-200">
                      <td className="px-3 py-2 font-semibold">Total</td>
                      <td className={`px-3 py-2 text-right font-bold ${Math.abs(result.total_weight - 100) <= 1 ? "text-green-600" : "text-red-500"}`}>
                        {result.total_weight}%
                      </td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          )}

          {result.notes.length > 0 && (
            <p className="text-xs text-gray-400">{result.notes.join(" ")}</p>
          )}
        </div>
      )}
    </div>
  );
}
