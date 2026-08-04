interface HealthScoreBadgeProps {
  branch: string;
  score: number;
}

function scoreClasses(score: number) {
  if (score >= 85) return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (score >= 70) return "bg-amber-50 text-amber-700 border-amber-200";
  return "bg-red-50 text-red-700 border-red-200";
}

export function HealthScoreBadge({ branch, score }: HealthScoreBadgeProps) {
  return (
    <div className={`flex items-center justify-between gap-3 rounded-md border px-3 py-2 ${scoreClasses(score)}`}>
      <span className="truncate text-sm font-medium">{branch}</span>
      <span className="text-sm font-semibold tabular-nums">{score}</span>
    </div>
  );
}

