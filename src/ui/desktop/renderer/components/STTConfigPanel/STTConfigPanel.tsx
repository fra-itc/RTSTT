/**
 * STT Configuration Panel Component
 *
 * Allows users to configure STT provider settings, API keys,
 * and provider-specific options.
 */

import React, { useState, useEffect } from 'react';

interface ProviderConfig {
  apiKey: string;
  model: string;
  language: string;
  features: {
    punctuation?: boolean;
    diarization?: boolean;
    smartFormat?: boolean;
    sentimentAnalysis?: boolean;
  };
}

interface STTConfigPanelProps {
  selectedProvider: string;
  config: Record<string, ProviderConfig>;
  onConfigChange: (provider: string, config: ProviderConfig) => void;
  onTestConnection: (provider: string) => Promise<boolean>;
  className?: string;
}

// Provider-specific model options
const PROVIDER_MODELS: Record<string, string[]> = {
  local_whisper: ['large-v3', 'large-v2', 'medium', 'small', 'base', 'tiny'],
  openai: ['whisper-1'],
  deepgram: ['nova-3', 'nova-2', 'whisper-large', 'whisper-medium', 'base'],
  assemblyai: ['best', 'nano'],
};

// Provider-specific features
const PROVIDER_FEATURES: Record<
  string,
  Array<{ key: string; label: string; description: string }>
> = {
  local_whisper: [],
  openai: [],
  deepgram: [
    {
      key: 'punctuation',
      label: 'Punctuation',
      description: 'Add punctuation to transcription',
    },
    {
      key: 'diarization',
      label: 'Speaker Diarization',
      description: 'Identify different speakers',
    },
    {
      key: 'smartFormat',
      label: 'Smart Formatting',
      description: 'Apply smart formatting rules',
    },
  ],
  assemblyai: [
    {
      key: 'diarization',
      label: 'Speaker Labels',
      description: 'Identify different speakers',
    },
    {
      key: 'sentimentAnalysis',
      label: 'Sentiment Analysis',
      description: 'Analyze sentiment of transcription',
    },
  ],
};

export const STTConfigPanel: React.FC<STTConfigPanelProps> = ({
  selectedProvider,
  config,
  onConfigChange,
  onTestConnection,
  className = '',
}) => {
  const [currentConfig, setCurrentConfig] = useState<ProviderConfig>(
    config[selectedProvider] || {
      apiKey: '',
      model: PROVIDER_MODELS[selectedProvider]?.[0] || '',
      language: 'it',
      features: {},
    }
  );

  const [showApiKey, setShowApiKey] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  // Update local config when selected provider changes
  useEffect(() => {
    setCurrentConfig(
      config[selectedProvider] || {
        apiKey: '',
        model: PROVIDER_MODELS[selectedProvider]?.[0] || '',
        language: 'it',
        features: {},
      }
    );
    setTestResult(null);
  }, [selectedProvider, config]);

  const handleConfigChange = (updates: Partial<ProviderConfig>) => {
    const newConfig = { ...currentConfig, ...updates };
    setCurrentConfig(newConfig);
    onConfigChange(selectedProvider, newConfig);
  };

  const handleFeatureToggle = (featureKey: string) => {
    const newFeatures = {
      ...currentConfig.features,
      [featureKey]: !currentConfig.features[featureKey],
    };
    handleConfigChange({ features: newFeatures });
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setTestResult(null);

    try {
      const success = await onTestConnection(selectedProvider);
      setTestResult(success ? 'success' : 'error');
    } catch (error) {
      setTestResult('error');
    } finally {
      setTestingConnection(false);
    }
  };

  const requiresApiKey = !['local_whisper'].includes(selectedProvider);
  const availableModels = PROVIDER_MODELS[selectedProvider] || [];
  const availableFeatures = PROVIDER_FEATURES[selectedProvider] || [];

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Provider Configuration
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Configure settings for {selectedProvider}
        </p>
      </div>

      {/* API Key */}
      {requiresApiKey && (
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            API Key
          </label>
          <div className="flex gap-2">
            <input
              type={showApiKey ? 'text' : 'password'}
              value={currentConfig.apiKey}
              onChange={(e) => handleConfigChange({ apiKey: e.target.value })}
              placeholder="Enter your API key"
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={() => setShowApiKey(!showApiKey)}
              className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              {showApiKey ? 'Hide' : 'Show'}
            </button>
          </div>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Your API key is stored securely and never sent to our servers
          </p>
        </div>
      )}

      {/* Model Selection */}
      {availableModels.length > 1 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Model
          </label>
          <select
            value={currentConfig.model}
            onChange={(e) => handleConfigChange({ model: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {availableModels.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Language Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Default Language
        </label>
        <select
          value={currentConfig.language}
          onChange={(e) => handleConfigChange({ language: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="it">Italian</option>
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="pt">Portuguese</option>
          <option value="auto">Auto-detect</option>
        </select>
      </div>

      {/* Provider-specific Features */}
      {availableFeatures.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Features
          </label>
          <div className="space-y-3">
            {availableFeatures.map((feature) => (
              <div
                key={feature.key}
                className="flex items-start justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {feature.label}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {feature.description}
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={currentConfig.features[feature.key] || false}
                    onChange={() => handleFeatureToggle(feature.key)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Test Connection */}
      {requiresApiKey && (
        <div>
          <button
            onClick={handleTestConnection}
            disabled={!currentConfig.apiKey || testingConnection}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {testingConnection ? 'Testing Connection...' : 'Test Connection'}
          </button>

          {testResult === 'success' && (
            <div className="mt-2 p-3 rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
              <p className="text-sm text-green-800 dark:text-green-200">
                Connection successful! Provider is ready to use.
              </p>
            </div>
          )}

          {testResult === 'error' && (
            <div className="mt-2 p-3 rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-800 dark:text-red-200">
                Connection failed. Please check your API key and try again.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Configuration Summary */}
      <div className="p-4 rounded-lg bg-gray-100 dark:bg-gray-800">
        <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Configuration Summary
        </h4>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Provider:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {selectedProvider}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Model:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {currentConfig.model}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Language:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {currentConfig.language}
            </span>
          </div>
          {Object.entries(currentConfig.features).filter(([_, v]) => v).length > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Active Features:</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {Object.entries(currentConfig.features)
                  .filter(([_, enabled]) => enabled)
                  .map(([key]) => key)
                  .join(', ')}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default STTConfigPanel;
