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
        // Add a state parameter to the navigation to indicate a refresh is needed
        navigate('/vacancies', { state: { refreshNeeded: true, action: 'deleted' } });
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
      console.log("Match_Toelichting found, type:", typeof vacancy.Match_Toelichting);
      
      // Try to parse the match details as JSON
      if (typeof vacancy.Match_Toelichting === 'string') {
        console.log("String format detected, length:", vacancy.Match_Toelichting.length);
        try {
          matchDetails = JSON.parse(vacancy.Match_Toelichting);
          console.log('Successfully parsed match details as JSON:', matchDetails);
        } catch (jsonError) {
          console.error('Failed to parse match details as JSON:', jsonError);
          // If not valid JSON, check if it might be a stringified JSON string (double encoded)
          try {
            const unescaped = vacancy.Match_Toelichting.replace(/\\"/g, '"');
            matchDetails = JSON.parse(unescaped);
            console.log('Successfully parsed double-encoded match details');
          } catch (doubleJsonError) {
            console.error('Not a double-encoded JSON either:', doubleJsonError);
            // If not JSON at all, use the raw text
            matchDetails = { raw_text: vacancy.Match_Toelichting };
          }
        }
      } else if (typeof vacancy.Match_Toelichting === 'object') {
        console.log("Object format detected, keys:", Object.keys(vacancy.Match_Toelichting).length);
        
        // Check if it might be a character-by-character object
        const keys = Object.keys(vacancy.Match_Toelichting);
        const isNumericKeys = keys.every(key => !isNaN(parseInt(key)));
        console.log("All keys are numeric:", isNumericKeys);
        
        // Check if keys are sequential
        const isSequential = keys.length > 0 && 
                             keys.map(Number).sort((a, b) => a - b).join(',') === 
                             [...Array(keys.length).keys()].join(',');
        console.log("Keys are sequential:", isSequential);
        
        // If both conditions are true, this is likely a character-by-character object
        if (isNumericKeys && isSequential) {
          console.log("Character-by-character format detected");
          try {
            // Combine all characters into a single string and parse
            const combinedString = Object.values(vacancy.Match_Toelichting).join('');
            console.log("Combined string (first 100 chars):", combinedString.substring(0, 100));
            matchDetails = JSON.parse(combinedString);
            console.log('Successfully parsed character-by-character JSON:', matchDetails);
          } catch (charJsonError) {
            console.error('Failed to parse character JSON:', charJsonError);
            // If not parseable as JSON, store as raw object
            console.log("Storing original character-by-character object for direct handling in renderer");
            matchDetails = vacancy.Match_Toelichting;
          }
        } else {
          // Already a proper object, use as is
          console.log("Using object as-is");
          matchDetails = vacancy.Match_Toelichting;
        }
      }
    } else {
      console.log("No Match_Toelichting found in vacancy");
    }
  } catch (e) {
    console.error('Error handling match details:', e);
  }
  
  // Add debug output after processing
  console.log("Final matchDetails type:", typeof matchDetails);
  if (typeof matchDetails === 'object') {
    console.log("matchDetails keys:", Object.keys(matchDetails));
  }

  // Function to render match details in a more readable format
  const renderMatchDetails = (text) => {
    if (!text) return null;

    // Handle the character-by-character array case first
    if (typeof text === 'object' && !Array.isArray(text)) {
      // Check if it's a character-by-character object (keys are sequential numbers)
      const keys = Object.keys(text);
      const isNumericKeys = keys.every(key => !isNaN(parseInt(key)));
      
      if (isNumericKeys) {
        // Sort the keys numerically to ensure correct order
        const sortedKeys = keys.map(Number).sort((a, b) => a - b);
        
        // Check if keys are sequential
        const isSequential = sortedKeys.length > 0 && 
                            sortedKeys.join(',') === 
                            [...Array(sortedKeys.length).keys()].join(',');
        
        if (isSequential) {
          console.log("Detected character-by-character format, rebuilding string");
          
          // Use sortedKeys to maintain proper order
          const combinedString = sortedKeys.map(key => 
            text[key.toString()]
          ).join('');
          
          try {
            // Try to parse the reconstructed string as JSON
            const jsonObject = JSON.parse(combinedString);
            console.log("Successfully parsed combined string as JSON");
            return renderJsonAsHtml(jsonObject);
          } catch (e) {
            console.error("Failed to parse combined string as JSON:", e);
            // If not valid JSON, display the combined string as plain text
            return formatAsMarkdown(combinedString);
          }
        }
      }
    }

    // Regular string case
    if (typeof text === 'string') {
      try {
        const jsonObject = JSON.parse(text);
        return renderJsonAsHtml(jsonObject);
      } catch (e) {
        // Not JSON, try to format as markdown-like text
        return formatAsMarkdown(text);
      }
    } else if (typeof text === 'object') {
      return renderJsonAsHtml(text);
    }
    
    // Fallback to plain text
    return text;
  };

  // Convert JSON to styled HTML
  const renderJsonAsHtml = (jsonObj) => {
    // Handle case where jsonObj might be a string that needs parsing
    let parsedObj = jsonObj;
    
    if (typeof jsonObj === 'string') {
      try {
        // Try to parse string as JSON
        parsedObj = JSON.parse(jsonObj);
      } catch (e) {
        // Not a parseable JSON string
        return (
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {jsonObj.toString()}
          </Typography>
        );
      }
    } else if (typeof jsonObj === 'object' && !Array.isArray(jsonObj)) {
      // Check if it's a character-by-character object (keys are sequential numbers)
      const keys = Object.keys(jsonObj);
      const isNumericKeys = keys.every(key => !isNaN(parseInt(key)));
      
      if (isNumericKeys) {
        // Sort the keys numerically to ensure correct order
        const sortedKeys = keys.map(Number).sort((a, b) => a - b);
        
        // Check if keys are sequential
        const isSequential = sortedKeys.length > 0 && 
                             sortedKeys.join(',') === 
                             [...Array(sortedKeys.length).keys()].join(',');
        
        if (isSequential) {
          console.log("renderJsonAsHtml: Found character-by-character object");
          
          // Use sortedKeys to maintain proper order
          const combinedString = sortedKeys.map(key => 
            jsonObj[key.toString()]
          ).join('');
          
          try {
            // Try to parse the reconstructed string as JSON
            parsedObj = JSON.parse(combinedString);
          } catch (e) {
            console.error("Failed to parse combined string as JSON:", e);
            // If not valid JSON, display the combined string as plain text
            return (
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {combinedString}
              </Typography>
            );
          }
        }
      }
    }
    
    // If it's an array
    if (Array.isArray(parsedObj)) {
      return (
        <Box component="div">
          {parsedObj.map((item, i) => (
            <Box key={i} sx={{ mb: 2 }}>
              {typeof item === 'object' ? renderJsonAsHtml(item) : item}
            </Box>
          ))}
        </Box>
      );
    }
    
    // If it's an object
    if (typeof parsedObj === 'object' && parsedObj !== null) {
      return (
        <Box component="div">
          {Object.entries(parsedObj).map(([key, value], i) => {
            // Skip numeric keys that might be from character-by-character parsing
            if (!isNaN(parseInt(key)) && typeof value === 'string' && value.length === 1) {
              return null;
            }
            
            const formattedKey = key.replace(/_/g, ' ');
            
            if (typeof value === 'object' && value !== null) {
              return (
                <Box key={i} sx={{ mb: 2 }}>
                  <Typography variant="h6" sx={{ color: 'primary.main', mb: 1 }}>
                    {formattedKey}:
                  </Typography>
                  <Box sx={{ pl: 2 }}>
                    {renderJsonAsHtml(value)}
                  </Box>
                </Box>
              );
            }
            
            // Handle arrays
            if (Array.isArray(value)) {
              return (
                <Box key={i} sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    {formattedKey}:
                  </Typography>
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    {value.map((item, j) => (
                      <li key={j}>
                        <Typography variant="body2">{item}</Typography>
                      </li>
                    ))}
                  </ul>
                </Box>
              );
            }
            
            // Simple key-value pairs
            return (
              <Box key={i} sx={{ mb: 1 }}>
                <Typography variant="body1">
                  <strong>{formattedKey}:</strong> {value}
                </Typography>
              </Box>
            );
          })}
        </Box>
      );
    }
    
    // Fallback for primitive values
    return (
      <Typography variant="body1">
        {String(parsedObj)}
      </Typography>
    );
  };

  // Format plain text as markdown-like content
  const formatAsMarkdown = (text) => {
    if (!text) return null;
    
    // Split by lines
    const lines = text.split('\n');
    
    return (
      <Box component="div">
        {lines.map((line, i) => {
          // Heading detection
          if (line.startsWith('# ')) {
            return (
              <Typography key={i} variant="h4" gutterBottom>
                {line.substring(2)}
              </Typography>
            );
          }
          
          if (line.startsWith('## ')) {
            return (
              <Typography key={i} variant="h5" gutterBottom sx={{ color: 'primary.main' }}>
                {line.substring(3)}
              </Typography>
            );
          }
          
          if (line.startsWith('### ')) {
            return (
              <Typography key={i} variant="h6" gutterBottom>
                {line.substring(4)}
              </Typography>
            );
          }
          
          // List item detection
          if (line.startsWith('- ') || line.startsWith('* ')) {
            return (
              <Box key={i} sx={{ display: 'flex', alignItems: 'flex-start', mb: 0.5 }}>
                <Box component="span" sx={{ mr: 1 }}>•</Box>
                <Typography variant="body2">{line.substring(2)}</Typography>
              </Box>
            );
          }
          
          // Empty line
          if (line.trim() === '') {
            return <Box key={i} sx={{ height: '0.5em' }} />;
          }
          
          // Regular paragraph
          return (
            <Typography key={i} variant="body2" paragraph>
              {line}
            </Typography>
          );
        })}
      </Box>
    );
  };

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
        <Grid item xs={12} lg={8}>
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

        {/* Sidebar with Vacancy Source Information */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardHeader 
              title="Vacancy Source" 
              sx={{
                bgcolor: 'background.paper',
                borderBottom: '1px solid',
                borderColor: 'divider'
              }}
            />
            <CardContent>
              <Typography variant="body2" gutterBottom>
                <strong>URL:</strong>{' '}
                <a 
                  href={`https://${vacancy.URL}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  sx={{ 
                    color: 'primary.main', 
                    textDecoration: 'none',
                    '&:hover': {
                      textDecoration: 'underline'
                    }
                  }}
                >
                  {vacancy.URL}
                </a>
              </Typography>
              <Divider sx={{ my: 1.5 }} />
              <Typography variant="body2" gutterBottom>
                <strong>AI Model:</strong> {vacancy.Model || 'Not specified'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Version:</strong> {vacancy.Version || 'Not specified'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Top Match Score:</strong> {vacancy.Top_Match || 0}%
              </Typography>

              {vacancy.Checked_resumes && (
                <>
                  <Divider sx={{ my: 1.5 }} />
                  <Typography variant="subtitle1" gutterBottom>
                    <strong>Resumes Evaluated:</strong> {vacancy.Checked_resumes.split(',').length}
                  </Typography>
                  <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {vacancy.Checked_resumes.split(',').map((name) => (
                      <Chip
                        key={name}
                        label={name.trim()}
                        size="small"
                        sx={{ 
                          bgcolor: 'primary.light', 
                          color: 'primary.contrastText',
                          borderRadius: '4px',
                          '&:hover': {
                            bgcolor: 'primary.main',
                          }
                        }}
                      />
                    ))}
                  </Box>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Match Details - Full Width Section */}
        <Grid item xs={12}>
          <Card sx={{ mb: 3 }}>
            <CardHeader
              title="Match Details"
              sx={{
                bgcolor: 'background.paper',
                borderBottom: '1px solid',
                borderColor: 'divider'
              }}
            />
            <CardContent>
              {!vacancy.Checked_resumes && (
                <Typography variant="body2" color="text.secondary">
                  No resumes have been evaluated yet
                </Typography>
              )}

              {/* Simple JSON formatted display of match details */}
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Match Details:
                </Typography>
                <Box sx={{ 
                  p: 3, 
                  bgcolor: 'background.default', 
                  borderRadius: 2, 
                  border: '1px solid', 
                  borderColor: 'divider' 
                }}>
                  <pre style={{ 
                    margin: 0, 
                    padding: 0, 
                    overflow: 'auto', 
                    maxHeight: '800px',
                    fontSize: '14px',
                    fontFamily: 'monospace',
                    whiteSpace: 'pre',
                    wordBreak: 'break-all'
                  }}>
                    {(() => {
                      // Simple format JSON data from Match_Toelichting
                      if (vacancy.Match_Toelichting) {
                        // Handle character-by-character object first
                        if (typeof vacancy.Match_Toelichting === 'object' && 
                            !Array.isArray(vacancy.Match_Toelichting)) {
                          
                          // Check for character-by-character data
                          const keys = Object.keys(vacancy.Match_Toelichting);
                          const isNumericKeys = keys.every(key => !isNaN(parseInt(key)));
                          
                          if (isNumericKeys) {
                            // Sort the keys numerically to ensure correct order
                            const sortedKeys = keys.map(Number).sort((a, b) => a - b);
                            
                            // Combine characters into a single string
                            const combinedString = sortedKeys.map(key => 
                              vacancy.Match_Toelichting[key.toString()]
                            ).join('');
                            
                            // Handle double-encoded JSON (string with escape sequences and quotes)
                            if (combinedString.startsWith('"') && 
                                (combinedString.includes('\\n') || combinedString.includes('\\{'))) {
                              try {
                                // Remove outer quotes and unescape
                                const unquoted = combinedString.slice(1, -1);
                                // Replace all escaped characters
                                const unescaped = unquoted
                                  .replace(/\\"/g, '"')   // Replace \" with "
                                  .replace(/\\\\/g, '\\') // Replace \\ with \
                                  .replace(/\\n/g, '\n')  // Replace \n with actual newlines
                                  .replace(/\\t/g, '\t')  // Replace \t with actual tabs
                                  .replace(/\\r/g, '\r'); // Replace \r with actual carriage returns
                                
                                try {
                                  // Try to parse and format
                                  const parsedJson = JSON.parse(unescaped);
                                  return JSON.stringify(parsedJson, null, 2);
                                } catch {
                                  // If parsing fails, return the unescaped string with newlines preserved
                                  return unescaped;
                                }
                              } catch {
                                // If unescaping fails, return the combined string
                                return combinedString;
                              }
                            } else {
                              // Not a double-encoded string, format directly
                              try {
                                const parsedJson = JSON.parse(combinedString);
                                return JSON.stringify(parsedJson, null, 2);
                              } catch {
                                return combinedString;
                              }
                            }
                          } else {
                            // Regular object
                            return JSON.stringify(vacancy.Match_Toelichting, null, 2);
                          }
                        } else if (typeof vacancy.Match_Toelichting === 'string') {
                          // Handle string data
                          
                          // Case 1: Double-encoded JSON string
                          if (vacancy.Match_Toelichting.startsWith('"') && 
                              (vacancy.Match_Toelichting.includes('\\n') || 
                               vacancy.Match_Toelichting.includes('\\{'))) {
                            try {
                              // Remove quotes and unescape
                              const unquoted = vacancy.Match_Toelichting.slice(1, -1);
                              // Replace all escaped characters
                              const unescaped = unquoted
                                .replace(/\\"/g, '"')   // Replace \" with "
                                .replace(/\\\\/g, '\\') // Replace \\ with \
                                .replace(/\\n/g, '\n')  // Replace \n with actual newlines
                                .replace(/\\t/g, '\t')  // Replace \t with actual tabs
                                .replace(/\\r/g, '\r'); // Replace \r with actual carriage returns
                              
                              try {
                                // Try to parse and format
                                const parsedJson = JSON.parse(unescaped);
                                return JSON.stringify(parsedJson, null, 2);
                              } catch {
                                // If parsing fails, return the unescaped string with newlines preserved
                                return unescaped;
                              }
                            } catch {
                              // If unescaping fails, check if it's JSON already
                              try {
                                const parsedJson = JSON.parse(vacancy.Match_Toelichting);
                                return JSON.stringify(parsedJson, null, 2);
                              } catch {
                                return vacancy.Match_Toelichting;
                              }
                            }
                          } else {
                            // Regular string, try JSON parsing
                            try {
                              const parsedJson = JSON.parse(vacancy.Match_Toelichting);
                              return JSON.stringify(parsedJson, null, 2);
                            } catch {
                              // Not JSON, return as is
                              return vacancy.Match_Toelichting;
                            }
                          }
                        } else {
                          // Any other type
                          return String(vacancy.Match_Toelichting);
                        }
                      }
                      
                      return "No match details available";
                    })()}
                  </pre>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default VacancyDetail;