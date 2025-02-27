import React, { useState, useMemo, createContext, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import NavBar from './components/NavBar';
import Dashboard from './pages/Dashboard';
import VacanciesList from './pages/VacanciesList';
import VacancyDetail from './pages/VacancyDetail';
import ResumesList from './pages/ResumesList';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';

// Create theme context
export const ColorModeContext = createContext({ 
  toggleColorMode: () => {},
  mode: 'dark'
});

function App() {
  // Get the user's preference from localStorage or default to dark mode
  const storedMode = localStorage.getItem('themeMode') || 'dark';
  const [mode, setMode] = useState(storedMode);

  // Theme toggle function
  const colorMode = useMemo(
    () => ({
      toggleColorMode: () => {
        setMode((prevMode) => {
          const newMode = prevMode === 'light' ? 'dark' : 'light';
          localStorage.setItem('themeMode', newMode);
          return newMode;
        });
      },
      mode
    }),
    [mode]
  );

  // Create theme based on current mode
  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: {
            main: '#1976d2',
          },
          secondary: {
            main: mode === 'dark' ? '#f48fb1' : '#dc004e',
          },
          background: {
            default: mode === 'dark' ? '#121212' : '#f5f5f5',
            paper: mode === 'dark' ? '#1e1e1e' : '#ffffff',
          },
        },
        typography: {
          fontFamily: [
            'Roboto',
            'Arial',
            'sans-serif',
          ].join(','),
        },
        components: {
          MuiAppBar: {
            styleOverrides: {
              root: {
                backgroundColor: mode === 'dark' ? '#272727' : '#1976d2',
              },
            },
          },
        },
      }),
    [mode]
  );

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <NavBar />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/vacancies" element={<VacanciesList />} />
            <Route path="/vacancies/:id" element={<VacancyDetail />} />
            <Route path="/resumes" element={<ResumesList />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Router>
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

export default App;