import type { CourseSearchResult, CourseDetail, CompareResult } from "../types/course";
import type { ReviewCreate, ReviewOut } from "../types/review";

// In dev, Vite proxies /api/* to localhost:8000.
// In prod, VITE_API_URL points directly at the Railway backend (no /api prefix).
export const API_BASE = import.meta.env.VITE_API_URL || "/api";
const BASE = API_BASE;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json();
}

export const searchCourses = (query: string) =>
  request<CourseSearchResult[]>(`/courses/search?query=${encodeURIComponent(query)}`);

export const getCourse = (id: number) =>
  request<CourseDetail>(`/courses/${id}`);

export const compareCourses = (course_id_a: number, course_id_b: number) =>
  request<CompareResult>("/courses/compare", {
    method: "POST",
    body: JSON.stringify({ course_id_a, course_id_b }),
  });

export const submitReview = (courseId: number, review: ReviewCreate) =>
  request<ReviewOut>(`/courses/${courseId}/reviews`, {
    method: "POST",
    body: JSON.stringify(review),
  });

export const getReviews = (courseId: number) =>
  request<ReviewOut[]>(`/courses/${courseId}/reviews`);

export const flagReview = (courseId: number, reviewId: number) =>
  request<{ status: string }>(`/courses/${courseId}/reviews/${reviewId}/flag`, {
    method: "POST",
  });
