import React from "react";

/**
 * Skeleton loader for the report viewer to show loading state
 * with an animated shimmer effect.
 */
function SkeletonLoader() {
  return (
    <div className="space-y-8 p-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="space-y-4">
        <div className="h-8 w-3/4 rounded-md bg-slate-200 dark:bg-slate-700"></div>
        <div className="flex gap-4">
          <div className="h-4 w-24 rounded-md bg-slate-200 dark:bg-slate-700"></div>
          <div className="h-4 w-32 rounded-md bg-slate-200 dark:bg-slate-700"></div>
        </div>
      </div>

      <hr className="border-slate-200 dark:border-slate-700" />

      {/* Overview Skeleton */}
      <div className="space-y-3">
        <div className="h-6 w-48 rounded-md bg-slate-200 dark:bg-slate-700"></div>
        <div className="h-4 w-full rounded-md bg-slate-200 dark:bg-slate-700"></div>
        <div className="h-4 w-full rounded-md bg-slate-200 dark:bg-slate-700"></div>
        <div className="h-4 w-5/6 rounded-md bg-slate-200 dark:bg-slate-700"></div>
      </div>

      {/* Bullet Points Skeleton */}
      <div className="space-y-4">
        <div className="h-6 w-40 rounded-md bg-slate-200 dark:bg-slate-700"></div>
        <div className="space-y-3 pl-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex gap-3">
              <div className="mt-1.5 h-2 w-2 rounded-full bg-slate-200 dark:bg-slate-700"></div>
              <div className="h-4 w-full rounded-md bg-slate-200 dark:bg-slate-700"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default SkeletonLoader;
