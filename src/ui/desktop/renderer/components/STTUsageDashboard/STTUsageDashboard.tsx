/**
 * STT Usage Dashboard Component
 *
 * Displays real-time cost tracking, usage statistics, and
 * comparison charts for different STT providers.
 */

import React, { useState, useEffect } from 'react';

interface UsageStats {
  totalCost: number;
  totalDurationSeconds: number;
  totalRequests: number;
  providerStats: Record<
    string,
    {
      totalRequests: number;
      successfulRequests: number;
      failedRequests: number;
      totalDuration: number;
      totalCost: number;
    }
  >;
}

interface STTUsageDashboardProps {
  className?: string;
}

export const STTUsageDashboard: React.FC<STTUsageDashboardProps> = ({
  className = '',
}) => {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [timeRange, setTimeRange] = useState<'today' | 'week' | 'month' | 'all'>('today');
  const [loading, setLoading] = useState(true);

  // Mock data for demonstration
  const mockStats: UsageStats = {
    totalCost: 2.45,
    totalDurationSeconds: 3600,
    totalRequests: 45,
    providerStats: {
      local_whisper: {
        totalRequests: 20,
        successfulRequests: 20,
        failedRequests: 0,
        totalDuration: 1800,
        totalCost: 0,
      },
      openai: {
        totalRequests: 15,
        successfulRequests: 14,
        failedRequests: 1,
        totalDuration: 1200,
        totalCost: 0.12,
      },
      deepgram: {
        totalRequests: 10,
        successfulRequests: 10,
        failedRequests: 0,
        totalDuration: 600,
        totalCost: 0.06,
      },
    },
  };

  useEffect(() => {
    // TODO: Fetch actual stats from backend
    setTimeout(() => {
      setStats(mockStats);
      setLoading(false);
    }, 500);
  }, [timeRange]);

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatCost = (cost: number) => {
    return cost === 0 ? 'Free' : `$${cost.toFixed(2)}`;
  };

  const getSuccessRate = (successful: number, total: number) => {
    if (total === 0) return 0;
    return ((successful / total) * 100).toFixed(1);
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-gray-500 dark:text-gray-400">Loading usage data...</div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-gray-500 dark:text-gray-400">No usage data available</div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Usage Dashboard
        </h3>
        <div className="flex gap-2">
          {(['today', 'week', 'month', 'all'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              {range.charAt(0).toUpperCase() + range.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">
            Total Cost
          </div>
          <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
            {formatCost(stats.totalCost)}
          </div>
        </div>

        <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
          <div className="text-sm text-green-600 dark:text-green-400 mb-1">
            Total Duration
          </div>
          <div className="text-2xl font-bold text-green-900 dark:text-green-100">
            {formatDuration(stats.totalDurationSeconds)}
          </div>
        </div>

        <div className="p-4 rounded-lg bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
          <div className="text-sm text-purple-600 dark:text-purple-400 mb-1">
            Total Requests
          </div>
          <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
            {stats.totalRequests}
          </div>
        </div>
      </div>

      {/* Provider Breakdown */}
      <div>
        <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
          Provider Breakdown
        </h4>
        <div className="space-y-3">
          {Object.entries(stats.providerStats).map(([provider, data]) => (
            <div
              key={provider}
              className="p-4 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center justify-between mb-3">
                <h5 className="font-semibold text-gray-900 dark:text-gray-100">
                  {provider}
                </h5>
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {formatCost(data.totalCost)}
                </span>
              </div>

              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-gray-600 dark:text-gray-400 mb-1">
                    Requests
                  </div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100">
                    {data.totalRequests}
                  </div>
                </div>

                <div>
                  <div className="text-gray-600 dark:text-gray-400 mb-1">
                    Success Rate
                  </div>
                  <div className="font-semibold text-green-600 dark:text-green-400">
                    {getSuccessRate(data.successfulRequests, data.totalRequests)}%
                  </div>
                </div>

                <div>
                  <div className="text-gray-600 dark:text-gray-400 mb-1">
                    Duration
                  </div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100">
                    {formatDuration(data.totalDuration)}
                  </div>
                </div>

                <div>
                  <div className="text-gray-600 dark:text-gray-400 mb-1">
                    Failures
                  </div>
                  <div
                    className={`font-semibold ${
                      data.failedRequests > 0
                        ? 'text-red-600 dark:text-red-400'
                        : 'text-gray-900 dark:text-gray-100'
                    }`}
                  >
                    {data.failedRequests}
                  </div>
                </div>
              </div>

              {/* Usage Bar */}
              <div className="mt-3">
                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 rounded-full"
                    style={{
                      width: `${
                        (data.totalDuration / stats.totalDurationSeconds) * 100
                      }%`,
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cost Comparison Chart */}
      <div>
        <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
          Cost Comparison
        </h4>
        <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="space-y-2">
            {Object.entries(stats.providerStats)
              .sort((a, b) => b[1].totalCost - a[1].totalCost)
              .map(([provider, data]) => {
                const percentage =
                  stats.totalCost > 0 ? (data.totalCost / stats.totalCost) * 100 : 0;
                return (
                  <div key={provider}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-700 dark:text-gray-300">
                        {provider}
                      </span>
                      <span className="text-gray-900 dark:text-gray-100 font-medium">
                        {formatCost(data.totalCost)} ({percentage.toFixed(0)}%)
                      </span>
                    </div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      </div>

      {/* Export Button */}
      <div className="flex justify-end">
        <button
          onClick={() => {
            // TODO: Implement export functionality
            console.log('Exporting usage report...');
          }}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          Export Report
        </button>
      </div>
    </div>
  );
};

export default STTUsageDashboard;
