import React, { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { 
  Container, 
  Grid, 
  Paper, 
  Typography, 
  Box, 
  Button,
  Card,
  CardContent,
  CardActions,
  Divider,
  CircularProgress,
  Alert
} from '@mui/material';
import WorkIcon from '@mui/icons-material/Work';
import PersonIcon from '@mui/icons-material/Person';
import SettingsIcon from '@mui/icons-material/Settings';
import axios from 'axios';

// For debugging network issues and direct API access
const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
console.log('Backend URL:', backendUrl);

// We'll use the backend URL directly instead of relying on the proxy
// This ensures we can access the backend from inside the Docker container
const baseURL = backendUrl;

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalVacancies: 0,
    newVacancies: 0,
    openVacancies: 0,
    totalResumes: 0,
    loading: true,
    error: null
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        console.log('Fetching dashboard data...');
        
        // Create axios instance with consistent base URL
        const api = axios.create({
          baseURL: baseURL,
          timeout: 5000,
        });
        
        // Log request info before making requests
        console.log('Sending request to:', `${baseURL}/api/vacancies`);
        
        // Fetch vacancies stats
        const vacanciesResponse = await api.get('/api/vacancies');
        console.log('Vacancies response:', vacanciesResponse.data);
        
        // Get total vacancies from the total_all field (across all statuses)
        const totalAllVacancies = vacanciesResponse.data.total_all || vacanciesResponse.data.total;
        
        // Fetch specifically Open vacancies to get their count
        const openVacanciesResponse = await api.get('/api/vacancies?status=Open&limit=1');
        const openVacanciesCount = openVacanciesResponse.data.total;
        
        // Fetch specifically New vacancies to get their count
        const newVacanciesResponse = await api.get('/api/vacancies?status=Nieuw&limit=1');
        const newVacanciesCount = newVacanciesResponse.data.total;
        
        // Fetch resumes stats
        const resumesResponse = await api.get('/api/resumes');
        
        setStats({
          totalVacancies: totalAllVacancies,
          newVacancies: newVacanciesCount,
          openVacancies: openVacanciesCount,
          totalResumes: resumesResponse.data.total,
          loading: false,
          error: null
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setStats({
          ...stats,
          loading: false,
          error: 'Failed to load dashboard data. Please try again later. Error: ' + (error.message || 'Unknown error')
        });
      }
    };

    fetchStats();
  }, []);

  // Stat cards with icons and counts
  const StatCard = ({ title, count, icon, color, link }) => (
    <Card 
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderTop: `4px solid ${color}`
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="div" color="text.secondary">
            {title}
          </Typography>
          <Box sx={{ 
            backgroundColor: `${color}20`,
            borderRadius: '50%',
            p: 1,
            display: 'flex'
          }}>
            {icon}
          </Box>
        </Box>
        <Typography variant="h3" component="div">
          {stats.loading ? <CircularProgress size={30} /> : count}
        </Typography>
      </CardContent>
      <Divider />
      <CardActions>
        <Button 
          component={RouterLink} 
          to={link} 
          size="small" 
          sx={{ color }}
        >
          View details
        </Button>
      </CardActions>
    </Card>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      {stats.error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {stats.error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Total Vacancies */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Total Vacancies" 
            count={stats.totalVacancies} 
            icon={<WorkIcon sx={{ color: '#1976d2' }} />} 
            color="#1976d2"
            link="/vacancies"
          />
        </Grid>
        
        {/* New Vacancies */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="New Vacancies" 
            count={stats.newVacancies} 
            icon={<WorkIcon sx={{ color: '#2e7d32' }} />} 
            color="#2e7d32"
            link="/vacancies?status=Nieuw"
          />
        </Grid>
        
        {/* Open Vacancies */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Open Vacancies" 
            count={stats.openVacancies} 
            icon={<WorkIcon sx={{ color: '#ed6c02' }} />} 
            color="#ed6c02"
            link="/vacancies?status=Open"
          />
        </Grid>
        
        {/* Total Resumes */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Total Resumes" 
            count={stats.totalResumes} 
            icon={<PersonIcon sx={{ color: '#9c27b0' }} />} 
            color="#9c27b0"
            link="/resumes"
          />
        </Grid>
        
        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              <Grid item>
                <Button 
                  variant="contained" 
                  startIcon={<WorkIcon />}
                  component={RouterLink}
                  to="/vacancies"
                >
                  View All Vacancies
                </Button>
              </Grid>
              <Grid item>
                <Button 
                  variant="contained" 
                  color="secondary" 
                  startIcon={<PersonIcon />}
                  component={RouterLink}
                  to="/resumes"
                >
                  View All Resumes
                </Button>
              </Grid>
              <Grid item>
                <Button 
                  variant="outlined" 
                  startIcon={<SettingsIcon />}
                  component={RouterLink}
                  to="/settings"
                >
                  Settings
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;