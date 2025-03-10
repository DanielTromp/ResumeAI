import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  TextField,
  Grid,
  Card,
  CardContent,
  CardActions,
  CardHeader,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  CircularProgress,
  Alert,
  Snackbar,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tabs,
  Tab,
  Divider,
  useTheme,
  TablePagination
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import BugReportIcon from '@mui/icons-material/BugReport';
import BuildIcon from '@mui/icons-material/Build';
import DoneIcon from '@mui/icons-material/Done';
import AssignmentIcon from '@mui/icons-material/Assignment';
import PriorityHighIcon from '@mui/icons-material/PriorityHigh';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import RefreshIcon from '@mui/icons-material/Refresh';
import axios from 'axios';

// Task type icons
const TYPE_ICONS = {
  bug: <BugReportIcon color="error" />,
  feature: <BuildIcon color="primary" />,
  improvement: <AssignmentIcon color="success" />,
  task: <AssignmentIcon />
};

// Priority styles with colors
const PRIORITY_STYLES = {
  critical: { bgcolor: '#ffebee', color: '#d32f2f', icon: <PriorityHighIcon sx={{ color: '#d32f2f' }} /> },
  high: { bgcolor: '#fff8e1', color: '#f57c00', icon: <PriorityHighIcon sx={{ color: '#f57c00' }} /> },
  medium: { bgcolor: '#e3f2fd', color: '#1976d2', icon: <PriorityHighIcon sx={{ color: '#1976d2' }} /> },
  low: { bgcolor: '#e8f5e9', color: '#388e3c', icon: <PriorityHighIcon sx={{ color: '#388e3c' }} /> }
};

// Status styles and buttons
const STATUS_STYLES = {
  todo: { bgcolor: '#f5f5f5', color: '#424242', label: 'To Do' },
  in_progress: { bgcolor: '#e3f2fd', color: '#1976d2', label: 'In Progress' },
  done: { bgcolor: '#e8f5e9', color: '#388e3c', label: 'Done' }
};

const TaskBoard = () => {
  const theme = useTheme();
  const [tasks, setTasks] = useState([]);
  const [filteredTasks, setFilteredTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalTasks, setTotalTasks] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'task',
    priority: 'medium',
    status: 'todo',
    due_date: null
  });
  const [editingTaskId, setEditingTaskId] = useState(null);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [tabValue, setTabValue] = useState(0);

  // Fetch tasks
  useEffect(() => {
    fetchTasks();
  }, [page, rowsPerPage, filterStatus, filterType, filterPriority]);

  // Apply local filtering to tasks
  useEffect(() => {
    if (!tasks) return;
    
    let filtered = [...tasks];
    
    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(task => 
        task.title.toLowerCase().includes(search) || 
        task.description.toLowerCase().includes(search)
      );
    }
    
    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(task => task.status === filterStatus);
    }
    
    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.filter(task => task.type === filterType);
    }
    
    // Apply priority filter
    if (filterPriority !== 'all') {
      filtered = filtered.filter(task => task.priority === filterPriority);
    }
    
    setFilteredTasks(filtered);
    setTotalTasks(filtered.length);
  }, [tasks, searchTerm, filterStatus, filterType, filterPriority]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      // Build query parameters
      const params = {
        skip: page * rowsPerPage,
        limit: rowsPerPage,
        // Add cache-busting timestamp
        _: new Date().getTime()
      };
      
      const response = await axios.get('/api/tasks', { 
        params,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      console.log('Tasks fetched:', response.data);
      setTasks(response.data.items);
      setTotalTasks(response.data.total);
      setError(null);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setError('Failed to load tasks. Please try again later.');
    } finally {
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

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleAddTask = () => {
    setFormData({
      title: '',
      description: '',
      type: 'task',
      priority: 'medium',
      status: 'todo',
      due_date: null
    });
    setEditingTaskId(null);
    setDialogOpen(true);
  };

  const handleEditTask = (task) => {
    setFormData({
      title: task.title,
      description: task.description,
      type: task.type,
      priority: task.priority,
      status: task.status,
      due_date: task.due_date
    });
    setEditingTaskId(task.id);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
  };

  const handleDeleteClick = (task) => {
    setSelectedTask(task);
    setConfirmDeleteOpen(true);
  };

  const handleCancelDelete = () => {
    setConfirmDeleteOpen(false);
    setSelectedTask(null);
  };

  const handleConfirmDelete = async () => {
    if (!selectedTask) return;
    
    try {
      await axios.delete(`/api/tasks/${selectedTask.id}`);
      setConfirmDeleteOpen(false);
      setSelectedTask(null);
      showNotification('Task deleted successfully', 'success');
      fetchTasks();
    } catch (err) {
      console.error('Error deleting task:', err);
      showNotification('Failed to delete task', 'error');
      setConfirmDeleteOpen(false);
    }
  };

  const handleSubmitTask = async (e) => {
    e.preventDefault();
    
    try {
      if (editingTaskId) {
        // Update existing task
        await axios.put(`/api/tasks/${editingTaskId}`, formData);
        showNotification('Task updated successfully', 'success');
      } else {
        // Create new task
        await axios.post('/api/tasks', formData);
        showNotification('Task created successfully', 'success');
      }
      
      setDialogOpen(false);
      fetchTasks();
    } catch (err) {
      console.error('Error saving task:', err);
      showNotification('Failed to save task', 'error');
    }
  };

  const handleChangeStatus = async (taskId, newStatus) => {
    try {
      await axios.put(`/api/tasks/${taskId}`, { status: newStatus });
      showNotification(`Task marked as ${STATUS_STYLES[newStatus].label}`, 'success');
      fetchTasks();
    } catch (err) {
      console.error('Error updating task status:', err);
      showNotification('Failed to update task status', 'error');
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

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    switch (newValue) {
      case 0: // All
        setFilterStatus('all');
        break;
      case 1: // To Do
        setFilterStatus('todo');
        break;
      case 2: // In Progress
        setFilterStatus('in_progress');
        break;
      case 3: // Done
        setFilterStatus('done');
        break;
      default:
        setFilterStatus('all');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString();
  };

  const renderTaskStatusControls = (task) => {
    switch (task.status) {
      case 'todo':
        return (
          <Button
            startIcon={<PlayArrowIcon />}
            size="small"
            onClick={() => handleChangeStatus(task.id, 'in_progress')}
            color="primary"
          >
            Start
          </Button>
        );
      case 'in_progress':
        return (
          <Button
            startIcon={<DoneIcon />}
            size="small"
            onClick={() => handleChangeStatus(task.id, 'done')}
            color="success"
          >
            Complete
          </Button>
        );
      case 'done':
        return (
          <Button
            startIcon={<CheckCircleIcon />}
            size="small"
            disabled
            color="success"
          >
            Completed
          </Button>
        );
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Task Board
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleAddTask}
        >
          Add Task
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ mb: 2 }}>
          <TextField
            label="Search tasks"
            variant="outlined"
            fullWidth
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mb: 2 }}
          />
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={filterType}
                  label="Type"
                  onChange={(e) => setFilterType(e.target.value)}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="bug">Bug</MenuItem>
                  <MenuItem value="feature">Feature</MenuItem>
                  <MenuItem value="improvement">Improvement</MenuItem>
                  <MenuItem value="task">Task</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={filterPriority}
                  label="Priority"
                  onChange={(e) => setFilterPriority(e.target.value)}
                >
                  <MenuItem value="all">All Priorities</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Button 
                variant="outlined" 
                onClick={() => {
                  setSearchTerm('');
                  setFilterType('all');
                  setFilterPriority('all');
                  setFilterStatus('all');
                  setTabValue(0);
                }}
                fullWidth
                sx={{ height: '56px' }}
              >
                Clear Filters
              </Button>
            </Grid>
          </Grid>
        </Box>

        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label="All" />
          <Tab label="To Do" />
          <Tab label="In Progress" />
          <Tab label="Done" />
        </Tabs>
      </Paper>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        filteredTasks.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              No tasks found
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Try adjusting your filters or add a new task
            </Typography>
          </Paper>
        ) : (
          <>
            <Grid container spacing={3}>
              {filteredTasks
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map(task => (
                <Grid item xs={12} key={task.id}>
                  <Card 
                    sx={{ 
                      borderLeft: `5px solid ${PRIORITY_STYLES[task.priority].color}`,
                      bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'background.paper'
                    }}
                  >
                    <CardHeader
                      title={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {TYPE_ICONS[task.type]}
                          <Typography variant="h6">
                            <span style={{ fontWeight: 'bold' }}>[#{task.id}]</span> {task.title}
                          </Typography>
                        </Box>
                      }
                      action={
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <IconButton size="small" onClick={() => handleEditTask(task)}>
                            <EditIcon />
                          </IconButton>
                          <IconButton size="small" color="error" onClick={() => handleDeleteClick(task)}>
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                      }
                    />
                    <CardContent>
                      <Typography variant="body1" sx={{ whiteSpace: 'pre-line', mb: 2 }}>
                        {task.description}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                        <Chip 
                          label={`Priority: ${task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}`}
                          icon={PRIORITY_STYLES[task.priority].icon}
                          size="small"
                          sx={{ 
                            bgcolor: PRIORITY_STYLES[task.priority].bgcolor,
                            color: PRIORITY_STYLES[task.priority].color
                          }}
                        />
                        <Chip 
                          label={`Status: ${STATUS_STYLES[task.status].label}`}
                          size="small"
                          sx={{ 
                            bgcolor: STATUS_STYLES[task.status].bgcolor,
                            color: STATUS_STYLES[task.status].color
                          }}
                        />
                        <Chip 
                          label={`Type: ${task.type.charAt(0).toUpperCase() + task.type.slice(1)}`}
                          icon={TYPE_ICONS[task.type]}
                          size="small"
                        />
                        {task.due_date && (
                          <Chip 
                            label={`Due: ${formatDate(task.due_date)}`}
                            size="small"
                          />
                        )}
                      </Box>
                      
                      <Box sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>
                        Created: {formatDate(task.created_at)} • Last updated: {formatDate(task.updated_at)}
                      </Box>
                    </CardContent>
                    <Divider />
                    <CardActions sx={{ justifyContent: 'flex-end' }}>
                      {renderTaskStatusControls(task)}
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
            
            <Box sx={{ mt: 2 }}>
              <TablePagination
                component="div"
                count={totalTasks}
                page={page}
                onPageChange={handleChangePage}
                rowsPerPage={rowsPerPage}
                onRowsPerPageChange={handleChangeRowsPerPage}
                rowsPerPageOptions={[5, 10, 25, 50]}
              />
            </Box>
          </>
        )
      )}

      {/* Task Form Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <form onSubmit={handleSubmitTask}>
          <DialogTitle>
            {editingTaskId ? 'Edit Task' : 'Add New Task'}
          </DialogTitle>
          <DialogContent>
            <TextField
              margin="normal"
              label="Title"
              name="title"
              value={formData.title}
              onChange={handleFormChange}
              fullWidth
              required
              autoFocus
            />
            <TextField
              margin="normal"
              label="Description"
              name="description"
              value={formData.description}
              onChange={handleFormChange}
              fullWidth
              required
              multiline
              rows={4}
            />
            
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Type</InputLabel>
                  <Select
                    name="type"
                    value={formData.type}
                    onChange={handleFormChange}
                    label="Type"
                  >
                    <MenuItem value="bug">Bug</MenuItem>
                    <MenuItem value="feature">Feature</MenuItem>
                    <MenuItem value="improvement">Improvement</MenuItem>
                    <MenuItem value="task">Task</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Priority</InputLabel>
                  <Select
                    name="priority"
                    value={formData.priority}
                    onChange={handleFormChange}
                    label="Priority"
                  >
                    <MenuItem value="critical">Critical</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Status</InputLabel>
                  <Select
                    name="status"
                    value={formData.status}
                    onChange={handleFormChange}
                    label="Status"
                  >
                    <MenuItem value="todo">To Do</MenuItem>
                    <MenuItem value="in_progress">In Progress</MenuItem>
                    <MenuItem value="done">Done</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button type="submit" variant="contained" color="primary">
              Save
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={confirmDeleteOpen} onClose={handleCancelDelete}>
        <DialogTitle>Delete Task</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the task "{selectedTask?.title}"?
            This action cannot be undone.
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

      {/* Notifications */}
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

export default TaskBoard;