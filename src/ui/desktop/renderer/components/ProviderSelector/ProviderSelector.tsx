/**
 * ProviderSelector Component
 * UI for selecting NLP and Summary providers (Local, OpenAI, OpenRouter)
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Chip,
  Alert,
  Divider,
  Grid,
  Paper,
  SelectChangeEvent,
} from '@mui/material';
import {
  Computer as LocalIcon,
  Cloud as CloudIcon,
  Psychology as NLPIcon,
  Summarize as SummaryIcon,
  AttachMoney as CostIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';

export interface Provider {
  id: string;
  name: string;
  type: 'local' | 'cloud';
  available: boolean;
  cost_per_request?: number;
  avg_latency_ms?: number;
  capabilities?: string[];
}

export interface ProviderSelectorProps {
  nlpProviders?: Provider[];
  summaryProviders?: Provider[];
  selectedNLPProvider?: string;
  selectedSummaryProvider?: string;
  onNLPProviderChange?: (providerId: string) => void;
  onSummaryProviderChange?: (providerId: string) => void;
}

export const ProviderSelector: React.FC<ProviderSelectorProps> = ({
  nlpProviders = [],
  summaryProviders = [],
  selectedNLPProvider = 'local',
  selectedSummaryProvider = 'local',
  onNLPProviderChange,
  onSummaryProviderChange,
}) => {
  const [nlpProvider, setNlpProvider] = useState(selectedNLPProvider);
  const [summaryProvider, setSummaryProvider] = useState(selectedSummaryProvider);

  const handleNLPChange = (event: SelectChangeEvent) => {
    const value = event.target.value;
    setNlpProvider(value);
    if (onNLPProviderChange) {
      onNLPProviderChange(value);
    }
  };

  const handleSummaryChange = (event: SelectChangeEvent) => {
    const value = event.target.value;
    setSummaryProvider(value);
    if (onSummaryProviderChange) {
      onSummaryProviderChange(value);
    }
  };

  const getProviderById = (providers: Provider[], id: string): Provider | undefined => {
    return providers.find(p => p.id === id);
  };

  const selectedNLP = getProviderById(nlpProviders, nlpProvider);
  const selectedSummary = getProviderById(summaryProviders, summaryProvider);

  const renderProviderInfo = (provider?: Provider) => {
    if (!provider) return null;

    return (
      <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
        <Stack spacing={2}>
          <Stack direction="row" alignItems="center" spacing={1}>
            {provider.type === 'local' ? <LocalIcon /> : <CloudIcon />}
            <Typography variant="subtitle1" fontWeight="bold">
              {provider.name}
            </Typography>
            {provider.available ? (
              <Chip size="small" icon={<CheckCircleIcon />} label="Available" color="success" />
            ) : (
              <Chip size="small" label="Unavailable" color="error" />
            )}
          </Stack>

          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Stack direction="row" spacing={1} alignItems="center">
                <SpeedIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  Latency: {provider.avg_latency_ms ? `${provider.avg_latency_ms}ms` : 'N/A'}
                </Typography>
              </Stack>
            </Grid>
            <Grid item xs={6}>
              <Stack direction="row" spacing={1} alignItems="center">
                <CostIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  Cost: {provider.cost_per_request
                    ? `$${provider.cost_per_request.toFixed(4)}/req`
                    : 'Free'}
                </Typography>
              </Stack>
            </Grid>
          </Grid>

          {provider.capabilities && provider.capabilities.length > 0 && (
            <Box>
              <Typography variant="caption" color="text.secondary">
                Capabilities:
              </Typography>
              <Stack direction="row" spacing={0.5} flexWrap="wrap" mt={0.5}>
                {provider.capabilities.map((cap) => (
                  <Chip key={cap} label={cap} size="small" variant="outlined" />
                ))}
              </Stack>
            </Box>
          )}
        </Stack>
      </Paper>
    );
  };

  const hasCloudProviders = nlpProviders.some(p => p.type === 'cloud') ||
                           summaryProviders.some(p => p.type === 'cloud');

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Provider Selection
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Choose which providers to use for NLP analysis and summarization.
          Cloud providers offer higher accuracy but incur costs.
        </Typography>

        {!hasCloudProviders && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            No cloud providers configured. Configure API keys in settings to enable cloud providers.
          </Alert>
        )}

        <Stack spacing={4}>
          {/* NLP Provider Selection */}
          <Box>
            <Stack direction="row" alignItems="center" spacing={1} mb={2}>
              <NLPIcon color="primary" />
              <Typography variant="h6">NLP Analysis Provider</Typography>
            </Stack>

            <FormControl fullWidth>
              <InputLabel id="nlp-provider-label">NLP Provider</InputLabel>
              <Select
                labelId="nlp-provider-label"
                value={nlpProvider}
                label="NLP Provider"
                onChange={handleNLPChange}
              >
                {nlpProviders.map((provider) => (
                  <MenuItem
                    key={provider.id}
                    value={provider.id}
                    disabled={!provider.available}
                  >
                    <Stack direction="row" spacing={1} alignItems="center">
                      {provider.type === 'local' ? <LocalIcon fontSize="small" /> : <CloudIcon fontSize="small" />}
                      <span>{provider.name}</span>
                      {provider.type === 'cloud' && provider.cost_per_request && (
                        <Chip size="small" label={`$${provider.cost_per_request.toFixed(4)}`} />
                      )}
                    </Stack>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {renderProviderInfo(selectedNLP)}
          </Box>

          <Divider />

          {/* Summary Provider Selection */}
          <Box>
            <Stack direction="row" alignItems="center" spacing={1} mb={2}>
              <SummaryIcon color="primary" />
              <Typography variant="h6">Summary Provider</Typography>
            </Stack>

            <FormControl fullWidth>
              <InputLabel id="summary-provider-label">Summary Provider</InputLabel>
              <Select
                labelId="summary-provider-label"
                value={summaryProvider}
                label="Summary Provider"
                onChange={handleSummaryChange}
              >
                {summaryProviders.map((provider) => (
                  <MenuItem
                    key={provider.id}
                    value={provider.id}
                    disabled={!provider.available}
                  >
                    <Stack direction="row" spacing={1} alignItems="center">
                      {provider.type === 'local' ? <LocalIcon fontSize="small" /> : <CloudIcon fontSize="small" />}
                      <span>{provider.name}</span>
                      {provider.type === 'cloud' && provider.cost_per_request && (
                        <Chip size="small" label={`$${provider.cost_per_request.toFixed(4)}`} />
                      )}
                    </Stack>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {renderProviderInfo(selectedSummary)}
          </Box>
        </Stack>

        {/* Cost Estimation */}
        {(selectedNLP?.cost_per_request || selectedSummary?.cost_per_request) && (
          <Box mt={3}>
            <Alert severity="info">
              <Typography variant="body2">
                <strong>Estimated Cost:</strong> Approximately $
                {((selectedNLP?.cost_per_request || 0) + (selectedSummary?.cost_per_request || 0)).toFixed(4)}
                {' '}per request
              </Typography>
              <Typography variant="caption" display="block" mt={1}>
                Actual costs may vary based on text length and API usage.
              </Typography>
            </Alert>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default ProviderSelector;
