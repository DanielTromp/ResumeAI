import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider
} from '@mui/material';
import axios from 'axios';
import CloudSyncIcon from '@mui/icons-material/CloudSync';

const DatabaseMigration = () => {
  const [migrationStatus, setMigrationStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(null);

  const fetchStatus = async () => {
    try {
      const response = await axios.get('/api/migration/nocodb-to-postgres/status');
      setMigrationStatus(response.data);
      setLastRefresh(new Date());
      setError(null);
    } catch (err) {
      setError('Error fetching migration status: ' + (err.response?.data?.detail || err.message));
    }
  };

  const startMigration = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.post('/api/migration/nocodb-to-postgres');
      setMigrationStatus(response.data.status);
      
      // Set up auto-refresh if migration is running
      if (response.data.status.status === 'running' && !refreshInterval) {
        const interval = setInterval(fetchStatus, 2000);
        setRefreshInterval(interval);
      }
    } catch (err) {
      setError('Error starting migration: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  // Initial fetch and cleanup
  useEffect(() => {
    fetchStatus();
    
    // Cleanup
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, []);

  // Set up or clear interval based on status
  useEffect(() => {
    if (migrationStatus?.status === 'running' && !refreshInterval) {
      const interval = setInterval(fetchStatus, 2000);
      setRefreshInterval(interval);
    } else if (migrationStatus?.status !== 'running' && refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [migrationStatus]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'info';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getProgressPercentage = () => {
    if (!migrationStatus || migrationStatus.total === 0) return 0;
    return Math.round((migrationStatus.migrated / migrationStatus.total) * 100);
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <CloudSyncIcon sx={{ mr: 1 }} />
          <Typography variant="h6">NocoDB to PostgreSQL Migration</Typography>
        </Box>

        <Typography variant="body2" color="text.secondary" gutterBottom>
          Migrate all vacancies from NocoDB to PostgreSQL database
        </Typography>

        <Divider sx={{ my: 2 }} />

        {/* Status display */}
        {migrationStatus && (
          <Box mb={3}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="subtitle1">
                Status: <strong>{migrationStatus.status}</strong>
              </Typography>
              {lastRefresh && (
                <Typography variant="caption" color="text.secondary">
                  Last updated: {lastRefresh.toLocaleTimeString()}
                </Typography>
              )}
            </Box>

            {migrationStatus.status === 'running' && (
              <Box>
                <Box display="flex" justifyContent="space-between" mb={0.5}>
                  <Typography variant="body2">
                    {migrationStatus.migrated} of {migrationStatus.total} records migrated
                  </Typography>
                  <Typography variant="body2">{getProgressPercentage()}%</Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={getProgressPercentage()} 
                  sx={{ mb: 2 }}
                />
              </Box>
            )}

            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell component="th" scope="row">Total Records</TableCell>
                    <TableCell align="right">{migrationStatus.total}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">Successfully Migrated</TableCell>
                    <TableCell align="right">{migrationStatus.migrated}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">Failed</TableCell>
                    <TableCell align="right">{migrationStatus.failed}</TableCell>
                  </TableRow>
                  {migrationStatus.started_at && (
                    <TableRow>
                      <TableCell component="th" scope="row">Started At</TableCell>
                      <TableCell align="right">{new Date(migrationStatus.started_at).toLocaleString()}</TableCell>
                    </TableRow>
                  )}
                  {migrationStatus.completed_at && (
                    <TableRow>
                      <TableCell component="th" scope="row">Completed At</TableCell>
                      <TableCell align="right">{new Date(migrationStatus.completed_at).toLocaleString()}</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            {migrationStatus.last_error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {migrationStatus.last_error}
              </Alert>
            )}

            {migrationStatus.status === 'completed' && migrationStatus.migrated > 0 && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Migration completed successfully! {migrationStatus.migrated} records migrated.
              </Alert>
            )}
          </Box>
        )}

        {/* Error display */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Action buttons */}
        <Box display="flex" justifyContent="space-between">
          <Button 
            variant="contained" 
            color="primary" 
            onClick={startMigration}
            disabled={isLoading || migrationStatus?.status === 'running'}
            startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : null}
          >
            {isLoading ? 'Starting Migration...' : 'Start Migration'}
          </Button>
          <Button 
            variant="outlined" 
            onClick={fetchStatus}
            disabled={isLoading}
          >
            Refresh Status
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default DatabaseMigration;