/**
 * AppShell - Main Application Layout
 * Responsive shell with header, sidebar, and main content area
 */

import React, { useState, ReactNode } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  useTheme,
  useMediaQuery,
  Container,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useThemeMode } from '../../theme/ThemeProvider';

interface AppShellProps {
  children: ReactNode;
  sidebar?: ReactNode;
  title?: string;
}

const DRAWER_WIDTH = 300;
const APP_BAR_HEIGHT = 64;

export const AppShell: React.FC<AppShellProps> = ({
  children,
  sidebar,
  title = 'ORCHIDEA RTSTT',
}) => {
  const theme = useTheme();
  const { mode, toggleTheme } = useThemeMode();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawerContent = sidebar ? (
    <Box
      sx={{
        width: DRAWER_WIDTH,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
      }}
    >
      {sidebar}
    </Box>
  ) : null;

  return (
    <Box sx={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          background: mode === 'dark'
            ? 'linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%)'
            : 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
          boxShadow: theme.shadows[4],
        }}
      >
        <Toolbar>
          {/* Mobile Menu Button */}
          {sidebar && isMobile && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}

          {/* App Title */}
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{
              flexGrow: 1,
              fontWeight: 700,
              letterSpacing: '0.5px',
            }}
          >
            {title}
          </Typography>

          {/* Theme Toggle */}
          <Tooltip title={`Switch to ${mode === 'light' ? 'dark' : 'light'} mode`}>
            <IconButton
              color="inherit"
              onClick={toggleTheme}
              sx={{
                mr: 1,
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              {mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
            </IconButton>
          </Tooltip>

          {/* Settings Button */}
          <Tooltip title="Settings">
            <IconButton
              color="inherit"
              sx={{
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Sidebar Drawer */}
      {sidebar && (
        <>
          {/* Mobile Drawer */}
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{
              keepMounted: true, // Better mobile performance
            }}
            sx={{
              display: { xs: 'block', md: 'none' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: DRAWER_WIDTH,
                marginTop: `${APP_BAR_HEIGHT}px`,
                height: `calc(100% - ${APP_BAR_HEIGHT}px)`,
                borderRight: `1px solid ${theme.palette.divider}`,
              },
            }}
          >
            {drawerContent}
          </Drawer>

          {/* Desktop Drawer */}
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: 'none', md: 'block' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: DRAWER_WIDTH,
                marginTop: `${APP_BAR_HEIGHT}px`,
                height: `calc(100% - ${APP_BAR_HEIGHT}px)`,
                borderRight: `1px solid ${theme.palette.divider}`,
                backgroundColor: theme.palette.background.default,
              },
            }}
            open
          >
            {drawerContent}
          </Drawer>
        </>
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          overflow: 'hidden',
          marginTop: `${APP_BAR_HEIGHT}px`,
          marginLeft: sidebar && !isMobile ? `${DRAWER_WIDTH}px` : 0,
          transition: theme.transitions.create(['margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Container
          maxWidth={false}
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'auto',
            padding: { xs: 2, sm: 3 },
            backgroundColor: theme.palette.background.default,
          }}
        >
          {children}
        </Container>
      </Box>
    </Box>
  );
};
