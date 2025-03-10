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
  Grid,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';
import VisibilityIcon from '@mui/icons-material/Visibility';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import CloseIcon from '@mui/icons-material/Close';
import RefreshIcon from '@mui/icons-material/Refresh';
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
      
      // Add cache-busting timestamp
      params.append('_', new Date().getTime());

      // If showOnlySelected is true, use the selected endpoint
      const endpoint = showOnlySelected ? '/api/resumes/selected' : '/api/resumes';
      const response = await axios.get(`${endpoint}?${params.toString()}`, {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      console.log('Resumes fetched:', response.data);
      setResumes(response.data.items);
      setTotalResumes(response.data.total);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching resumes:', err);
      setError('Failed to load resumes. Please try again later.');
      setLoading(false);
    }
  };

  // Add useEffect after fetchResumes is defined
  useEffect(() => {
    fetchResumes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, rowsPerPage, showOnlySelected, searchTerm]);

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
            startIcon={<RefreshIcon />}
            onClick={fetchResumes}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<UploadFileIcon />}
            onClick={handleUploadDialogOpen}
          >
            Upload Resume
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <form onSubmit={handleSearchSubmit}>
              <TextField
                fullWidth
                label="Search resumes"
                value={searchTerm}
                onChange={handleSearchChange}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton type="submit" edge="end">
                        <SearchIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </form>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={showOnlySelected}
                  onChange={(e) => setShowOnlySelected(e.target.checked)}
                  color="primary"
                />
              }
              label="Show only selected resumes"
            />
          </Grid>
        </Grid>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper>
        {loading ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Tooltip title="Toggle selection">
                        <span>
                          <Checkbox disabled />
                        </span>
                      </Tooltip>
                    </TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Date Added</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {resumes.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        {showOnlySelected
                          ? "No selected resumes found. Select resumes to see them here."
                          : "No resumes found. Upload a resume to get started."}
                      </TableCell>
                    </TableRow>
                  ) : (
                    resumes.map((resume) => (
                      <TableRow key={resume.name} hover selected={resume.file_info?.selected}>
                        <TableCell padding="checkbox">
                          <Checkbox
                            checked={!!resume.file_info?.selected}
                            onChange={() => toggleResumeSelection(resume)}
                            color="primary"
                          />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <PictureAsPdfIcon sx={{ mr: 1, color: theme.palette.error.main }} />
                            {resume.name}
                          </Box>
                        </TableCell>
                        <TableCell>
                          {new Date(resume.file_info?.creation_time || Date.now()).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          {formatFileSize(resume.file_info?.size || 0)}
                        </TableCell>
                        <TableCell align="right">
                          <Tooltip title="View Resume">
                            <IconButton onClick={() => handleViewResume(resume)}>
                              <VisibilityIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Download">
                            <IconButton onClick={() => handleDownload(resume)}>
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton onClick={() => handleDeleteClick(resume)}>
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
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
      </Paper>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onClose={handleUploadDialogClose}>
        <DialogTitle>Upload Resume</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Select a PDF file to upload as a resume. The filename will be used as the resume name.
          </DialogContentText>
          <Box sx={{ mt: 2 }}>
            <input
              ref={fileInputRef}
              accept="application/pdf"
              type="file"
              onChange={handleFileUpload}
              disabled={uploading}
              style={{ display: 'none' }}
              id="resume-file-upload"
            />
            <label htmlFor="resume-file-upload">
              <Button
                variant="contained"
                component="span"
                startIcon={<UploadFileIcon />}
                disabled={uploading}
                fullWidth
              >
                Select PDF File
              </Button>
            </label>
          </Box>
          {uploading && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
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
          <Button onClick={handleUploadDialogClose} disabled={uploading}>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Resume Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={handleViewDialogClose}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          {selectedResume?.name}
          <IconButton
            aria-label="close"
            onClick={handleViewDialogClose}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {selectedResume && (
            <Box sx={{ height: '80vh' }}>
              <iframe
                src={`/api/resumes/download/${encodeURIComponent(selectedResume.file_info.filename)}#toolbar=0`}
                width="100%"
                height="100%"
                title={selectedResume.name}
                style={{ border: 'none' }}
              />
            </Box>
          )}
        </DialogContent>
      </Dialog>

      {/* Confirm Delete Dialog */}
      <Dialog
        open={confirmDeleteOpen}
        onClose={handleCancelDelete}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the resume "{selectedResume?.name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete}>Cancel</Button>
          <Button onClick={handleConfirmDelete} color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notifications */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
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