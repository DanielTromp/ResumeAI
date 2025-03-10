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
import { getVacancyStats, getResumes } from '../utils/api';

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
        console.log('Current API configuration:', {
          baseURL: window.location.origin,
          apiPath: '/api/statistics/vacancies',
          fullUrl: `${window.location.origin}/api/statistics/vacancies`
        });
        
        // Fetch vacancy statistics - this is more efficient than multiple API calls
        console.log('Making vacancy stats request...');
        let statsResponse;
        try {
          statsResponse = await getVacancyStats();
          console.log('Vacancy stats request successful');
        } catch (vacancyError) {
          console.error('Vacancy stats request failed:', vacancyError);
          throw new Error(`Vacancy stats request failed: ${vacancyError.message}`);
        }
        
        console.log('Statistics response received:', statsResponse.data);
        
        // Get the statistics from the response
        const vacancyStats = statsResponse.data.statistics || {};
        
        // Get total vacancies from statistics
        const totalAllVacancies = vacancyStats.total || 0;
        
        // Get status-specific counts
        const openVacanciesCount = vacancyStats.Open || 0;
        const newVacanciesCount = vacancyStats.Nieuw || 0;
        
        // Fetch resumes stats
        console.log('Making resumes request...');
        let resumesResponse;
        try {
          resumesResponse = await getResumes({ limit: 1 });
          console.log('Resumes request successful');
        } catch (resumesError) {
          console.error('Resumes request failed:', resumesError);
          throw new Error(`Resumes request failed: ${resumesError.message}`);
        }
        
        console.log('Setting dashboard stats with data:', {
          totalVacancies: totalAllVacancies,
          newVacancies: newVacanciesCount,
          openVacancies: openVacanciesCount,
          totalResumes: resumesResponse.data.total
        });
        
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
        
        // Create a more detailed error message
        let errorMessage = 'Failed to load dashboard data. ';
        
        if (error.message) {
          errorMessage += `Error: ${error.message}`;
        }
        
        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          errorMessage += ` (Status: ${error.response.status})`;
          console.error('Server response:', error.response.data);
        } else if (error.request) {
          // The request was made but no response was received
          errorMessage += ' (Network Error: No response received from server)';
          console.error('Network error - request made but no response');
          
          // Add connection diagnostic info
          console.error('Browser online status:', navigator.onLine ? 'Online' : 'Offline');
          console.error('Current location:', window.location.href);
        }
        
        setStats({
          ...stats,
          loading: false,
          error: errorMessage
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