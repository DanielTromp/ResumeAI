import React, { useState, useEffect } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Button,
  Chip,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import axios from 'axios';

const VacanciesList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialStatus = searchParams.get('status') || '';

  const [vacancies, setVacancies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState(initialStatus);
  const [totalVacancies, setTotalVacancies] = useState(0);

  // Status options for filtering
  const statusOptions = [
    { value: '', label: 'All Statuses' },
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
    const fetchVacancies = async () => {
      try {
        setLoading(true);
        // Prepare query parameters
        const params = new URLSearchParams();
        params.append('skip', page * rowsPerPage);
        params.append('limit', rowsPerPage);
        if (statusFilter) {
          params.append('status', statusFilter);
        }

        const response = await axios.get(`/api/vacancies?${params.toString()}`);
        setVacancies(response.data.items);
        setTotalVacancies(response.data.total);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching vacancies:', err);
        setError('Failed to load vacancies. Please try again later.');
        setLoading(false);
      }
    };

    fetchVacancies();
  }, [page, rowsPerPage, statusFilter]);

  // Update URL when status filter changes
  useEffect(() => {
    if (statusFilter) {
      setSearchParams({ status: statusFilter });
    } else {
      setSearchParams({});
    }
  }, [statusFilter, setSearchParams]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleStatusFilterChange = (event) => {
    setStatusFilter(event.target.value);
    setPage(0); // Reset to first page when filter changes
  };

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
  };

  // Filter vacancies based on search term (client-side filtering for simplicity)
  const filteredVacancies = vacancies.filter((vacancy) => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      (vacancy.Functie && vacancy.Functie.toLowerCase().includes(searchLower)) ||
      (vacancy.Klant && vacancy.Klant.toLowerCase().includes(searchLower)) ||
      (vacancy.Branche && vacancy.Branche.toLowerCase().includes(searchLower)) ||
      (vacancy.Regio && vacancy.Regio.toLowerCase().includes(searchLower))
    );
  });

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Vacancies
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          component={RouterLink}
          to="/vacancies/new"
        >
          Add Vacancy
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            label="Search"
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
          <FormControl variant="outlined" size="small" sx={{ minWidth: '200px' }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              onChange={handleStatusFilterChange}
              label="Status"
            >
              {statusOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
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
                  <TableCell>Status</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Client</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell>Posted</TableCell>
                  <TableCell>Match %</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredVacancies.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      No vacancies found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredVacancies.map((vacancy) => (
                    <TableRow key={vacancy.id}>
                      <TableCell>
                        <Chip
                          label={vacancy.Status}
                          color={getStatusColor(vacancy.Status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{vacancy.Functie}</TableCell>
                      <TableCell>{vacancy.Klant}</TableCell>
                      <TableCell>{vacancy.Regio}</TableCell>
                      <TableCell>{vacancy.Geplaatst}</TableCell>
                      <TableCell>
                        {vacancy.Top_Match ? `${vacancy.Top_Match}%` : '-'}
                      </TableCell>
                      <TableCell>
                        <Button
                          component={RouterLink}
                          to={`/vacancies/${vacancy.id}`}
                          size="small"
                          startIcon={<VisibilityIcon />}
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
              count={totalVacancies}
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

export default VacanciesList;