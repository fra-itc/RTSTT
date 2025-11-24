/**
 * MainView - Main application view
 * Wires all components together with useAudioPipeline hook
 * Features responsive grid layout with transcriptions, insights, and suggestions
 */

import React from 'react';
import { Box, Grid } from '@mui/material';
import { AppShell } from '../components/layout';
import { AudioControlPanel } from '../components/AudioControlPanel';
import { TranscriptionList } from '../components/TranscriptionList';
import { InsightsPanel } from '../components/InsightsPanel';
import { SuggestionsPanel } from '../components/SuggestionsPanel';
import { useAudioPipeline } from '../hooks/useAudioPipeline';

export const MainView: React.FC = () => {
  const audio = useAudioPipeline();

  /**
   * Handle export transcriptions
   */
  const handleExport = (format: 'txt' | 'json' | 'srt', data: any[]) => {
    let content = '';
    let filename = `transcriptions-${new Date().toISOString().replace(/:/g, '-')}`;

    switch (format) {
      case 'txt':
        content = data.map((t) => t.text).join('\n\n');
        filename += '.txt';
        break;
      case 'json':
        content = JSON.stringify(data, null, 2);
        filename += '.json';
        break;
      case 'srt':
        // SRT format (SubRip)
        content = data
          .map((t, i) => {
            const startTime = new Date(t.timestamp);
            const endTime = new Date(startTime.getTime() + 2000); // 2 second duration
            const formatSrtTime = (d: Date) => {
              const pad = (n: number) => n.toString().padStart(2, '0');
              return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())},${d.getMilliseconds().toString().padStart(3, '0')}`;
            };
            return `${i + 1}\n${formatSrtTime(startTime)} --> ${formatSrtTime(endTime)}\n${t.text}\n`;
          })
          .join('\n');
        filename += '.srt';
        break;
    }

    // Download file
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <AppShell
      title="ORCHIDEA RTSTT"
      sidebar={
        <AudioControlPanel
          devices={audio.devices}
          selectedDevice={audio.selectedDevice}
          volume={audio.volume}
          preampGain={audio.preampGain}
          isRecording={audio.isRecording}
          audioLevel={audio.audioLevel}
          waveformData={audio.waveformData}
          connectionStatus={audio.connectionStatus}
          wsError={audio.wsError}
          language={audio.language}
          model={audio.model}
          sampleRate={audio.sampleRate}
          channels={audio.channels}
          onDeviceChange={audio.setSelectedDevice}
          onVolumeChange={audio.handleVolumeChange}
          onPreampChange={audio.handlePreampChange}
          onRecordToggle={audio.handleRecordToggle}
          onLanguageChange={audio.handleLanguageChange}
          onModelChange={audio.handleModelChange}
          onRefreshDevices={audio.loadDevices}
        />
      }
    >
      <Box
        sx={{
          height: '100%',
          overflow: 'hidden',
          p: 2,
        }}
      >
        <Grid
          container
          spacing={2}
          sx={{
            height: '100%',
            overflow: 'hidden',
          }}
        >
          {/* Left Column - Transcriptions */}
          <Grid
            item
            xs={12}
            lg={6}
            sx={{
              height: { xs: 'auto', lg: '100%' },
              minHeight: { xs: 400, lg: 0 },
            }}
          >
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <TranscriptionList
                transcriptions={audio.transcriptions}
                onExport={handleExport}
              />
            </Box>
          </Grid>

          {/* Right Column - Insights and Suggestions */}
          <Grid
            item
            xs={12}
            lg={6}
            sx={{
              height: { xs: 'auto', lg: '100%' },
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
            }}
          >
            {/* Top Right - Insights Panel */}
            <Box sx={{ flex: 1, minHeight: { xs: 300, lg: 0 } }}>
              <InsightsPanel
                keywords={audio.insights.keywords}
                entities={audio.insights.entities}
                sentiment={audio.insights.sentiment}
                isLoading={audio.isRecording && audio.transcriptions.length > 0 && !audio.insights.keywords.length}
                isEmpty={!audio.isRecording && audio.transcriptions.length === 0}
              />
            </Box>

            {/* Bottom Right - Suggestions Panel */}
            <Box sx={{ flex: 1, minHeight: { xs: 300, lg: 0 } }}>
              <SuggestionsPanel
                summary={audio.summary}
                suggestions={audio.suggestions}
                isLoading={audio.isRecording && audio.transcriptions.length > 0 && !audio.summary}
                isEmpty={!audio.isRecording && audio.transcriptions.length === 0}
              />
            </Box>
          </Grid>
        </Grid>
      </Box>
    </AppShell>
  );
};
