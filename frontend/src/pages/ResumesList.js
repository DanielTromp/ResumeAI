import React, { useState, useEffect } from 'react';
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
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import axios from 'axios';

const ResumesList = () => {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [totalResumes, setTotalResumes] = useState(0);

  useEffect(() => {
    const fetchResumes = async () => {
      try {
        setLoading(true);
        // Prepare query parameters
        const params = new URLSearchParams();
        params.append('skip', page * rowsPerPage);
        params.append('limit', rowsPerPage);

        const response = await axios.get(`/api/resumes?${params.toString()}`);
        setResumes(response.data.items);
        setTotalResumes(response.data.total);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching resumes:', err);
        setError('Failed to load resumes. Please try again later.');
        setLoading(false);
      }
    };

    fetchResumes();
  }, [page, rowsPerPage]);

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

  // Filter resumes based on search term
  const filteredResumes = resumes.filter(resume => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      resume.name.toLowerCase().includes(searchLower)
    );
  });

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
            sx={{ mr: 2 }}
          >
            Upload Resume
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
          >
            Add Resume
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
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
                  <TableCell>Name</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Updated</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredResumes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      No resumes found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredResumes.map((resume) => (
                    <TableRow key={resume.id}>
                      <TableCell>{resume.name}</TableCell>
                      <TableCell>{new Date(resume.created_at).toLocaleDateString()}</TableCell>
                      <TableCell>{new Date(resume.updated_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="outlined"
                        >
                          View
                        </Button>
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
    </Container>
  );
};

export default ResumesList;