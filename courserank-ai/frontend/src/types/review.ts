export interface ReviewCreate {
  professor_name?: string;
  term_taken?: string;
  difficulty_rating?: number;
  workload_rating?: number;
  hours_per_week?: number;
  organization_rating?: number;
  assessment_fairness_rating?: number;
  usefulness_rating?: number;
  review_text?: string;
  would_recommend?: boolean;
}

export interface ReviewOut extends ReviewCreate {
  id: number;
  created_at: string;
}
