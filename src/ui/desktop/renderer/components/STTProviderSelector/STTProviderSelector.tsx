/**
 * STT Provider Selector Component
 *
 * Allows users to select and switch between different STT providers
 * with real-time cost estimates and capability indicators.
 */

import React, { useState, useEffect } from 'react';

// Provider information types
interface ProviderInfo {
  name: string;
  displayName: string;
  type: 'local' | 'cloud';
  costPerMinute: number | null;
  latencyMs: number;
  capabilities: {
    streaming: boolean;
    diarization: boolean;
    wordTimestamps: boolean;
    translation: boolean;
  };
  requiresApiKey: boolean;
  requiresGpu: boolean;
  models: string[];
  isHealthy?: boolean;
}

// Available providers
const PROVIDERS: ProviderInfo[] = [
  {
    name: 'local_whisper',
    displayName: 'Local Whisper Large-v3',
    type: 'local',
    costPerMinute: 0,
    latencyMs: 300,
    capabilities: {
      streaming: true,
      diarization: false,
      wordTimestamps: true,
      translation: true,
    },
    requiresApiKey: false,
    requiresGpu: true,
    models: ['large-v3', 'large-v2', 'medium', 'small'],
  },
  {
    name: 'openai',
    displayName: 'OpenAI Whisper API',
    type: 'cloud',
    costPerMinute: 0.006,
    latencyMs: 2000,
    capabilities: {
      streaming: false,
      diarization: false,
      wordTimestamps: true,
      translation: true,
    },
    requiresApiKey: true,
    requiresGpu: false,
    models: ['whisper-1'],
  },
  {
    name: 'deepgram',
    displayName: 'Deepgram Nova-3',
    type: 'cloud',
    costPerMinute: 0.0059,
    latencyMs: 50,
    capabilities: {
      streaming: true,
      diarization: true,
      wordTimestamps: true,
      translation: false,
    },
    requiresApiKey: true,
    requiresGpu: false,
    models: ['nova-3', 'nova-2', 'whisper-large'],
  },
  {
    name: 'assemblyai',
    displayName: 'AssemblyAI Universal-2',
    type: 'cloud',
    costPerMinute: 0.015,
    latencyMs: 5000,
    capabilities: {
      streaming: false,
      diarization: true,
      wordTimestamps: true,
      translation: false,
    },
    requiresApiKey: true,
    requiresGpu: false,
    models: ['best', 'nano'],
  },
];

interface STTProviderSelectorProps {
  selectedProvider: string;
  onProviderChange: (providerName: string) => void;
  estimatedMinutesPerDay?: number;
  className?: string;
}

export const STTProviderSelector: React.FC<STTProviderSelectorProps> = ({
  selectedProvider,
  onProviderChange,
  estimatedMinutesPerDay = 60,
  className = '',
}) => {
  const [healthStatus, setHealthStatus] = useState<Record<string, boolean>>({});

  // Check provider health on mount
  useEffect(() => {
    checkProviderHealth();
  }, []);

  const checkProviderHealth = async () => {
    // TODO: Call backend API to check health
    // For now, mock it
    const mockHealth: Record<string, boolean> = {
      local_whisper: true,
      openai: true,
      deepgram: true,
      assemblyai: true,
    };
    setHealthStatus(mockHealth);
  };

  const calculateMonthlyCost = (costPerMinute: number | null) => {
    if (costPerMinute === null || costPerMinute === 0) return 'Free';
    const monthly = costPerMinute * estimatedMinutesPerDay * 30;
    return `$${monthly.toFixed(2)}/mo`;
  };

  const getProviderBadge = (provider: ProviderInfo) => {
    const badges = [];

    if (provider.type === 'local') {
      badges.push(
        <span
          key="local"
          className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
        >
          Local
        </span>
      );
    }

    if (provider.costPerMinute === 0) {
      badges.push(
        <span
          key="free"
          className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
        >
          Free
        </span>
      );
    }

    if (provider.capabilities.streaming) {
      badges.push(
        <span
          key="streaming"
          className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
        >
          Streaming
        </span>
      );
    }

    if (provider.capabilities.diarization) {
      badges.push(
        <span
          key="diarization"
          className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
        >
          Diarization
        </span>
      );
    }

    return badges;
  };

  const getHealthIndicator = (providerName: string) => {
    const isHealthy = healthStatus[providerName];

    if (isHealthy === undefined) {
      return (
        <div className="w-3 h-3 rounded-full bg-gray-400" title="Unknown" />
      );
    }

    return (
      <div
        className={`w-3 h-3 rounded-full ${
          isHealthy ? 'bg-green-500' : 'bg-red-500'
        }`}
        title={isHealthy ? 'Healthy' : 'Unhealthy'}
      />
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          STT Provider
        </h3>
        <button
          onClick={checkProviderHealth}
          className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
        >
          Check Health
        </button>
      </div>

      <div className="space-y-2">
        {PROVIDERS.map((provider) => (
          <div
            key={provider.name}
            onClick={() => onProviderChange(provider.name)}
            className={`
              p-4 rounded-lg border-2 cursor-pointer transition-all
              ${
                selectedProvider === provider.name
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }
            `}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {getHealthIndicator(provider.name)}
                  <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                    {provider.displayName}
                  </h4>
                </div>

                <div className="flex flex-wrap gap-2 mb-2">
                  {getProviderBadge(provider)}
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <div>
                    <span className="font-medium">Cost:</span>{' '}
                    {provider.costPerMinute === 0
                      ? 'Free'
                      : `$${provider.costPerMinute.toFixed(4)}/min`}
                  </div>
                  <div>
                    <span className="font-medium">Latency:</span>{' '}
                    {provider.latencyMs}ms
                  </div>
                  {estimatedMinutesPerDay > 0 && (
                    <div>
                      <span className="font-medium">Est. Monthly:</span>{' '}
                      {calculateMonthlyCost(provider.costPerMinute)}
                    </div>
                  )}
                  <div>
                    <span className="font-medium">Models:</span>{' '}
                    {provider.models.length}
                  </div>
                </div>

                {provider.requiresApiKey && (
                  <div className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                    Requires API key
                  </div>
                )}

                {provider.requiresGpu && (
                  <div className="mt-2 text-xs text-purple-600 dark:text-purple-400">
                    Requires GPU (8GB+ VRAM)
                  </div>
                )}
              </div>

              <div className="ml-4">
                <input
                  type="radio"
                  checked={selectedProvider === provider.name}
                  onChange={() => onProviderChange(provider.name)}
                  className="w-5 h-5"
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 rounded-lg bg-gray-100 dark:bg-gray-800">
        <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Estimation for {estimatedMinutesPerDay} min/day
        </h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-gray-600 dark:text-gray-400">Daily Cost:</div>
          <div className="font-semibold text-gray-900 dark:text-gray-100">
            {(() => {
              const selected = PROVIDERS.find((p) => p.name === selectedProvider);
              if (!selected || selected.costPerMinute === 0) return 'Free';
              const daily = selected.costPerMinute * estimatedMinutesPerDay;
              return `$${daily.toFixed(2)}`;
            })()}
          </div>
          <div className="text-gray-600 dark:text-gray-400">Monthly Cost:</div>
          <div className="font-semibold text-gray-900 dark:text-gray-100">
            {(() => {
              const selected = PROVIDERS.find((p) => p.name === selectedProvider);
              return calculateMonthlyCost(selected?.costPerMinute ?? null);
            })()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default STTProviderSelector;
