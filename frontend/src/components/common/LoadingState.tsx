interface LoadingStateProps {
  rows?: number;
}

export function LoadingState({ rows = 3 }: LoadingStateProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div className="h-24 animate-pulse rounded-lg border border-slate-200 bg-slate-50" key={index} />
      ))}
    </div>
  );
}

