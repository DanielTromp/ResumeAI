import React, { useState, useEffect, useRef } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  CircularProgress,
  Alert,
  TextField,
  InputAdornment,
  IconButton,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Snackbar,
  Tooltip,
  FormControlLabel,
  Switch,
  useTheme,
  LinearProgress,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';
import VisibilityIcon from '@mui/icons-material/Visibility';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import CloseIcon from '@mui/icons-material/Close';
import axios from 'axios';

const ResumesList = () => {
  const theme = useTheme();
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [totalResumes, setTotalResumes] = useState(0);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [selectedResume, setSelectedResume] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [showOnlySelected, setShowOnlySelected] = useState(false);
  const fileInputRef = useRef(null);
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // Add useEffect after all declarations
  useEffect(() => {
    // Fetch resumes when component mounts or when dependencies change
    const getResumes = async () => {
      try {
        setLoading(true);
        // Prepare query parameters
        const params = new URLSearchParams();
        params.append('skip', page * rowsPerPage);
        params.append('limit', rowsPerPage);
        
        if (searchTerm) {
          params.append('search', searchTerm);
        }

        // If showOnlySelected is true, use the selected endpoint
        const endpoint = showOnlySelected ? '/api/resumes/selected' : '/api/resumes';
        const response = await axios.get(`${endpoint}?${params.toString()}`);
        
        setResumes(response.data.items);
        setTotalResumes(response.data.total);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching resumes:', err);
        setError('Failed to load resumes. Please try again later.');
        setLoading(false);
      }
    };
    
    getResumes();
  }, [page, rowsPerPage, showOnlySelected, searchTerm]);
  
  // Define fetchResumes function for manual refreshes
  const fetchResumes = async () => {
    try {
      setLoading(true);
      // Prepare query parameters
      const params = new URLSearchParams();
      params.append('skip', page * rowsPerPage);
      params.append('limit', rowsPerPage);
      
      if (searchTerm) {
        params.append('search', searchTerm);
      }

      // If showOnlySelected is true, use the selected endpoint
      const endpoint = showOnlySelected ? '/api/resumes/selected' : '/api/resumes';
      const response = await axios.get(`${endpoint}?${params.toString()}`);
      
      setResumes(response.data.items);
      setTotalResumes(response.data.total);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching resumes:', err);
      setError('Failed to load resumes. Please try again later.');
      setLoading(false);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    fetchResumes();
  };

  const handleUploadDialogOpen = () => {
    setUploadDialogOpen(true);
  };

  const handleUploadDialogClose = () => {
    setUploadDialogOpen(false);
    setUploadProgress(0);
    setUploading(false);
    setUploadSuccess(false);
  };

  const handleViewResume = (resume) => {
    console.log('Viewing resume:', resume);
    setSelectedResume(resume);
    setViewDialogOpen(true);
    
    // Pre-validate the file exists
    const fileUrl = `/api/resumes/download/${encodeURIComponent(resume.file_info.filename)}`;
    console.log('Testing file URL:', fileUrl);
    
    fetch(fileUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
      })
      .catch(error => {
        console.error('Error testing file availability:', error);
        showNotification('Error loading resume for preview', 'error');
      });
  };

  const handleViewDialogClose = () => {
    setViewDialogOpen(false);
    setSelectedResume(null);
  };

  const handleDeleteClick = (resume) => {
    setSelectedResume(resume);
    setConfirmDeleteOpen(true);
  };

  const handleCancelDelete = () => {
    setConfirmDeleteOpen(false);
    setSelectedResume(null);
  };

  const handleConfirmDelete = async () => {
    if (!selectedResume) return;
    
    try {
      await axios.delete(`/api/resumes/${selectedResume.name}`);
      setConfirmDeleteOpen(false);
      setSelectedResume(null);
      showNotification('Resume deleted successfully', 'success');
      fetchResumes();
    } catch (err) {
      console.error('Error deleting resume:', err);
      showNotification('Failed to delete resume', 'error');
      setConfirmDeleteOpen(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Check if file is a PDF
    if (!file.type.includes('pdf')) {
      showNotification('Only PDF files are accepted', 'error');
      return;
    }

    try {
      setUploading(true);
      
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      
      // Get name from filename without extension
      const fileName = file.name.replace(/\.[^/.]+$/, "");
      formData.append('name', fileName);
      
      // Upload the file with progress tracking
      await axios.post('/api/resumes/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });
      
      setUploadSuccess(true);
      showNotification('Resume uploaded successfully', 'success');
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Close dialog after delay
      setTimeout(() => {
        handleUploadDialogClose();
        fetchResumes();
      }, 1500);
      
    } catch (err) {
      console.error('Error uploading resume:', err);
      showNotification('Failed to upload resume', 'error');
      setUploading(false);
    }
  };

  const handleDownload = (resume) => {
    try {
      console.log('Downloading resume:', resume.file_info.filename);
      
      // Create a hidden anchor element
      const link = document.createElement('a');
      
      // Encode the full URL properly
      const filename = encodeURIComponent(resume.file_info.filename);
      const downloadUrl = `/api/resumes/download/${filename}`;
      
      console.log('Download URL:', downloadUrl);
      
      link.href = downloadUrl;
      link.download = resume.file_info.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('Error downloading resume:', err);
      showNotification('Failed to download resume', 'error');
    }
  };

  const toggleResumeSelection = async (resume) => {
    const isCurrentlySelected = resume.file_info?.selected || false;
    
    try {
      const endpoint = isCurrentlySelected 
        ? `/api/resumes/deselect/${resume.name}` 
        : `/api/resumes/select/${resume.name}`;
        
      await axios.post(endpoint);
      
      // Update local state
      setResumes(prev => 
        prev.map(r => 
          r.name === resume.name 
            ? {...r, file_info: {...r.file_info, selected: !isCurrentlySelected}} 
            : r
        )
      );
      
      showNotification(
        `Resume ${isCurrentlySelected ? 'deselected' : 'selected'} successfully`, 
        'success'
      );
    } catch (err) {
      console.error(`Error ${isCurrentlySelected ? 'deselecting' : 'selecting'} resume:`, err);
      showNotification(`Failed to ${isCurrentlySelected ? 'deselect' : 'select'} resume`, 'error');
    }
  };

  const showNotification = (message, severity) => {
    setNotification({
      open: true,
      message,
      severity
    });
  };

  const handleCloseNotification = () => {
    setNotification({
      ...notification,
      open: false
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Resumes
        </Typography>
        <Box>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<UploadFileIcon />}
            onClick={handleUploadDialogOpen}
            sx={{ mr: 2 }}
          >
            Upload Resume
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
          <form onSubmit={handleSearchSubmit} style={{ display: 'flex', flexGrow: 1 }}>
            <TextField
              label="Search by name"
              variant="outlined"
              size="small"
              value={searchTerm}
              onChange={handleSearchChange}
              sx={{ minWidth: '250px', flexGrow: 1 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
            <Button 
              type="submit"
              variant="contained"
              sx={{ ml: 1 }}
            >
              Search
            </Button>
          </form>
          
          <FormControlLabel
            control={
              <Switch
                checked={showOnlySelected}
                onChange={() => setShowOnlySelected(!showOnlySelected)}
                color="primary"
              />
            }
            label="Show only selected"
          />
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox">
                    <Tooltip title="Select/Deselect">
                      <span>Select</span>
                    </Tooltip>
                  </TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {resumes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      No resumes found
                    </TableCell>
                  </TableRow>
                ) : (
                  resumes.map((resume) => (
                    <TableRow 
                      key={resume.id}
                      sx={{
                        backgroundColor: resume.file_info?.selected ? 
                          theme.palette.mode === 'dark' ? 'rgba(0, 100, 0, 0.15)' : 'rgba(200, 255, 200, 0.35)' 
                          : 'inherit'
                      }}
                    >
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={resume.file_info?.selected || false}
                          onChange={() => toggleResumeSelection(resume)}
                          color="primary"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <PictureAsPdfIcon color="error" sx={{ mr: 1 }} />
                          {resume.name}
                        </Box>
                      </TableCell>
                      <TableCell>
                        {resume.file_info?.created_at 
                          ? new Date(resume.file_info.created_at).toLocaleDateString() 
                          : new Date(resume.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        {resume.file_info?.size ? formatFileSize(resume.file_info.size) : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Tooltip title="View">
                          <IconButton
                            onClick={() => handleViewResume(resume)}
                            size="small"
                            color="primary"
                          >
                            <VisibilityIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Download">
                          <IconButton
                            onClick={() => handleDownload(resume)}
                            size="small"
                            color="primary"
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            onClick={() => handleDeleteClick(resume)}
                            size="small"
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
            <TablePagination
              rowsPerPageOptions={[5, 10, 25, 50]}
              component="div"
              count={totalResumes}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </>
        )}
      </TableContainer>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onClose={handleUploadDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Resume</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Select a PDF file to upload as a resume.
          </DialogContentText>
          
          <Box sx={{ mb: 2 }}>
            <input
              accept="application/pdf"
              type="file"
              id="resume-upload"
              onChange={handleFileUpload}
              disabled={uploading}
              ref={fileInputRef}
              style={{ display: 'none' }}
            />
            <label htmlFor="resume-upload">
              <Button
                variant="contained"
                component="span"
                startIcon={<UploadFileIcon />}
                disabled={uploading}
              >
                Select PDF File
              </Button>
            </label>
          </Box>
          
          {uploading && (
            <Box sx={{ width: '100%', mt: 2 }}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Uploading: {uploadProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
          )}
          
          {uploadSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Resume uploaded successfully!
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleUploadDialogClose} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Resume Dialog */}
      <Dialog 
        open={viewDialogOpen} 
        onClose={handleViewDialogClose} 
        maxWidth="lg" 
        fullWidth
        PaperProps={{
          sx: { 
            height: '90vh',
            display: 'flex',
            flexDirection: 'column'
          }
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {selectedResume?.name}
            </Typography>
            <IconButton onClick={handleViewDialogClose} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ 
          flex: 1, 
          overflow: 'hidden',
          padding: 0,
          display: 'flex',
          flexDirection: 'column'
        }}>
          {selectedResume && (
            <iframe 
              src={`/api/resumes/download/${encodeURIComponent(selectedResume.file_info?.filename)}#toolbar=0`}
              title={selectedResume.name}
              width="100%" 
              height="100%"
              style={{ border: 'none', flex: 1 }}
              onError={(e) => {
                console.error('Error loading PDF in iframe:', e);
                showNotification('Error loading PDF preview', 'error');
              }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => selectedResume && handleDownload(selectedResume)} 
            color="primary"
            startIcon={<DownloadIcon />}
          >
            Download
          </Button>
          <Button 
            onClick={() => selectedResume && toggleResumeSelection(selectedResume)} 
            color="primary"
            variant={selectedResume?.file_info?.selected ? "outlined" : "contained"}
          >
            {selectedResume?.file_info?.selected ? "Deselect" : "Select"}
          </Button>
          <Button onClick={handleViewDialogClose} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog
        open={confirmDeleteOpen}
        onClose={handleCancelDelete}
      >
        <DialogTitle>Delete Resume</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the resume for '{selectedResume?.name}'? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete} color="primary">
            Cancel
          </Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={5000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity} 
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ResumesList;