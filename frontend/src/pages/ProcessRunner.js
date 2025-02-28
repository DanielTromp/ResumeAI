import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Divider,
  TextField,
  IconButton,
  Snackbar,
  LinearProgress
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import RefreshIcon from '@mui/icons-material/Refresh';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import axios from 'axios';

const ProcessRunner = () => {
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [processId, setProcessId] = useState('');
  const [status, setStatus] = useState('idle');
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [pollingInterval, setPollingInterval] = useState(null);
  const logEndRef = useRef(null);

  // Auto-scroll to the bottom of logs
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // When component unmounts, clear the polling interval
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // Start polling for status when running
  useEffect(() => {
    if (running) {
      const interval = setInterval(fetchProcessStatus, 2000);
      setPollingInterval(interval);
    } else if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  }, [running]);

  const fetchProcessStatus = async () => {
    try {
      const response = await axios.get('/api/process/status');
      const { status, process_id, logs } = response.data;
      
      setStatus(status);
      setProcessId(process_id);
      setLogs(logs);
      
      // If process is not running anymore, stop polling
      if (status !== 'running') {
        setRunning(false);
      }
    } catch (err) {
      console.error('Error fetching process status:', err);
      setError('Failed to fetch process status. Please try again later.');
      setRunning(false);
    }
  };

  const startProcess = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/process/start');
      
      if (response.data.status === 'started' || response.data.status === 'running') {
        setRunning(true);
        setSuccess(true);
        await fetchProcessStatus(); // Get initial status
      } else if (response.data.status === 'error') {
        setError(response.data.message);
      }
    } catch (err) {
      console.error('Error starting process:', err);
      setError('Failed to start process. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const copyLogsToClipboard = () => {
    const logsText = logs.join('\n');
    navigator.clipboard.writeText(logsText)
      .then(() => {
        setSuccess(true);
      })
      .catch((err) => {
        console.error('Could not copy logs:', err);
        setError('Failed to copy logs to clipboard');
      });
  };

  const handleCloseSnackbar = () => {
    setSuccess(false);
    setError(null);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Process Runner
      </Typography>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Combined Vacancy & Resume Matching Process
          </Typography>
          <Box>
            <Button
              variant="contained"
              color="primary"
              startIcon={<PlayArrowIcon />}
              onClick={startProcess}
              disabled={loading || running}
              sx={{ mr: 1 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Start Process'}
            </Button>
            <IconButton 
              color="primary" 
              onClick={fetchProcessStatus} 
              disabled={loading}
              aria-label="refresh status"
            >
              <RefreshIcon />
            </IconButton>
          </Box>
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Status: <strong>{status.charAt(0).toUpperCase() + status.slice(1)}</strong>
            {processId && ` (Process ID: ${processId})`}
          </Typography>
          
          {running && (
            <Box sx={{ width: '100%', mt: 1, mb: 2 }}>
              <LinearProgress />
            </Box>
          )}
        </Box>
        
        <Typography variant="subtitle1" gutterBottom>
          Log Output
          <IconButton 
            size="small" 
            onClick={copyLogsToClipboard}
            disabled={logs.length === 0}
            aria-label="copy logs to clipboard"
            sx={{ ml: 1 }}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Typography>
        
        <Box
          sx={{
            mt: 2,
            p: 2,
            height: '400px',
            bgcolor: 'background.paper',
            borderRadius: 1,
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            overflowY: 'auto',
            border: '1px solid',
            borderColor: 'divider',
          }}
        >
          {logs.length > 0 ? (
            logs.map((log, index) => (
              <Box key={index} sx={{ lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                {log}
              </Box>
            ))
          ) : (
            <Typography color="text.secondary" sx={{ fontStyle: 'italic' }}>
              No logs available. Start the process to see output here.
            </Typography>
          )}
          <div ref={logEndRef} />
        </Box>
      </Paper>
      
      {/* Notifications */}
      <Snackbar
        open={success}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success" sx={{ width: '100%' }}>
          {running ? 'Process started successfully!' : 'Logs copied to clipboard!'}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ProcessRunner;