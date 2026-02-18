export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-dark-700 rounded ${className}`} />
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
      <div className="flex items-center gap-3 mb-4">
        <Skeleton className="w-12 h-12 rounded-xl" />
        <div className="flex-1">
          <Skeleton className="h-4 w-32 mb-2" />
          <Skeleton className="h-3 w-48" />
        </div>
      </div>
      <div className="space-y-3">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-2xl overflow-hidden">
      <div className="p-4 border-b border-dark-600">
        <Skeleton className="h-5 w-32" />
      </div>
      <div className="divide-y divide-dark-600">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="p-4 flex items-center gap-3">
            <Skeleton className="w-10 h-10 rounded-lg" />
            <div className="flex-1">
              <Skeleton className="h-4 w-32 mb-2" />
              <Skeleton className="h-3 w-48" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
      <div className="flex items-center gap-3 mb-2">
        <Skeleton className="w-10 h-10 rounded-lg" />
        <Skeleton className="h-4 w-20" />
      </div>
      <Skeleton className="h-8 w-16" />
    </div>
  );
}
