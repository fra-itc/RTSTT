/**
 * App - Main Application Entry Point
 * Modern UI with integrated audio pipeline
 */

import React from 'react';
import { ThemeProvider } from './theme/ThemeProvider';
import { MainView } from './views/MainView';

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <MainView />
    </ThemeProvider>
  );
};

export default App;
