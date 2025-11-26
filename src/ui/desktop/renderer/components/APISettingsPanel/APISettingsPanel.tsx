/**
 * APISettingsPanel Component
 * Configuration UI for external LLM API keys (OpenAI, OpenRouter)
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  IconButton,
  InputAdornment,
  Chip,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Check as CheckIcon,
  Error as ErrorIcon,
  Key as KeyIcon,
  CloudDone as CloudDoneIcon,
  CloudOff as CloudOffIcon,
} from '@mui/icons-material';

export interface APIKeyStatus {
  provider: string;
  hasKey: boolean;
  valid: boolean;
  masked_key?: string;
  connected?: boolean;
  error?: string;
}

export interface APISettingsPanelProps {
  onSaveKey?: (provider: string, apiKey: string) => Promise<void>;
  onTestConnection?: (provider: string) => Promise<boolean>;
  onRemoveKey?: (provider: string) => Promise<void>;
  initialStatus?: Record<string, APIKeyStatus>;
}

export const APISettingsPanel: React.FC<APISettingsPanelProps> = ({
  onSaveKey,
  onTestConnection,
  onRemoveKey,
  initialStatus = {},
}) => {
  const [openaiKey, setOpenaiKey] = useState('');
  const [openrouterKey, setOpenrouterKey] = useState('');
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [showOpenrouterKey, setShowOpenrouterKey] = useState(false);

  const [openaiStatus, setOpenaiStatus] = useState<APIKeyStatus>(
    initialStatus['openai'] || { provider: 'openai', hasKey: false, valid: false }
  );
  const [openrouterStatus, setOpenrouterStatus] = useState<APIKeyStatus>(
    initialStatus['openrouter'] || { provider: 'openrouter', hasKey: false, valid: false }
  );

  const [saving, setSaving] = useState<string | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    // Load initial status
    if (initialStatus['openai']) {
      setOpenaiStatus(initialStatus['openai']);
    }
    if (initialStatus['openrouter']) {
      setOpenrouterStatus(initialStatus['openrouter']);
    }
  }, [initialStatus]);

  const handleSaveKey = async (provider: 'openai' | 'openrouter') => {
    const key = provider === 'openai' ? openaiKey : openrouterKey;

    if (!key || !key.trim()) {
      setMessage({ type: 'error', text: 'API key cannot be empty' });
      return;
    }

    setSaving(provider);
    setMessage(null);

    try {
      if (onSaveKey) {
        await onSaveKey(provider, key);
      }

      // Update status
      const status = { provider, hasKey: true, valid: true, connected: false };
      if (provider === 'openai') {
        setOpenaiStatus(status);
        setOpenaiKey(''); // Clear input after save
      } else {
        setOpenrouterStatus(status);
        setOpenrouterKey('');
      }

      setMessage({ type: 'success', text: `${provider.toUpperCase()} API key saved successfully` });
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to save API key: ${error}` });
    } finally {
      setSaving(null);
    }
  };

  const handleTestConnection = async (provider: 'openai' | 'openrouter') => {
    setTesting(provider);
    setMessage(null);

    try {
      const isConnected = onTestConnection ? await onTestConnection(provider) : false;

      if (provider === 'openai') {
        setOpenaiStatus({ ...openaiStatus, connected: isConnected, error: isConnected ? undefined : 'Connection failed' });
      } else {
        setOpenrouterStatus({ ...openrouterStatus, connected: isConnected, error: isConnected ? undefined : 'Connection failed' });
      }

      setMessage({
        type: isConnected ? 'success' : 'error',
        text: isConnected ? `${provider.toUpperCase()} connection successful` : `${provider.toUpperCase()} connection failed`
      });
    } catch (error) {
      setMessage({ type: 'error', text: `Connection test failed: ${error}` });
    } finally {
      setTesting(null);
    }
  };

  const handleRemoveKey = async (provider: 'openai' | 'openrouter') => {
    if (!confirm(`Are you sure you want to remove the ${provider.toUpperCase()} API key?`)) {
      return;
    }

    try {
      if (onRemoveKey) {
        await onRemoveKey(provider);
      }

      const status = { provider, hasKey: false, valid: false, connected: false };
      if (provider === 'openai') {
        setOpenaiStatus(status);
      } else {
        setOpenrouterStatus(status);
      }

      setMessage({ type: 'success', text: `${provider.toUpperCase()} API key removed` });
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to remove API key: ${error}` });
    }
  };

  const renderProviderSection = (
    provider: 'openai' | 'openrouter',
    key: string,
    setKey: (value: string) => void,
    showKey: boolean,
    setShowKey: (value: boolean) => void,
    status: APIKeyStatus,
    label: string,
    placeholder: string
  ) => (
    <Box>
      <Stack direction="row" alignItems="center" spacing={1} mb={2}>
        <KeyIcon color="primary" />
        <Typography variant="h6">{label}</Typography>
        {status.hasKey && (
          <Chip
            size="small"
            icon={status.connected ? <CloudDoneIcon /> : <CloudOffIcon />}
            label={status.connected ? 'Connected' : 'Not Connected'}
            color={status.connected ? 'success' : 'default'}
          />
        )}
      </Stack>

      {status.hasKey && status.masked_key && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Current key: <code>{status.masked_key}</code>
        </Alert>
      )}

      <Stack spacing={2}>
        <TextField
          fullWidth
          type={showKey ? 'text' : 'password'}
          label="API Key"
          placeholder={placeholder}
          value={key}
          onChange={(e) => setKey(e.target.value)}
          disabled={saving === provider}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowKey(!showKey)}
                  edge="end"
                >
                  {showKey ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            onClick={() => handleSaveKey(provider)}
            disabled={!key || saving === provider}
            startIcon={saving === provider ? <CircularProgress size={16} /> : <CheckIcon />}
          >
            {status.hasKey ? 'Update Key' : 'Save Key'}
          </Button>

          {status.hasKey && (
            <>
              <Button
                variant="outlined"
                onClick={() => handleTestConnection(provider)}
                disabled={testing === provider}
                startIcon={testing === provider ? <CircularProgress size={16} /> : <CloudDoneIcon />}
              >
                Test Connection
              </Button>

              <Button
                variant="outlined"
                color="error"
                onClick={() => handleRemoveKey(provider)}
              >
                Remove Key
              </Button>
            </>
          )}
        </Stack>
      </Stack>
    </Box>
  );

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          External LLM API Settings
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Configure API keys for external LLM providers. Your keys are encrypted and stored securely.
        </Typography>

        {message && (
          <Alert severity={message.type} sx={{ mb: 3 }} onClose={() => setMessage(null)}>
            {message.text}
          </Alert>
        )}

        <Stack spacing={4} divider={<Divider />}>
          {renderProviderSection(
            'openai',
            openaiKey,
            setOpenaiKey,
            showOpenaiKey,
            setShowOpenaiKey,
            openaiStatus,
            'OpenAI (GPT-4)',
            'sk-...'
          )}

          {renderProviderSection(
            'openrouter',
            openrouterKey,
            setOpenrouterKey,
            showOpenrouterKey,
            setShowOpenrouterKey,
            openrouterStatus,
            'OpenRouter (Multi-Model)',
            'sk-or-...'
          )}
        </Stack>

        <Box mt={3}>
          <Alert severity="warning">
            <Typography variant="body2">
              <strong>Security Notice:</strong> API keys are encrypted at rest and never transmitted to our servers.
              They are only used to communicate directly with the provider's API.
            </Typography>
          </Alert>
        </Box>
      </CardContent>
    </Card>
  );
};

export default APISettingsPanel;
