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
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import axios from 'axios';
import { ColorModeContext } from '../App';

const Settings = () => {
  const theme = useTheme();
  const colorMode = useContext(ColorModeContext);

  const [settings, setSettings] = useState({
    openai_api_key: '',
    supabase_url: '',
    supabase_key: '',
    nocodb_url: '',
    nocodb_token: '',
    nocodb_project: '',
    nocodb_table: '',
    spinweb_user: '',
    spinweb_pass: '',
    excluded_clients: '',
    ai_model: '',
    match_threshold: '',
    match_count: '',
    resume_prompt_template: '',
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/settings');
        setSettings(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching settings:', err);
        setError('Failed to load settings. Please try again later.');
        setLoading(false);
      }
    };

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
      await axios.put('/api/settings', settings);
      setSuccess(true);
      setLoading(false);
    } catch (err) {
      console.error('Error updating settings:', err);
      setError('Failed to update settings. Please try again later.');
      setLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSuccess(false);
    setError(null);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>

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

              {/* Supabase Configuration */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Supabase Configuration
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Supabase URL"
                  name="supabase_url"
                  value={settings.supabase_url}
                  onChange={handleInputChange}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Supabase Key"
                  name="supabase_key"
                  value={settings.supabase_key}
                  onChange={handleInputChange}
                  type="password"
                />
              </Grid>

              {/* NocoDB Configuration */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  NocoDB Configuration
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="NocoDB URL"
                  name="nocodb_url"
                  value={settings.nocodb_url}
                  onChange={handleInputChange}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="NocoDB Token"
                  name="nocodb_token"
                  value={settings.nocodb_token}
                  onChange={handleInputChange}
                  type="password"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="NocoDB Project"
                  name="nocodb_project"
                  value={settings.nocodb_project}
                  onChange={handleInputChange}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="NocoDB Table"
                  name="nocodb_table"
                  value={settings.nocodb_table}
                  onChange={handleInputChange}
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
          Settings updated successfully!
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

export default Settings;