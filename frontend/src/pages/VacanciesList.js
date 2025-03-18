import React, { useState, useEffect } from 'react';
import { Link as RouterLink, useSearchParams, useLocation } from 'react-router-dom';
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
  TableSortLabel,
  IconButton,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import RefreshIcon from '@mui/icons-material/Refresh';
import { getVacancies } from '../utils/api';

const VacanciesList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const initialStatus = searchParams.get('status') || '';
  
  // Check if we need to refresh due to navigation from another page
  const [notification, setNotification] = useState(null);

  const [vacancies, setVacancies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState(initialStatus);
  const [totalVacancies, setTotalVacancies] = useState(0);
  const [sortBy, setSortBy] = useState('Geplaatst');
  const [sortDirection, setSortDirection] = useState('desc');
  const [columnFilters, setColumnFilters] = useState({
    Status: '',
    Functie: '',
    Klant: '',
    Regio: ''
  });

  // Status options for filtering
  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'Nieuw', label: 'Nieuw' },
    { value: 'Open', label: 'Open' },
    { value: 'AI afgewezen', label: 'AI afgewezen' },
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

  // Define fetchVacancies as a memoized function that can be called manually
  const fetchVacancies = React.useCallback(async () => {
    try {
      setLoading(true);
      // Prepare query parameters
      const params = {
        skip: page * rowsPerPage,
        limit: rowsPerPage
      };
      
      if (statusFilter) {
        params.status = statusFilter;
      }

      console.log('Fetching vacancies with params:', params);
      const response = await getVacancies(params);
      
      console.log(`Received ${response.data.items.length} vacancies with total ${response.data.total}`);
      setVacancies(response.data.items);
      setTotalVacancies(response.data.total);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching vacancies:', err);
      setError('Failed to load vacancies. Please try again later.');
      setLoading(false);
    }
  }, [page, rowsPerPage, statusFilter]);

  // Use effect to fetch vacancies on mount and when dependencies change
  useEffect(() => {
    fetchVacancies();
  }, [fetchVacancies]);
  
  // Check if we came from a delete operation and need to refresh
  useEffect(() => {
    if (location.state?.refreshNeeded) {
      // Clear the location state so we don't trigger multiple refreshes
      window.history.replaceState({}, document.title);
      
      // Show notification
      if (location.state.action === 'deleted') {
        setNotification({ 
          type: 'success', 
          message: 'Vacancy was successfully deleted' 
        });
        
        // Clear notification after 3 seconds
        setTimeout(() => {
          setNotification(null);
        }, 3000);
      }
      
      // Refresh the data
      fetchVacancies();
    }
  }, [location, fetchVacancies]);

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
  
  const handleColumnFilterChange = (column, value) => {
    setColumnFilters(prev => ({
      ...prev,
      [column]: value
    }));
    setPage(0); // Reset to first page when filter changes
  };
  
  const handleSortRequest = (property) => {
    const isAsc = sortBy === property && sortDirection === 'asc';
    setSortDirection(isAsc ? 'desc' : 'asc');
    setSortBy(property);
  };

  // Filter vacancies based on search term and column filters (client-side filtering for simplicity)
  const filteredVacancies = vacancies
    .filter((vacancy) => {
      // Global search filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch = (
          (vacancy.Functie && vacancy.Functie.toLowerCase().includes(searchLower)) ||
          (vacancy.Klant && vacancy.Klant.toLowerCase().includes(searchLower)) ||
          (vacancy.Branche && vacancy.Branche.toLowerCase().includes(searchLower)) ||
          (vacancy.Regio && vacancy.Regio.toLowerCase().includes(searchLower))
        );
        if (!matchesSearch) return false;
      }
      
      // Column-specific filters
      if (columnFilters.Status && vacancy.Status && 
          !vacancy.Status.toLowerCase().includes(columnFilters.Status.toLowerCase())) {
        return false;
      }
      
      if (columnFilters.Functie && vacancy.Functie && 
          !vacancy.Functie.toLowerCase().includes(columnFilters.Functie.toLowerCase())) {
        return false;
      }
      
      if (columnFilters.Klant && vacancy.Klant && 
          !vacancy.Klant.toLowerCase().includes(columnFilters.Klant.toLowerCase())) {
        return false;
      }
      
      if (columnFilters.Regio && vacancy.Regio && 
          !vacancy.Regio.toLowerCase().includes(columnFilters.Regio.toLowerCase())) {
        return false;
      }
      
      return true;
    })
    // Apply client-side sorting
    .sort((a, b) => {
      // Helper function to safely compare values that might be undefined
      const compareValues = (valA, valB) => {
        // Handle undefined/null values
        if (valA === undefined || valA === null) return sortDirection === 'asc' ? -1 : 1;
        if (valB === undefined || valB === null) return sortDirection === 'asc' ? 1 : -1;
        
        // Compare strings
        if (typeof valA === 'string' && typeof valB === 'string') {
          return sortDirection === 'asc' 
            ? valA.localeCompare(valB)
            : valB.localeCompare(valA);
        }
        
        // Compare numbers (including percentages like "85%")
        if (typeof valA === 'string' && valA.includes('%')) {
          const numA = parseFloat(valA);
          const numB = parseFloat(valB);
          return sortDirection === 'asc' ? numA - numB : numB - numA;
        }
        
        // Default comparison
        return sortDirection === 'asc'
          ? valA > valB ? 1 : -1
          : valB > valA ? 1 : -1;
      };
      
      // Choose which property to sort by
      if (sortBy === 'Functie') {
        return compareValues(a.Functie, b.Functie);
      } else if (sortBy === 'Klant') {
        return compareValues(a.Klant, b.Klant);
      } else if (sortBy === 'Regio') {
        return compareValues(a.Regio, b.Regio);
      } else if (sortBy === 'Geplaatst') {
        return compareValues(a.Geplaatst, b.Geplaatst);
      } else if (sortBy === 'Status') {
        return compareValues(a.Status, b.Status);
      } else if (sortBy === 'Match') {
        return compareValues(a.Top_Match, b.Top_Match);
      }
      
      // Default to sorting by Geplaatst date
      return compareValues(a.Geplaatst, b.Geplaatst);
    });

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="h4" component="h1">
            Vacancies
          </Typography>
          <IconButton 
            color="primary" 
            onClick={fetchVacancies} 
            disabled={loading}
            aria-label="refresh vacancies"
            sx={{ ml: 2 }}
          >
            <RefreshIcon />
          </IconButton>
        </Box>
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
      
      {notification && (
        <Alert severity={notification.type} sx={{ mb: 3 }}>
          {notification.message}
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
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'Status'}
                      direction={sortBy === 'Status' ? sortDirection : 'asc'}
                      onClick={() => handleSortRequest('Status')}
                    >
                      Status
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'Functie'}
                      direction={sortBy === 'Functie' ? sortDirection : 'asc'}
                      onClick={() => handleSortRequest('Functie')}
                    >
                      Title
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'Klant'}
                      direction={sortBy === 'Klant' ? sortDirection : 'asc'}
                      onClick={() => handleSortRequest('Klant')}
                    >
                      Client
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'Regio'}
                      direction={sortBy === 'Regio' ? sortDirection : 'asc'}
                      onClick={() => handleSortRequest('Regio')}
                    >
                      Location
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'Geplaatst'}
                      direction={sortBy === 'Geplaatst' ? sortDirection : 'asc'}
                      onClick={() => handleSortRequest('Geplaatst')}
                    >
                      Geplaatst
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'Match'}
                      direction={sortBy === 'Match' ? sortDirection : 'asc'}
                      onClick={() => handleSortRequest('Match')}
                    >
                      Match %
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
                {/* Filter inputs row */}
                <TableRow>
                  <TableCell>
                    <TextField
                      size="small"
                      placeholder="Filter status..."
                      value={columnFilters.Status}
                      onChange={(e) => handleColumnFilterChange('Status', e.target.value)}
                      sx={{ width: '100%' }}
                      inputProps={{ style: { fontSize: '0.875rem' } }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      placeholder="Filter title..."
                      value={columnFilters.Functie}
                      onChange={(e) => handleColumnFilterChange('Functie', e.target.value)}
                      sx={{ width: '100%' }}
                      inputProps={{ style: { fontSize: '0.875rem' } }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      placeholder="Filter client..."
                      value={columnFilters.Klant}
                      onChange={(e) => handleColumnFilterChange('Klant', e.target.value)}
                      sx={{ width: '100%' }}
                      inputProps={{ style: { fontSize: '0.875rem' } }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      placeholder="Filter location..."
                      value={columnFilters.Regio}
                      onChange={(e) => handleColumnFilterChange('Regio', e.target.value)}
                      sx={{ width: '100%' }}
                      inputProps={{ style: { fontSize: '0.875rem' } }}
                    />
                  </TableCell>
                  <TableCell></TableCell>
                  <TableCell></TableCell>
                  <TableCell></TableCell>
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
              rowsPerPageOptions={[25, 50, 100]}
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