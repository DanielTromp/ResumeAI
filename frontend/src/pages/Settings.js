import React, { useState, useEffect, useContext } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  TextField,
  Button,
  Alert,
  Snackbar,
  CircularProgress,
  Divider,
  FormControlLabel,
  Switch,
  useTheme,
  IconButton,
  Tooltip,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import RefreshIcon from '@mui/icons-material/Refresh';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import axios from 'axios';
import { ColorModeContext } from '../App';

const Settings = () => {
  const theme = useTheme();
  const colorMode = useContext(ColorModeContext);

  const [settings, setSettings] = useState({
    openai_api_key: '',
    pg_host: '',
    pg_port: '',
    pg_user: '',
    pg_password: '',
    pg_database: '',
    spinweb_user: '',
    spinweb_pass: '',
    excluded_clients: '',
    ai_model: '',
    match_threshold: '',
    match_count: '',
    resume_prompt_template: '',
    // Scheduler settings
    scheduler_enabled: false,
    scheduler_start_hour: '6',
    scheduler_end_hour: '20',
    scheduler_interval_minutes: '60',
    scheduler_days: 'mon,tue,wed,thu,fri',
    // Email settings
    email_enabled: false,
    email_provider: 'smtp',
    email_smtp_host: '',
    email_smtp_port: '587',
    email_smtp_use_tls: true,
    email_username: '',
    email_password: '',
    email_from_email: '',
    email_from_name: '',
    email_recipients: '',
    email_digest_subject: '',
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [success, setSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Function to fetch settings - extracted so it can be called manually
  const fetchSettings = async () => {
    try {
      setLoading(true);
      // Add timestamp parameter to prevent caching
      const timestamp = new Date().getTime();
      const response = await axios.get(`/api/settings?_=${timestamp}`, {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      console.log('Settings fetched:', response.data);
      setSettings(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching settings:', err);
      setError('Failed to load settings. Please try again later.');
      setLoading(false);
    }
  };

  // Initial fetch on component mount
  useEffect(() => {
    fetchSettings();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSettings({
      ...settings,
      [name]: value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await axios.put('/api/settings', settings, {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      setSuccess(true);
      setSuccessMessage("Settings updated successfully!");
      // Fetch the latest settings after updating
      await fetchSettings();
    } catch (err) {
      console.error('Error updating settings:', err);
      setError(true);
      setErrorMessage(err.response?.data?.detail || 'Failed to update settings. Please try again later.');
      setLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSuccess(false);
    setError(null);
    setSuccessMessage('');
    setErrorMessage('');
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" component="h1">
          Settings
        </Typography>
        <Tooltip title="Refresh settings">
          <IconButton 
            onClick={fetchSettings} 
            color="primary" 
            disabled={loading}
            aria-label="refresh settings"
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {!loading && (
        <Paper sx={{ p: 3 }}>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              {/* UI Settings */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  UI Settings
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>
              
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
                  <Brightness4Icon sx={{ mr: 1, color: theme.palette.mode === 'dark' ? 'inherit' : 'text.secondary' }} />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={theme.palette.mode === 'dark'}
                        onChange={colorMode.toggleColorMode}
                        name="darkMode"
                        color="primary"
                      />
                    }
                    label="Dark Mode"
                  />
                  <Brightness7Icon sx={{ ml: 1, color: theme.palette.mode === 'light' ? 'inherit' : 'text.secondary' }} />
                </Box>
              </Grid>
              
              {/* API Configuration */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  API Configuration
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="OpenAI API Key"
                  name="openai_api_key"
                  value={settings.openai_api_key}
                  onChange={handleInputChange}
                  type="password"
                  required
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="AI Model"
                  name="ai_model"
                  value={settings.ai_model}
                  onChange={handleInputChange}
                  helperText="e.g., gpt-4o-mini"
                />
              </Grid>

              {/* PostgreSQL Configuration */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  PostgreSQL Configuration
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="PostgreSQL Host"
                  name="pg_host"
                  value={settings.pg_host}
                  onChange={handleInputChange}
                  helperText="Hostname or IP address (e.g., localhost, db)"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="PostgreSQL Port"
                  name="pg_port"
                  value={settings.pg_port}
                  onChange={handleInputChange}
                  helperText="Default: 5432"
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="PostgreSQL User"
                  name="pg_user"
                  value={settings.pg_user}
                  onChange={handleInputChange}
                  helperText="Database username"
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="PostgreSQL Password"
                  name="pg_password"
                  value={settings.pg_password}
                  onChange={handleInputChange}
                  type="password"
                  helperText="Database password"
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="PostgreSQL Database"
                  name="pg_database"
                  value={settings.pg_database}
                  onChange={handleInputChange}
                  helperText="Database name (e.g., resumeai)"
                />
              </Grid>


              {/* Spinweb Configuration */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Spinweb Configuration
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Spinweb Username"
                  name="spinweb_user"
                  value={settings.spinweb_user}
                  onChange={handleInputChange}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Spinweb Password"
                  name="spinweb_pass"
                  value={settings.spinweb_pass}
                  onChange={handleInputChange}
                  type="password"
                />
              </Grid>

              {/* Matching Configuration */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Matching Configuration
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Match Threshold"
                  name="match_threshold"
                  value={settings.match_threshold}
                  onChange={handleInputChange}
                  type="number"
                  inputProps={{ min: 0, max: 1, step: 0.01 }}
                  helperText="Range: 0-1 (e.g., 0.75)"
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Match Count"
                  name="match_count"
                  value={settings.match_count}
                  onChange={handleInputChange}
                  type="number"
                  inputProps={{ min: 1, step: 1 }}
                  helperText="Number of matches to return"
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Excluded Clients"
                  name="excluded_clients"
                  value={settings.excluded_clients}
                  onChange={handleInputChange}
                  helperText="Comma-separated list of clients to exclude"
                />
              </Grid>
              
              {/* Prompt Template */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Resume Matching Prompt
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Resume Prompt Template"
                  name="resume_prompt_template"
                  value={settings.resume_prompt_template}
                  onChange={handleInputChange}
                  multiline
                  rows={20}
                  variant="outlined"
                  helperText="The prompt template used for resume matching. Use {name}, {vacancy_text}, and {cv_text} as placeholders."
                />
              </Grid>

              {/* Scheduler Configuration - Removed */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Cron Configuration
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>
              
              <Grid item xs={12}>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body1" fontWeight="bold">Scheduler has been removed</Typography>
                  <Typography variant="body2">
                    The process is now configured to run via system cron. Contact your administrator for schedule changes.
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Sample cron command: <code>0 9,13,17 * * 1-5 docker exec resumeai-backend-1 python -m app.combined_process</code>
                  </Typography>
                </Alert>
              </Grid>

              {/* Email Settings */}
              <Grid item xs={12} sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Email Notifications
                </Typography>
                <Divider />
              </Grid>

              {/* Email Toggle */}
              <Grid item xs={12} sm={6} md={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.email_enabled}
                      onChange={(e) => {
                        setSettings({
                          ...settings,
                          email_enabled: e.target.checked,
                        });
                      }}
                      name="email_enabled"
                      color="primary"
                    />
                  }
                  label="Enable Email Notifications"
                />
              </Grid>

              {/* Email Provider */}
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  select
                  fullWidth
                  label="Email Provider"
                  name="email_provider"
                  value={settings.email_provider}
                  onChange={handleInputChange}
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="smtp">SMTP</option>
                  <option value="gmail">Gmail</option>
                  <option value="mailersend">MailerSend</option>
                </TextField>
              </Grid>

              {/* Test Email Button */}
              <Grid item xs={12} sm={6} md={4}>
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={() => {
                    // First show a prompt for the test email recipient
                    const recipient = prompt("Enter email address for test:", "");
                    if (recipient) {
                      axios.post('/api/settings/email/test', { recipient })
                        .then(response => {
                          setSuccess(true);
                          setSuccessMessage("Test email sent successfully!");
                        })
                        .catch(error => {
                          setError(true);
                          setErrorMessage("Failed to send test email: " + (error.response?.data?.detail || error.message));
                        });
                    }
                  }}
                  disabled={!settings.email_enabled}
                  sx={{ mt: 1 }}
                >
                  Send Test Email
                </Button>
              </Grid>

              {/* SMTP Settings - shown when provider is 'smtp' or 'gmail' */}
              {(settings.email_provider === 'smtp' || settings.email_provider === 'gmail') && (
                <>
                  {/* SMTP Host */}
                  <Grid item xs={12} sm={6} md={4}>
                    <TextField
                      fullWidth
                      label="SMTP Host"
                      name="email_smtp_host"
                      value={settings.email_smtp_host}
                      onChange={handleInputChange}
                      disabled={settings.email_provider === 'gmail'}
                      helperText={settings.email_provider === 'gmail' ? "Using smtp.gmail.com" : ""}
                    />
                  </Grid>

                  {/* SMTP Port */}
                  <Grid item xs={12} sm={6} md={4}>
                    <TextField
                      fullWidth
                      label="SMTP Port"
                      name="email_smtp_port"
                      value={settings.email_smtp_port}
                      onChange={handleInputChange}
                      type="number"
                      disabled={settings.email_provider === 'gmail'}
                      helperText={settings.email_provider === 'gmail' ? "Using port 587" : ""}
                    />
                  </Grid>

                  {/* SMTP TLS */}
                  <Grid item xs={12} sm={6} md={4}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.email_smtp_use_tls}
                          onChange={(e) => {
                            setSettings({
                              ...settings,
                              email_smtp_use_tls: e.target.checked,
                            });
                          }}
                          name="email_smtp_use_tls"
                          color="primary"
                          disabled={settings.email_provider === 'gmail'}
                        />
                      }
                      label="Use TLS"
                    />
                  </Grid>
                </>
              )}

              {/* Email Username */}
              <Grid item xs={12} sm={6} md={6}>
                <TextField
                  fullWidth
                  label={settings.email_provider === 'mailersend' ? "MailerSend API Key" : "Email Username"}
                  name="email_username"
                  value={settings.email_username}
                  onChange={handleInputChange}
                  helperText={settings.email_provider === 'mailersend' ? "API Key from MailerSend dashboard" : "Email account username/email"}
                />
              </Grid>

              {/* Email Password */}
              <Grid item xs={12} sm={6} md={6}>
                <TextField
                  fullWidth
                  label="Password"
                  name="email_password"
                  value={settings.email_password}
                  onChange={handleInputChange}
                  type="password"
                  autoComplete="current-password"
                  helperText={settings.email_provider === 'mailersend' ? "Not used for MailerSend (leave empty)" : "Email account password"}
                  disabled={settings.email_provider === 'mailersend'}
                />
              </Grid>

              {/* From Email */}
              <Grid item xs={12} sm={6} md={6}>
                <TextField
                  fullWidth
                  label="From Email Address"
                  name="email_from_email"
                  value={settings.email_from_email}
                  onChange={handleInputChange}
                  helperText="Email address shown in the From field"
                />
              </Grid>

              {/* From Name */}
              <Grid item xs={12} sm={6} md={6}>
                <TextField
                  fullWidth
                  label="From Name"
                  name="email_from_name"
                  value={settings.email_from_name}
                  onChange={handleInputChange}
                  helperText="Display name shown in the From field"
                />
              </Grid>

              {/* Recipients */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Recipients"
                  name="email_recipients"
                  value={settings.email_recipients}
                  onChange={handleInputChange}
                  helperText="Comma-separated list of email addresses to receive notifications"
                />
              </Grid>

              {/* Email Subject */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Digest Email Subject"
                  name="email_digest_subject"
                  value={settings.email_digest_subject}
                  onChange={handleInputChange}
                  helperText="Subject line for digest emails (date will be appended)"
                />
              </Grid>

              {/* Submit Button */}
              <Grid item xs={12} sx={{ mt: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  startIcon={<SaveIcon />}
                  disabled={loading}
                >
                  Save Settings
                </Button>
              </Grid>
            </Grid>
          </form>
        </Paper>
      )}


      {/* Success/Error Notifications */}
      <Snackbar
        open={success}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success" sx={{ width: '100%' }}>
          {successMessage || "Settings updated successfully!"}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="error" sx={{ width: '100%' }}>
          {errorMessage || error}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Settings;