import { useNavigate } from "react-router-dom";
import type { CourseSearchResult } from "../types/course";
import TagBadge from "./TagBadge";
import ScorePill from "./ScorePill";

interface Props {
  course: CourseSearchResult;
}

export default function CourseCard({ course }: Props) {
  const navigate = useNavigate();

  return (
    <div
      onClick={() => navigate(`/courses/${course.id}`)}
      className="bg-white border border-gray-200 rounded-xl p-5 cursor-pointer hover:border-western-purple hover:shadow-md transition"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-western-purple uppercase tracking-wider mb-1">
            {course.course_code}
          </p>
          <h3 className="text-base font-semibold text-gray-900 truncate">
            {course.course_name}
          </h3>
          {course.department && (
            <p className="text-xs text-gray-500 mt-0.5">{course.department}</p>
          )}
        </div>
        <div className="flex gap-2 shrink-0">
          {course.difficulty_score !== null && (
            <ScorePill label="Difficulty" value={course.difficulty_score} />
          )}
          {course.workload_score !== null && (
            <ScorePill label="Workload" value={course.workload_score} />
          )}
        </div>
      </div>
      {course.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {course.tags.map((tag) => (
            <TagBadge key={tag} tag={tag} />
          ))}
        </div>
      )}
    </div>
  );
}
