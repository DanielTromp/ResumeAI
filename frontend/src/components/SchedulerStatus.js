import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  CircularProgress,
  Divider,
  Grid,
  Alert
} from '@mui/material';
import { PlayArrow, Stop, Refresh } from '@mui/icons-material';
import axios from 'axios';

const SchedulerStatus = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/process/scheduler/status');
      setStatus(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching scheduler status:', err);
      setError('Failed to fetch scheduler status');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    
    // Set up periodic refresh
    const interval = setInterval(() => {
      fetchStatus();
    }, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (action) => {
    try {
      setActionLoading(true);
      setActionSuccess(null);
      
      const response = await axios.post('/api/process/scheduler/control', { action });
      
      if (response.data.status === 'success') {
        setActionSuccess(response.data.message);
        // Refresh status
        fetchStatus();
      } else {
        setError(response.data.message);
      }
      
      setActionLoading(false);
    } catch (err) {
      console.error(`Error ${action} scheduler:`, err);
      setError(`Failed to ${action} scheduler`);
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Card variant="outlined" sx={{ mt: 3 }}>
      <CardContent>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h6" component="div">
              Scheduler Status
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Automatic process runs
            </Typography>
            
            <Divider sx={{ my: 1 }} />
            
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Status:</strong> {status?.running ? 'Running' : 'Stopped'}
              </Typography>
              <Typography variant="body2">
                <strong>Enabled:</strong> {status?.enabled ? 'Yes' : 'No'}
              </Typography>
              <Typography variant="body2">
                <strong>Schedule:</strong> {status?.active_days?.join(', ')}, {status?.active_hours}, every {status?.interval_minutes} min
              </Typography>
              <Typography variant="body2">
                <strong>Next Run:</strong> {status?.next_run || 'Not scheduled'}
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={<PlayArrow />}
                disabled={status?.running || actionLoading || !status?.enabled}
                onClick={() => handleAction('start')}
                fullWidth
              >
                Start Scheduler
              </Button>
              
              <Button
                variant="outlined"
                color="secondary"
                startIcon={<Stop />}
                disabled={!status?.running || actionLoading}
                onClick={() => handleAction('stop')}
                fullWidth
              >
                Stop Scheduler
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                disabled={actionLoading}
                onClick={() => handleAction('update')}
                fullWidth
              >
                Refresh Configuration
              </Button>
              
              {actionSuccess && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  {actionSuccess}
                </Alert>
              )}
              
              {!status?.enabled && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Scheduler is disabled. Enable it in Settings to automatically run the process.
                </Alert>
              )}
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SchedulerStatus;