import React, { useContext } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Box,
  Container,
  IconButton,
  Tooltip,
  useTheme
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import WorkIcon from '@mui/icons-material/Work';
import PersonIcon from '@mui/icons-material/Person';
import SettingsIcon from '@mui/icons-material/Settings';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import { ColorModeContext } from '../App';

const NavBar = () => {
  const location = useLocation();
  const theme = useTheme();
  const colorMode = useContext(ColorModeContext);

  // Navigation items
  const navItems = [
    { label: 'Dashboard', path: '/', icon: <DashboardIcon fontSize="small" /> },
    { label: 'Vacancies', path: '/vacancies', icon: <WorkIcon fontSize="small" /> },
    { label: 'Resumes', path: '/resumes', icon: <PersonIcon fontSize="small" /> },
    { label: 'Settings', path: '/settings', icon: <SettingsIcon fontSize="small" /> },
  ];

  return (
    <AppBar position="sticky">
      <Container maxWidth={false}>
        <Toolbar>
          <Typography 
            variant="h6" 
            component={RouterLink} 
            to="/" 
            sx={{ 
              flexGrow: 1,
              textDecoration: 'none',
              color: 'inherit',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            ResumeAI
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {/* Theme toggle button */}
            <Tooltip title={theme.palette.mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
              <IconButton
                onClick={colorMode.toggleColorMode}
                color="inherit"
                sx={{ ml: 1 }}
                aria-label="toggle theme"
              >
                {theme.palette.mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
              </IconButton>
            </Tooltip>
            
            {/* Navigation buttons */}
            {navItems.map((item) => (
              <Button
                key={item.path}
                component={RouterLink}
                to={item.path}
                color="inherit"
                sx={{ 
                  mx: 1,
                  opacity: location.pathname === item.path ? 1 : 0.7,
                  fontWeight: location.pathname === item.path ? 'bold' : 'normal',
                  '&:hover': {
                    opacity: 1,
                  },
                }}
                startIcon={item.icon}
              >
                {item.label}
              </Button>
            ))}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default NavBar;