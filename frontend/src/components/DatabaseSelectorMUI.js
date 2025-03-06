import React, { useState, useEffect } from 'react';
import {
  FormControl,
  FormLabel,
  Select,
  MenuItem,
  Button,
  Alert,
  Typography,
  Chip,
  CircularProgress,
  Tooltip,
  Box,
  Divider,
  Paper,
  Grid,
} from '@mui/material';
import axios from 'axios';
import StorageIcon from '@mui/icons-material/Storage';
import CloudIcon from '@mui/icons-material/Cloud';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';

const DatabaseSelectorMUI = () => {
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [status, setStatus] = useState({});
  const [error, setError] = useState(null);
  const [selectedProvider, setSelectedProvider] = useState('');

  const fetchStatus = async () => {
    setLoading(true);
    try {
      console.log('Fetching database status...');
      
      // Set a reasonable timeout for the request
      const response = await axios.get('/api/settings/database/status', {
        timeout: 5000 // 5 seconds timeout
      });
      
      console.log('Database status response:', response.data);
      
      // If we got an empty response or no data, set a default status
      if (!response.data || Object.keys(response.data).length === 0) {
        console.warn('Received empty database status response');
        setStatus({
          postgres: true,
          supabase: false,
          current_provider: 'postgres',
          resume_counts: { postgres: 0, supabase: 0 }
        });
        setSelectedProvider('postgres');
      } else {
        setStatus(response.data);
        setSelectedProvider(response.data.current_provider || 'postgres');
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching database status:', err);
      
      // Set default values if we can't fetch the status
      setStatus({
        postgres: true,
        supabase: false,
        current_provider: 'postgres',
        resume_counts: { postgres: 0, supabase: 0 }
      });
      setSelectedProvider('postgres');
      
      setError('Error fetching database status: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleSwitch = async () => {
    if (selectedProvider === status.current_provider) return;
    
    setSwitching(true);
    try {
      console.log(`Switching database provider to: ${selectedProvider}`);
      
      await axios.post('/api/settings/database/switch', selectedProvider, {
        headers: {
          'Content-Type': 'text/plain'
        }
      });
      
      console.log(`Switch successful, refreshing status...`);
      
      // Wait a moment for the backend to update
      setTimeout(async () => {
        try {
          await fetchStatus();
          setError(null);
        } catch (refreshErr) {
          console.error('Error refreshing status:', refreshErr);
          setError('Provider switched but error refreshing status. Please reload the page.');
        } finally {
          setSwitching(false);
        }
      }, 1000);
      
    } catch (err) {
      console.error('Error switching provider:', err);
      setError('Error switching database provider: ' + (err.response?.data?.detail || err.message));
      setSwitching(false);
    }
  };

  const getProviderChip = (provider) => {
    const isConnected = status[provider] === true;
    const isCurrent = status.current_provider === provider;
    
    let color = 'default';
    let label = 'Unavailable';
    
    if (isConnected) {
      color = isCurrent ? 'success' : 'primary';
      label = isCurrent ? 'Active' : 'Available';
    }
    
    return (
      <Chip 
        color={color}
        variant={isCurrent ? 'filled' : 'outlined'}
        label={label}
        size="small"
      />
    );
  };

  const getResumeCount = (provider) => {
    if (!status.resume_counts || status.resume_counts[provider] === undefined) return '?';
    return status.resume_counts[provider];
  };

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Database Provider
      </Typography>
      <Divider sx={{ mb: 2 }} />
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <FormControl fullWidth>
              <FormLabel>Select Database Provider</FormLabel>
              <Select 
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                disabled={switching}
                sx={{ mt: 1 }}
              >
                <MenuItem value="postgres">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <StorageIcon sx={{ mr: 1 }} />
                    PostgreSQL (Local)
                  </Box>
                </MenuItem>
                <MenuItem 
                  value="supabase"
                  disabled={!status.supabase}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CloudIcon sx={{ mr: 1 }} />
                    Supabase (Cloud)
                    {!status.supabase && (
                      <span style={{ marginLeft: '8px', fontSize: '0.8rem', color: 'gray' }}>
                        (Not Available)
                      </span>
                    )}
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }} />
            <Typography variant="subtitle2" gutterBottom>
              Provider Status
            </Typography>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <StorageIcon sx={{ mr: 1, fontSize: 20 }} />
                <Typography>PostgreSQL:</Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {getProviderChip('postgres')}
                <Tooltip title="Number of resumes">
                  <Chip 
                    label={`${getResumeCount('postgres')} resumes`}
                    variant="outlined"
                    size="small"
                    color="secondary"
                  />
                </Tooltip>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CloudIcon sx={{ mr: 1, fontSize: 20 }} />
                <Typography>Supabase:</Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {getProviderChip('supabase')}
                <Tooltip title="Number of resumes">
                  <Chip 
                    label={`${getResumeCount('supabase')} resumes`}
                    variant="outlined"
                    size="small"
                    color="secondary"
                  />
                </Tooltip>
              </Box>
            </Box>
          </Grid>
          
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }} />
            <Button
              variant="contained"
              color="primary"
              onClick={handleSwitch}
              disabled={switching || selectedProvider === status.current_provider}
              startIcon={<SwapHorizIcon />}
              sx={{ mt: 1 }}
            >
              {switching ? 'Switching...' : 'Switch Provider'}
            </Button>
          </Grid>
        </Grid>
      )}
    </Paper>
  );
};

export default DatabaseSelectorMUI;