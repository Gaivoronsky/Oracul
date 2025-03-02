import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Tabs, 
  Tab, 
  Paper,
  Button,
  Divider,
  Alert,
  Snackbar,
  TextField,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Breadcrumbs,
  Link
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  PlayArrow as StartIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import Dashboard from '../components/Dashboard';
import api from '../services/api';

/**
 * Admin page component
 */
const Admin = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sources, setSources] = useState([]);
  const [stats, setStats] = useState(null);
  const [categoryDistribution, setCategoryDistribution] = useState([]);
  const [topEntities, setTopEntities] = useState([]);
  const [sourcePerformance, setSourcePerformance] = useState([]);
  const [statsPeriod, setStatsPeriod] = useState('day');
  const [openDialog, setOpenDialog] = useState(false);
  const [currentSource, setCurrentSource] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Handle stats period change
  const handlePeriodChange = (event) => {
    setStatsPeriod(event.target.value);
  };

  // Handle source dialog open
  const handleOpenSourceDialog = (source = null) => {
    setCurrentSource(source || { 
      name: '', 
      url: '', 
      type: 'rss',
      update_interval: 60,
      active: true
    });
    setOpenDialog(true);
  };

  // Handle source dialog close
  const handleCloseSourceDialog = () => {
    setOpenDialog(false);
  };

  // Handle source form submit
  const handleSourceSubmit = () => {
    // In a real app, this would save the source to the API
    console.log('Save source:', currentSource);
    
    // Show success message
    setSnackbar({
      open: true,
      message: currentSource.id ? 'Source updated successfully' : 'Source added successfully',
      severity: 'success'
    });
    
    handleCloseSourceDialog();
    
    // Refresh sources list
    fetchSources();
  };

  // Handle source delete
  const handleDeleteSource = (sourceId) => {
    // In a real app, this would delete the source via the API
    console.log('Delete source:', sourceId);
    
    // Show success message
    setSnackbar({
      open: true,
      message: 'Source deleted successfully',
      severity: 'success'
    });
    
    // Refresh sources list
    fetchSources();
  };

  // Handle trigger crawl
  const handleTriggerCrawl = (sourceId = null) => {
    // In a real app, this would trigger a crawl via the API
    console.log('Trigger crawl for source:', sourceId || 'all');
    
    // Show success message
    setSnackbar({
      open: true,
      message: sourceId ? 'Crawl triggered for selected source' : 'Crawl triggered for all sources',
      severity: 'success'
    });
  };

  // Handle snackbar close
  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Fetch sources
  const fetchSources = async () => {
    setLoading(true);
    try {
      const response = await api.getSources();
      setSources(response);
    } catch (err) {
      setError('Failed to load sources. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch analytics data
  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [statsData, categoryData, entitiesData, sourcesData] = await Promise.all([
        api.getStats(statsPeriod),
        api.getCategoryDistribution(statsPeriod),
        api.getTopEntities(10, statsPeriod),
        api.getSourcePerformance(10, statsPeriod)
      ]);
      
      setStats(statsData);
      setCategoryDistribution(categoryData);
      setTopEntities(entitiesData);
      setSourcePerformance(sourcesData);
    } catch (err) {
      setError('Failed to load analytics data. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch data based on active tab
  useEffect(() => {
    if (tabValue === 0) {
      fetchAnalytics();
    } else if (tabValue === 1) {
      fetchSources();
    }
  }, [tabValue, statsPeriod]);

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        {/* Breadcrumbs */}
        <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
          <Link color="inherit" href="/" onClick={(e) => {
            e.preventDefault();
            navigate('/');
          }}>
            Home
          </Link>
          <Typography color="text.primary">Admin</Typography>
        </Breadcrumbs>
        
        <Typography variant="h4" component="h1" gutterBottom>
          Admin Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          Manage sources and view analytics
        </Typography>
        
        {/* Error alert */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 3 }}
            action={
              <Button color="inherit" size="small" onClick={() => setError(null)}>
                Dismiss
              </Button>
            }
          >
            {error}
          </Alert>
        )}
        
        {/* Admin tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange} 
            aria-label="admin tabs"
          >
            <Tab label="Analytics" id="tab-0" />
            <Tab label="Sources" id="tab-1" />
          </Tabs>
        </Box>
        
        {/* Analytics tab */}
        <div role="tabpanel" hidden={tabValue !== 0}>
          {tabValue === 0 && (
            <Box>
              {/* Period selector */}
              <Paper sx={{ p: 2, mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="body1" sx={{ mr: 2 }}>
                    Time Period:
                  </Typography>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <Select
                      value={statsPeriod}
                      onChange={handlePeriodChange}
                      displayEmpty
                    >
                      <MenuItem value="day">Last 24 Hours</MenuItem>
                      <MenuItem value="week">Last Week</MenuItem>
                      <MenuItem value="month">Last Month</MenuItem>
                      <MenuItem value="year">Last Year</MenuItem>
                    </Select>
                  </FormControl>
                  <Button 
                    startIcon={<RefreshIcon />} 
                    onClick={fetchAnalytics}
                    sx={{ ml: 'auto' }}
                  >
                    Refresh
                  </Button>
                </Box>
              </Paper>
              
              {/* Dashboard component */}
              {stats && (
                <Dashboard 
                  stats={stats}
                  categoryDistribution={categoryDistribution}
                  topEntities={topEntities}
                  sourcePerformance={sourcePerformance}
                  loading={loading}
                />
              )}
            </Box>
          )}
        </div>
        
        {/* Sources tab */}
        <div role="tabpanel" hidden={tabValue !== 1}>
          {tabValue === 1 && (
            <Box>
              {/* Actions toolbar */}
              <Paper sx={{ p: 2, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6">
                    News Sources
                  </Typography>
                  <Box>
                    <Button 
                      variant="contained" 
                      startIcon={<AddIcon />}
                      onClick={() => handleOpenSourceDialog()}
                      sx={{ mr: 1 }}
                    >
                      Add Source
                    </Button>
                    <Button 
                      variant="outlined" 
                      startIcon={<StartIcon />}
                      onClick={() => handleTriggerCrawl()}
                    >
                      Trigger Crawl
                    </Button>
                  </Box>
                </Box>
              </Paper>
              
              {/* Sources list */}
              <Paper>
                <List>
                  {sources.length === 0 && !loading ? (
                    <ListItem>
                      <ListItemText primary="No sources found. Add a source to get started." />
                    </ListItem>
                  ) : (
                    sources.map((source, index) => (
                      <React.Fragment key={source.id || index}>
                        <ListItem>
                          <ListItemText 
                            primary={source.name} 
                            secondary={
                              <>
                                <Typography component="span" variant="body2" color="text.primary">
                                  {source.type.toUpperCase()}
                                </Typography>
                                {` — ${source.url}`}
                              </>
                            }
                          />
                          <ListItemSecondaryAction>
                            <IconButton 
                              edge="end" 
                              aria-label="start crawl"
                              onClick={() => handleTriggerCrawl(source.id)}
                              sx={{ mr: 1 }}
                            >
                              <StartIcon />
                            </IconButton>
                            <IconButton 
                              edge="end" 
                              aria-label="edit"
                              onClick={() => handleOpenSourceDialog(source)}
                              sx={{ mr: 1 }}
                            >
                              <EditIcon />
                            </IconButton>
                            <IconButton 
                              edge="end" 
                              aria-label="delete"
                              onClick={() => handleDeleteSource(source.id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                        {index < sources.length - 1 && <Divider />}
                      </React.Fragment>
                    ))
                  )}
                </List>
              </Paper>
            </Box>
          )}
        </div>
      </Box>
      
      {/* Source dialog */}
      <Dialog open={openDialog} onClose={handleCloseSourceDialog}>
        <DialogTitle>
          {currentSource?.id ? 'Edit Source' : 'Add New Source'}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Enter the details for the news source.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="name"
            label="Source Name"
            type="text"
            fullWidth
            variant="outlined"
            value={currentSource?.name || ''}
            onChange={(e) => setCurrentSource({ ...currentSource, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            id="url"
            label="URL"
            type="url"
            fullWidth
            variant="outlined"
            value={currentSource?.url || ''}
            onChange={(e) => setCurrentSource({ ...currentSource, url: e.target.value })}
            sx={{ mb: 2 }}
          />
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel id="type-label">Source Type</InputLabel>
                <Select
                  labelId="type-label"
                  id="type"
                  value={currentSource?.type || 'rss'}
                  label="Source Type"
                  onChange={(e) => setCurrentSource({ ...currentSource, type: e.target.value })}
                >
                  <MenuItem value="rss">RSS Feed</MenuItem>
                  <MenuItem value="html">HTML Scraping</MenuItem>
                  <MenuItem value="api">API</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <TextField
                margin="dense"
                id="update_interval"
                label="Update Interval (minutes)"
                type="number"
                fullWidth
                variant="outlined"
                value={currentSource?.update_interval || 60}
                onChange={(e) => setCurrentSource({ 
                  ...currentSource, 
                  update_interval: parseInt(e.target.value) || 60 
                })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseSourceDialog}>Cancel</Button>
          <Button onClick={handleSourceSubmit} variant="contained">
            {currentSource?.id ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
      >
        <Alert 
          onClose={handleSnackbarClose} 
          severity={snackbar.severity} 
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Admin;