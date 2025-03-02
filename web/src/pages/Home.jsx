import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Tabs, 
  Tab, 
  Divider,
  Alert,
  Button
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import NewsList from '../components/NewsList';
import SearchBar from '../components/SearchBar';
import api from '../services/api';

/**
 * Home page component
 */
const Home = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [latestNews, setLatestNews] = useState([]);
  const [trendingNews, setTrendingNews] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [categories, setCategories] = useState([]);
  const [sources, setSources] = useState([]);

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

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
  const handleSearch = (searchParams) => {
    navigate('/search', { state: { searchParams } });
  };

  // Fetch latest news
  useEffect(() => {
    const fetchLatestNews = async () => {
      setLoading(true);
      try {
        const response = await api.getNews({ page, limit: 9 });
        setLatestNews(response.items);
        setTotalPages(response.pagination.pages);
        
        // In a real app, these would come from the API
        setCategories(['Politics', 'Business', 'Technology', 'Science', 'Health', 'Sports']);
        setSources(['CNN', 'BBC', 'Reuters', 'Associated Press', 'The Guardian']);
      } catch (err) {
        setError('Failed to load latest news. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchLatestNews();
  }, [page]);

  // Fetch trending news
  useEffect(() => {
    const fetchTrendingNews = async () => {
      try {
        const response = await api.getTrendingNews();
        setTrendingNews(response);
      } catch (err) {
        console.error(err);
        // We don't set the error state here to avoid blocking the whole page
        // if only trending news fails to load
      }
    };

    fetchTrendingNews();
  }, []);

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          News Aggregator
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          Your one-stop source for news from around the world
        </Typography>
        
        {/* Search bar */}
        <SearchBar 
          onSearch={handleSearch} 
          categories={categories}
          sources={sources}
        />
        
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
        
        {/* News tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange} 
            aria-label="news tabs"
            centered
          >
            <Tab label="Latest News" id="tab-0" />
            <Tab label="Trending" id="tab-1" />
          </Tabs>
        </Box>
        
        {/* Tab panels */}
        <div role="tabpanel" hidden={tabValue !== 0}>
          {tabValue === 0 && (
            <NewsList 
              news={latestNews}
              loading={loading}
              error={error}
              page={page}
              totalPages={totalPages}
              onPageChange={handlePageChange}
              onReadMore={handleReadMore}
              title="Latest News"
            />
          )}
        </div>
        <div role="tabpanel" hidden={tabValue !== 1}>
          {tabValue === 1 && (
            <NewsList 
              news={trendingNews}
              loading={loading}
              error={error}
              page={1}
              totalPages={1}
              onPageChange={() => {}}
              onReadMore={handleReadMore}
              title="Trending News"
            />
          )}
        </div>
      </Box>
    </Container>
  );
};

export default Home;