import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { 
  Paper, 
  InputBase, 
  IconButton, 
  Divider, 
  Box,
  Button,
  Popover,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Typography,
  Chip
} from '@mui/material';
import { 
  Search as SearchIcon, 
  FilterList as FilterListIcon,
  Close as CloseIcon
} from '@mui/icons-material';

/**
 * SearchBar component provides a search input with advanced filtering options
 */
const SearchBar = ({ onSearch, categories = [], sources = [] }) => {
  // Search query state
  const [query, setQuery] = useState('');
  
  // Advanced filter states
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [selectedSources, setSelectedSources] = useState([]);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  
  // Handle opening the filter popover
  const handleFilterClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  
  // Handle closing the filter popover
  const handleFilterClose = () => {
    setAnchorEl(null);
  };
  
  // Check if the filter popover is open
  const open = Boolean(anchorEl);
  
  // Handle search submission
  const handleSubmit = (event) => {
    event.preventDefault();
    onSearch({
      query,
      categories: selectedCategories,
      sources: selectedSources,
      dateFrom,
      dateTo
    });
  };
  
  // Handle category selection
  const handleCategoryChange = (event) => {
    setSelectedCategories(event.target.value);
  };
  
  // Handle source selection
  const handleSourceChange = (event) => {
    setSelectedSources(event.target.value);
  };
  
  // Handle clearing all filters
  const handleClearFilters = () => {
    setSelectedCategories([]);
    setSelectedSources([]);
    setDateFrom('');
    setDateTo('');
  };
  
  // Count active filters
  const activeFilterCount = 
    selectedCategories.length + 
    selectedSources.length + 
    (dateFrom ? 1 : 0) + 
    (dateTo ? 1 : 0);

  return (
    <Box sx={{ width: '100%', mb: 4 }}>
      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{ p: '2px 4px', display: 'flex', alignItems: 'center', width: '100%' }}
        elevation={3}
      >
        <IconButton sx={{ p: '10px' }} aria-label="search">
          <SearchIcon />
        </IconButton>
        <InputBase
          sx={{ ml: 1, flex: 1 }}
          placeholder="Search news articles..."
          inputProps={{ 'aria-label': 'search news articles' }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Divider sx={{ height: 28, m: 0.5 }} orientation="vertical" />
        <IconButton 
          color={activeFilterCount > 0 ? "primary" : "default"}
          sx={{ p: '10px' }} 
          aria-label="filters"
          onClick={handleFilterClick}
        >
          <FilterListIcon />
          {activeFilterCount > 0 && (
            <Chip 
              label={activeFilterCount} 
              color="primary" 
              size="small" 
              sx={{ 
                position: 'absolute', 
                top: 0, 
                right: 0, 
                height: 16, 
                width: 16, 
                fontSize: '0.6rem' 
              }} 
            />
          )}
        </IconButton>
        <Button type="submit" sx={{ ml: 1 }}>Search</Button>
      </Paper>
      
      {/* Advanced filters popover */}
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleFilterClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <Box sx={{ p: 3, width: 300 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Advanced Filters</Typography>
            <IconButton size="small" onClick={handleFilterClose}>
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>
          
          {/* Category filter */}
          <FormControl fullWidth margin="normal">
            <InputLabel id="category-select-label">Categories</InputLabel>
            <Select
              labelId="category-select-label"
              id="category-select"
              multiple
              value={selectedCategories}
              onChange={handleCategoryChange}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {categories.map((category) => (
                <MenuItem key={category} value={category}>
                  {category}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          {/* Source filter */}
          <FormControl fullWidth margin="normal">
            <InputLabel id="source-select-label">Sources</InputLabel>
            <Select
              labelId="source-select-label"
              id="source-select"
              multiple
              value={selectedSources}
              onChange={handleSourceChange}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {sources.map((source) => (
                <MenuItem key={source} value={source}>
                  {source}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          {/* Date range filters */}
          <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
            <TextField
              label="From Date"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
            />
            <TextField
              label="To Date"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
            />
          </Box>
          
          {/* Action buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button 
              variant="outlined" 
              onClick={handleClearFilters}
              disabled={activeFilterCount === 0}
            >
              Clear All
            </Button>
            <Button 
              variant="contained" 
              onClick={() => {
                handleFilterClose();
                handleSubmit({ preventDefault: () => {} });
              }}
            >
              Apply Filters
            </Button>
          </Box>
        </Box>
      </Popover>
    </Box>
  );
};

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
  categories: PropTypes.arrayOf(PropTypes.string),
  sources: PropTypes.arrayOf(PropTypes.string)
};

SearchBar.defaultProps = {
  categories: [],
  sources: []
};

export default SearchBar;