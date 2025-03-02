import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Breadcrumbs,
  Link,
  Chip,
  Paper,
  Divider,
  Alert,
  Button
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import NewsList from '../components/NewsList';
import SearchBar from '../components/SearchBar';
import api from '../services/api';

/**
 * Search page component
 */
const Search = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const initialSearchParams = location.state?.searchParams || { query: '' };
  
  const [searchParams, setSearchParams] = useState(initialSearchParams);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [categories, setCategories] = useState([]);
  const [sources, setSources] = useState([]);

  // Handle page change
  const handlePageChange = (newPage) => {
    setPage(newPage);
  };

  // Handle read more click
  const handleReadMore = (newsId) => {
    // In a real app, this would navigate to a news detail page
    console.log(`Navigate to news detail for ID: ${newsId}`);
  };

  // Handle search
  const handleSearch = (newSearchParams) => {
    setSearchParams(newSearchParams);
    setPage(1); // Reset to first page on new search
  };

  // Handle clear search
  const handleClearSearch = () => {
    navigate('/');
  };

  // Fetch search results
  useEffect(() => {
    const fetchSearchResults = async () => {
      // Skip if no query
      if (!searchParams.query) {
        setSearchResults([]);
        setTotalPages(1);
        return;
      }
      
      setLoading(true);
      try {
        const response = await api.searchNews({
          ...searchParams,
          page,
          limit: 9
        });
        setSearchResults(response.items);
        setTotalPages(response.pagination.pages);
        
        // In a real app, these would come from the API
        setCategories(['Politics', 'Business', 'Technology', 'Science', 'Health', 'Sports']);
        setSources(['CNN', 'BBC', 'Reuters', 'Associated Press', 'The Guardian']);
      } catch (err) {
        setError('Failed to load search results. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchSearchResults();
  }, [searchParams, page]);

  // Generate active filters display
  const activeFilters = [];
  if (searchParams.categories && searchParams.categories.length > 0) {
    activeFilters.push(...searchParams.categories.map(cat => ({
      type: 'Category',
      value: cat
    })));
  }
  if (searchParams.sources && searchParams.sources.length > 0) {
    activeFilters.push(...searchParams.sources.map(src => ({
      type: 'Source',
      value: src
    })));
  }
  if (searchParams.dateFrom) {
    activeFilters.push({
      type: 'From',
      value: new Date(searchParams.dateFrom).toLocaleDateString()
    });
  }
  if (searchParams.dateTo) {
    activeFilters.push({
      type: 'To',
      value: new Date(searchParams.dateTo).toLocaleDateString()
    });
  }

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
          <Typography color="text.primary">Search</Typography>
        </Breadcrumbs>
        
        <Typography variant="h4" component="h1" gutterBottom>
          Search Results
        </Typography>
        
        {/* Search bar */}
        <SearchBar 
          onSearch={handleSearch} 
          categories={categories}
          sources={sources}
        />
        
        {/* Active filters */}
        {activeFilters.length > 0 && (
          <Paper sx={{ p: 2, mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Active filters:
              </Typography>
              {activeFilters.map((filter, index) => (
                <Chip 
                  key={index}
                  label={`${filter.type}: ${filter.value}`}
                  size="small"
                  onDelete={() => {
                    // In a real app, this would remove the specific filter
                    console.log(`Remove filter: ${filter.type} - ${filter.value}`);
                  }}
                />
              ))}
              <Button 
                size="small" 
                variant="outlined" 
                onClick={handleClearSearch}
                sx={{ ml: 'auto' }}
              >
                Clear All
              </Button>
            </Box>
          </Paper>
        )}
        
        {/* Search query display */}
        <Typography variant="h6" gutterBottom>
          {searchParams.query ? `Results for "${searchParams.query}"` : 'Enter a search query'}
        </Typography>
        <Divider sx={{ mb: 3 }} />
        
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
        
        {/* No query message */}
        {!searchParams.query && !loading && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Please enter a search query to find news articles.
          </Alert>
        )}
        
        {/* Search results */}
        {searchParams.query && (
          <NewsList 
            news={searchResults}
            loading={loading}
            error={error}
            page={page}
            totalPages={totalPages}
            onPageChange={handlePageChange}
            onReadMore={handleReadMore}
            title=""
          />
        )}
      </Box>
    </Container>
  );
};

export default Search;