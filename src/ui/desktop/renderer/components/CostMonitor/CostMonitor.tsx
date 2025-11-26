/**
 * CostMonitor Component
 * Real-time cost tracking dashboard for external LLM APIs
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Grid,
  Paper,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ToggleButton,
  ToggleButtonGroup,
  LinearProgress,
} from '@mui/material';
import {
  AttachMoney as MoneyIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

export interface CostEntry {
  timestamp: Date;
  provider: string;
  service: 'nlp' | 'summary';
  model: string;
  tokens: number;
  cost_usd: number;
  request_id?: string;
}

export interface CostStats {
  total_cost: number;
  total_requests: number;
  total_tokens: number;
  avg_cost_per_request: number;
  by_provider: Record<string, {
    cost: number;
    requests: number;
    tokens: number;
  }>;
  by_service: Record<string, {
    cost: number;
    requests: number;
    tokens: number;
  }>;
}

export interface CostMonitorProps {
  entries?: CostEntry[];
  stats?: CostStats;
  timeRange?: 'daily' | 'weekly' | 'monthly';
  onTimeRangeChange?: (range: 'daily' | 'weekly' | 'monthly') => void;
  onRefresh?: () => void;
  onExport?: () => void;
  isLoading?: boolean;
}

export const CostMonitor: React.FC<CostMonitorProps> = ({
  entries = [],
  stats,
  timeRange = 'daily',
  onTimeRangeChange,
  onRefresh,
  onExport,
  isLoading = false,
}) => {
  const [selectedRange, setSelectedRange] = useState<'daily' | 'weekly' | 'monthly'>(timeRange);

  const handleRangeChange = (
    event: React.MouseEvent<HTMLElement>,
    newRange: 'daily' | 'weekly' | 'monthly' | null,
  ) => {
    if (newRange !== null) {
      setSelectedRange(newRange);
      if (onTimeRangeChange) {
        onTimeRangeChange(newRange);
      }
    }
  };

  // Calculate stats if not provided
  const calculatedStats = useMemo((): CostStats => {
    if (stats) return stats;

    const defaultStats: CostStats = {
      total_cost: 0,
      total_requests: 0,
      total_tokens: 0,
      avg_cost_per_request: 0,
      by_provider: {},
      by_service: {},
    };

    entries.forEach((entry) => {
      defaultStats.total_cost += entry.cost_usd;
      defaultStats.total_requests += 1;
      defaultStats.total_tokens += entry.tokens;

      // By provider
      if (!defaultStats.by_provider[entry.provider]) {
        defaultStats.by_provider[entry.provider] = { cost: 0, requests: 0, tokens: 0 };
      }
      defaultStats.by_provider[entry.provider].cost += entry.cost_usd;
      defaultStats.by_provider[entry.provider].requests += 1;
      defaultStats.by_provider[entry.provider].tokens += entry.tokens;

      // By service
      if (!defaultStats.by_service[entry.service]) {
        defaultStats.by_service[entry.service] = { cost: 0, requests: 0, tokens: 0 };
      }
      defaultStats.by_service[entry.service].cost += entry.cost_usd;
      defaultStats.by_service[entry.service].requests += 1;
      defaultStats.by_service[entry.service].tokens += entry.tokens;
    });

    if (defaultStats.total_requests > 0) {
      defaultStats.avg_cost_per_request = defaultStats.total_cost / defaultStats.total_requests;
    }

    return defaultStats;
  }, [entries, stats]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <AssessmentIcon color="primary" fontSize="large" />
            <Typography variant="h5">Cost Monitor</Typography>
          </Stack>

          <Stack direction="row" spacing={1}>
            <ToggleButtonGroup
              value={selectedRange}
              exclusive
              onChange={handleRangeChange}
              size="small"
            >
              <ToggleButton value="daily">Daily</ToggleButton>
              <ToggleButton value="weekly">Weekly</ToggleButton>
              <ToggleButton value="monthly">Monthly</ToggleButton>
            </ToggleButtonGroup>

            <Button
              size="small"
              startIcon={<RefreshIcon />}
              onClick={onRefresh}
              disabled={isLoading}
            >
              Refresh
            </Button>

            <Button
              size="small"
              startIcon={<DownloadIcon />}
              onClick={onExport}
              variant="outlined"
            >
              Export
            </Button>
          </Stack>
        </Stack>

        {isLoading && <LinearProgress sx={{ mb: 2 }} />}

        {/* Summary Cards */}
        <Grid container spacing={2} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, bgcolor: 'primary.50' }}>
              <Stack spacing={1}>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <MoneyIcon color="primary" fontSize="small" />
                  <Typography variant="caption" color="text.secondary">
                    Total Cost
                  </Typography>
                </Stack>
                <Typography variant="h5" fontWeight="bold">
                  {formatCurrency(calculatedStats.total_cost)}
                </Typography>
              </Stack>
            </Paper>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2 }}>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  Total Requests
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {formatNumber(calculatedStats.total_requests)}
                </Typography>
              </Stack>
            </Paper>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2 }}>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  Total Tokens
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {formatNumber(calculatedStats.total_tokens)}
                </Typography>
              </Stack>
            </Paper>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2 }}>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  Avg Cost/Request
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {formatCurrency(calculatedStats.avg_cost_per_request)}
                </Typography>
              </Stack>
            </Paper>
          </Grid>
        </Grid>

        {/* Breakdown by Provider */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Cost by Provider
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Provider</TableCell>
                  <TableCell align="right">Requests</TableCell>
                  <TableCell align="right">Tokens</TableCell>
                  <TableCell align="right">Cost</TableCell>
                  <TableCell align="right">% of Total</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(calculatedStats.by_provider).map(([provider, data]) => (
                  <TableRow key={provider}>
                    <TableCell>
                      <Chip label={provider} size="small" />
                    </TableCell>
                    <TableCell align="right">{formatNumber(data.requests)}</TableCell>
                    <TableCell align="right">{formatNumber(data.tokens)}</TableCell>
                    <TableCell align="right">{formatCurrency(data.cost)}</TableCell>
                    <TableCell align="right">
                      {calculatedStats.total_cost > 0
                        ? ((data.cost / calculatedStats.total_cost) * 100).toFixed(1)
                        : '0'}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>

        {/* Breakdown by Service */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Cost by Service
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Service</TableCell>
                  <TableCell align="right">Requests</TableCell>
                  <TableCell align="right">Tokens</TableCell>
                  <TableCell align="right">Cost</TableCell>
                  <TableCell align="right">% of Total</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(calculatedStats.by_service).map(([service, data]) => (
                  <TableRow key={service}>
                    <TableCell>
                      <Chip label={service.toUpperCase()} size="small" color="primary" />
                    </TableCell>
                    <TableCell align="right">{formatNumber(data.requests)}</TableCell>
                    <TableCell align="right">{formatNumber(data.tokens)}</TableCell>
                    <TableCell align="right">{formatCurrency(data.cost)}</TableCell>
                    <TableCell align="right">
                      {calculatedStats.total_cost > 0
                        ? ((data.cost / calculatedStats.total_cost) * 100).toFixed(1)
                        : '0'}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>

        {/* Recent Transactions */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Recent Transactions
          </Typography>
          <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 300 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Provider</TableCell>
                  <TableCell>Service</TableCell>
                  <TableCell>Model</TableCell>
                  <TableCell align="right">Tokens</TableCell>
                  <TableCell align="right">Cost</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {entries.slice(0, 50).map((entry, index) => (
                  <TableRow key={entry.request_id || index}>
                    <TableCell>
                      <Typography variant="caption">
                        {entry.timestamp.toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={entry.provider} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Chip label={entry.service} size="small" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">{entry.model}</Typography>
                    </TableCell>
                    <TableCell align="right">{formatNumber(entry.tokens)}</TableCell>
                    <TableCell align="right">{formatCurrency(entry.cost_usd)}</TableCell>
                  </TableRow>
                ))}
                {entries.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No transactions yet
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </CardContent>
    </Card>
  );
};

export default CostMonitor;
