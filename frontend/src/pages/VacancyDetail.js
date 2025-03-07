import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Button,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  CardHeader,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';
import { getVacancyById, updateVacancy, deleteVacancy } from '../utils/api';

const VacancyDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [vacancy, setVacancy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editedVacancy, setEditedVacancy] = useState(null);

  // Status options for dropdown
  const statusOptions = [
    { value: 'Nieuw', label: 'New' },
    { value: 'Open', label: 'Open' },
    { value: 'AI afgewezen', label: 'AI Rejected' },
    { value: 'Voorgesteld', label: 'Proposed' },
    { value: 'Error', label: 'Error' },
    { value: 'Gesloten', label: 'Closed' },
  ];

  // Status color mapping
  const getStatusColor = (status) => {
    switch (status) {
      case 'Nieuw':
        return 'primary';
      case 'Open':
        return 'success';
      case 'AI afgewezen':
        return 'error';
      case 'Voorgesteld':
        return 'warning';
      case 'Error':
        return 'error';
      case 'Gesloten':
        return 'default';
      default:
        return 'default';
    }
  };

  useEffect(() => {
    const fetchVacancy = async () => {
      try {
        setLoading(true);
        console.log('Fetching vacancy with ID:', id);
        const response = await getVacancyById(id);
        console.log('Vacancy response data:', response.data);
        
        // Check for valid data structure before setting state
        if (response.data && response.data.URL) {
          setVacancy(response.data);
          setEditedVacancy(response.data);
          setLoading(false);
        } else {
          console.error('Invalid vacancy data received:', response.data);
          setError('Received invalid vacancy data format from server');
          setLoading(false);
        }
      } catch (err) {
        console.error('Error fetching vacancy:', err);
        setError(`Failed to load vacancy details: ${err.message}`);
        setLoading(false);
      }
    };

    fetchVacancy();
  }, [id]);

  const handleEditToggle = () => {
    setEditing(!editing);
    if (!editing) {
      // When starting to edit, initialize editedVacancy with current vacancy
      setEditedVacancy({ ...vacancy });
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditedVacancy({
      ...editedVacancy,
      [name]: value,
    });
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const response = await updateVacancy(id, editedVacancy);
      setVacancy(response.data);
      setEditing(false);
      setLoading(false);
    } catch (err) {
      console.error('Error updating vacancy:', err);
      setError('Failed to update vacancy. Please try again later.');
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this vacancy?')) {
      try {
        setLoading(true);
        await deleteVacancy(id);
        navigate('/vacancies');
      } catch (err) {
        console.error('Error deleting vacancy:', err);
        setError('Failed to delete vacancy. Please try again later.');
        setLoading(false);
      }
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/vacancies')}
        >
          Back to Vacancies
        </Button>
      </Container>
    );
  }

  if (!vacancy) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="info">Vacancy not found</Alert>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/vacancies')}
          sx={{ mt: 2 }}
        >
          Back to Vacancies
        </Button>
      </Container>
    );
  }

  // Parse match details if available
  let matchDetails = null;
  try {
    if (vacancy.Match_Toelichting) {
      matchDetails = JSON.parse(vacancy.Match_Toelichting);
    }
  } catch (e) {
    console.error('Error parsing match details:', e);
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/vacancies')}
            sx={{ mr: 2 }}
          >
            Back
          </Button>
          <Typography variant="h4" component="h1">
            Vacancy Details
          </Typography>
        </Box>
        <Box>
          {editing ? (
            <Button
              variant="contained"
              color="primary"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              sx={{ mr: 1 }}
            >
              Save
            </Button>
          ) : (
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={handleEditToggle}
              sx={{ mr: 1 }}
            >
              Edit
            </Button>
          )}
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDelete}
          >
            Delete
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Main Vacancy Information */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            {editing ? (
              <>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Job Title"
                      name="Functie"
                      value={editedVacancy.Functie || ''}
                      onChange={handleInputChange}
                      variant="outlined"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Client"
                      name="Klant"
                      value={editedVacancy.Klant || ''}
                      onChange={handleInputChange}
                      variant="outlined"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth variant="outlined">
                      <InputLabel>Status</InputLabel>
                      <Select
                        name="Status"
                        value={editedVacancy.Status || ''}
                        onChange={handleInputChange}
                        label="Status"
                      >
                        {statusOptions.map((option) => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Industry"
                      name="Branche"
                      value={editedVacancy.Branche || ''}
                      onChange={handleInputChange}
                      variant="outlined"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Region"
                      name="Regio"
                      value={editedVacancy.Regio || ''}
                      onChange={handleInputChange}
                      variant="outlined"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Hours"
                      name="Uren"
                      value={editedVacancy.Uren || ''}
                      onChange={handleInputChange}
                      variant="outlined"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Rate"
                      name="Tarief"
                      value={editedVacancy.Tarief || ''}
                      onChange={handleInputChange}
                      variant="outlined"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Job Description"
                      name="Functieomschrijving"
                      value={editedVacancy.Functieomschrijving || ''}
                      onChange={handleInputChange}
                      variant="outlined"
                      multiline
                      rows={10}
                    />
                  </Grid>
                </Grid>
              </>
            ) : (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h5" component="h2">
                    {vacancy.Functie}
                  </Typography>
                  <Chip
                    label={vacancy.Status}
                    color={getStatusColor(vacancy.Status)}
                  />
                </Box>
                <Typography variant="body1" gutterBottom>
                  <strong>Client:</strong> {vacancy.Klant}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Industry:</strong> {vacancy.Branche}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Region:</strong> {vacancy.Regio}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Hours:</strong> {vacancy.Uren}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Rate:</strong> {vacancy.Tarief}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Posted:</strong> {vacancy.Geplaatst}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Closing:</strong> {vacancy.Sluiting || 'Not specified'}
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Job Description
                </Typography>
                <Typography
                  variant="body1"
                  sx={{ whiteSpace: 'pre-wrap' }}
                >
                  {vacancy.Functieomschrijving}
                </Typography>
              </>
            )}
          </Paper>
        </Grid>

        {/* Sidebar - Match Information */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardHeader
              title="Match Details"
              subheader={`Match Score: ${vacancy.Top_Match || 0}%`}
            />
            <CardContent>
              {vacancy.Checked_resumes ? (
                <>
                  <Typography variant="subtitle1" gutterBottom>
                    Checked Resumes:
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    {vacancy.Checked_resumes.split(',').map((name) => (
                      <Chip
                        key={name}
                        label={name.trim()}
                        size="small"
                        sx={{ m: 0.5 }}
                      />
                    ))}
                  </Box>
                </>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No resumes checked yet
                </Typography>
              )}

              {matchDetails && matchDetails.beste_match && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle1" gutterBottom>
                    Best Match: {matchDetails.beste_match.name} ({matchDetails.beste_match.percentage}%)
                  </Typography>
                  <Typography variant="subtitle2" sx={{ mt: 1 }}>
                    Strengths:
                  </Typography>
                  <ul>
                    {matchDetails.beste_match.sterke_punten.map((point, index) => (
                      <li key={index}>
                        <Typography variant="body2">{point}</Typography>
                      </li>
                    ))}
                  </ul>
                  <Typography variant="subtitle2" sx={{ mt: 1 }}>
                    Weaknesses:
                  </Typography>
                  <ul>
                    {matchDetails.beste_match.zwakke_punten.map((point, index) => (
                      <li key={index}>
                        <Typography variant="body2">{point}</Typography>
                      </li>
                    ))}
                  </ul>
                  <Typography variant="subtitle2" sx={{ mt: 1 }}>
                    Final Assessment:
                  </Typography>
                  <Typography variant="body2">
                    {matchDetails.beste_match.eindoordeel}
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader title="Vacancy Information" />
            <CardContent>
              <Typography variant="body2" gutterBottom>
                <strong>URL:</strong>{' '}
                <a href={`https://${vacancy.URL}`} target="_blank" rel="noopener noreferrer">
                  {vacancy.URL}
                </a>
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>AI Model:</strong> {vacancy.Model || 'Not specified'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Version:</strong> {vacancy.Version || 'Not specified'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default VacancyDetail;