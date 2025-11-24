/**
 * InsightsPanel Component
 * Displays NLP insights: keywords, named entities, and sentiment analysis
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Stack,
  Skeleton,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Label as LabelIcon,
  Psychology as PsychologyIcon,
  SentimentSatisfied as SentimentPositiveIcon,
  SentimentNeutral as SentimentNeutralIcon,
  SentimentDissatisfied as SentimentNegativeIcon,
} from '@mui/icons-material';

export interface Keyword {
  keyword: string;
  score: number;
}

export interface NamedEntity {
  text: string;
  type: string;
  confidence?: number;
}

export interface Sentiment {
  label: string;
  score: number;
  positive?: number;
  neutral?: number;
  negative?: number;
}

export interface InsightsPanelProps {
  keywords?: Keyword[];
  entities?: NamedEntity[];
  sentiment?: Sentiment;
  isLoading?: boolean;
  isEmpty?: boolean;
}

const getSentimentIcon = (label: string) => {
  const normalized = label.toLowerCase();
  if (normalized.includes('positive')) return <SentimentPositiveIcon />;
  if (normalized.includes('negative')) return <SentimentNegativeIcon />;
  return <SentimentNeutralIcon />;
};

const getSentimentColor = (label: string): 'success' | 'error' | 'default' => {
  const normalized = label.toLowerCase();
  if (normalized.includes('positive')) return 'success';
  if (normalized.includes('negative')) return 'error';
  return 'default';
};

const getEntityColor = (type: string): 'primary' | 'secondary' | 'info' | 'warning' | 'error' | 'default' => {
  const normalized = type.toUpperCase();
  if (normalized === 'PERSON' || normalized === 'PER') return 'primary';
  if (normalized === 'ORG' || normalized === 'ORGANIZATION') return 'secondary';
  if (normalized === 'LOC' || normalized === 'LOCATION' || normalized === 'GPE') return 'info';
  if (normalized === 'DATE' || normalized === 'TIME') return 'warning';
  if (normalized === 'MISC' || normalized === 'MISCELLANEOUS') return 'error';
  return 'default';
};

export const InsightsPanel: React.FC<InsightsPanelProps> = ({
  keywords = [],
  entities = [],
  sentiment,
  isLoading = false,
  isEmpty = false,
}) => {
  // Show empty state
  if (isEmpty && !isLoading) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Stack spacing={2} alignItems="center" justifyContent="center" sx={{ minHeight: 300 }}>
            <PsychologyIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
            <Typography variant="h6" color="text.secondary" align="center">
              No Insights Yet
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Start recording to see NLP insights
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1, overflow: 'auto' }}>
        <Stack spacing={3}>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PsychologyIcon color="primary" />
            <Typography variant="h6">NLP Insights</Typography>
          </Box>

          {/* Keywords Section */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
              <TrendingUpIcon fontSize="small" color="action" />
              <Typography variant="subtitle2" color="text.secondary">
                Keywords
              </Typography>
            </Box>
            {isLoading ? (
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} variant="rounded" width={80} height={32} />
                ))}
              </Stack>
            ) : keywords.length > 0 ? (
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {keywords.map((kw, index) => (
                  <Chip
                    key={index}
                    label={kw.keyword}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{
                      opacity: Math.max(0.5, kw.score),
                      fontWeight: 500,
                    }}
                  />
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary" fontStyle="italic">
                No keywords extracted yet
              </Typography>
            )}
          </Box>

          <Divider />

          {/* Named Entities Section */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
              <LabelIcon fontSize="small" color="action" />
              <Typography variant="subtitle2" color="text.secondary">
                Named Entities
              </Typography>
            </Box>
            {isLoading ? (
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} variant="rounded" width={100} height={32} />
                ))}
              </Stack>
            ) : entities.length > 0 ? (
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {entities.map((entity, index) => (
                  <Chip
                    key={index}
                    label={`${entity.text} (${entity.type})`}
                    size="small"
                    color={getEntityColor(entity.type)}
                    sx={{ fontWeight: 500 }}
                  />
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary" fontStyle="italic">
                No entities detected yet
              </Typography>
            )}
          </Box>

          <Divider />

          {/* Sentiment Analysis Section */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
              {sentiment ? getSentimentIcon(sentiment.label) : <SentimentNeutralIcon fontSize="small" color="action" />}
              <Typography variant="subtitle2" color="text.secondary">
                Sentiment Analysis
              </Typography>
            </Box>
            {isLoading ? (
              <Skeleton variant="rounded" width="100%" height={80} />
            ) : sentiment ? (
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Chip
                    icon={getSentimentIcon(sentiment.label)}
                    label={sentiment.label}
                    color={getSentimentColor(sentiment.label)}
                    sx={{ fontWeight: 600 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Confidence: {(sentiment.score * 100).toFixed(1)}%
                  </Typography>
                </Box>

                {/* Sentiment breakdown if available */}
                {(sentiment.positive !== undefined || sentiment.neutral !== undefined || sentiment.negative !== undefined) && (
                  <Stack spacing={1}>
                    {sentiment.positive !== undefined && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ minWidth: 80 }}>
                          Positive:
                        </Typography>
                        <Box
                          sx={{
                            flexGrow: 1,
                            height: 8,
                            bgcolor: 'action.hover',
                            borderRadius: 1,
                            overflow: 'hidden',
                          }}
                        >
                          <Box
                            sx={{
                              width: `${sentiment.positive * 100}%`,
                              height: '100%',
                              bgcolor: 'success.main',
                              transition: 'width 0.3s ease',
                            }}
                          />
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ minWidth: 50, textAlign: 'right' }}>
                          {(sentiment.positive * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    )}
                    {sentiment.neutral !== undefined && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ minWidth: 80 }}>
                          Neutral:
                        </Typography>
                        <Box
                          sx={{
                            flexGrow: 1,
                            height: 8,
                            bgcolor: 'action.hover',
                            borderRadius: 1,
                            overflow: 'hidden',
                          }}
                        >
                          <Box
                            sx={{
                              width: `${sentiment.neutral * 100}%`,
                              height: '100%',
                              bgcolor: 'grey.500',
                              transition: 'width 0.3s ease',
                            }}
                          />
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ minWidth: 50, textAlign: 'right' }}>
                          {(sentiment.neutral * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    )}
                    {sentiment.negative !== undefined && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ minWidth: 80 }}>
                          Negative:
                        </Typography>
                        <Box
                          sx={{
                            flexGrow: 1,
                            height: 8,
                            bgcolor: 'action.hover',
                            borderRadius: 1,
                            overflow: 'hidden',
                          }}
                        >
                          <Box
                            sx={{
                              width: `${sentiment.negative * 100}%`,
                              height: '100%',
                              bgcolor: 'error.main',
                              transition: 'width 0.3s ease',
                            }}
                          />
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ minWidth: 50, textAlign: 'right' }}>
                          {(sentiment.negative * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    )}
                  </Stack>
                )}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary" fontStyle="italic">
                No sentiment analysis available yet
              </Typography>
            )}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};
