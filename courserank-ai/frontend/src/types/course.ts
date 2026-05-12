export interface GradingComponent {
  id: number;
  component_name: string;
  weight: number;
  confidence_score: number | null;
}

export interface CourseScore {
  difficulty_score: number | null;
  workload_score: number | null;
  organization_score: number | null;
  assessment_fairness_score: number | null;
  usefulness_score: number | null;
  confidence_score: number | null;
  explanation: string | null;
}

export interface SentimentResult {
  overall_sentiment: string | null;
  sentiment_score: number | null;
  positive_themes: string[];
  negative_themes: string[];
  neutral_themes: string[];
  summary: string | null;
  confidence_score: number | null;
}

export interface CourseSearchResult {
  id: number;
  course_code: string;
  course_name: string;
  department: string | null;
  difficulty_score: number | null;
  workload_score: number | null;
  tags: string[];
}

export interface CourseDetail {
  id: number;
  course_code: string;
  course_name: string;
  department: string | null;
  description: string | null;
  prerequisites: string[];
  antirequisites: string[];
  created_at: string;
  grading_components: GradingComponent[];
  scores: CourseScore | null;
  sentiment: SentimentResult | null;
}

export interface CompareResult {
  course_a: CourseSummary;
  course_b: CourseSummary;
}

export interface CourseSummary {
  id: number;
  course_code: string;
  course_name: string;
  department: string | null;
  grading_components: { component_name: string; weight: number }[];
  scores: Partial<CourseScore>;
  tags: string[];
}
