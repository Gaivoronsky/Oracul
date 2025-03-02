import React from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  Typography, 
  Pagination, 
  CircularProgress, 
  Alert,
  Grid,
  Container,
  Divider
} from '@mui/material';
import NewsItem from './NewsItem';

/**
 * NewsList component displays a list of news articles with pagination
 */
const NewsList = ({ 
  news, 
  loading, 
  error, 
  page, 
  totalPages, 
  onPageChange, 
  onReadMore,
  title = 'Latest News'
}) => {
  // Handle page change
  const handlePageChange = (event, value) => {
    onPageChange(value);
  };

  return (
    <Container>
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          {title}
        </Typography>
        <Divider sx={{ mb: 3 }} />

        {/* Loading state */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {/* Error state */}
        {error && (
          <Alert severity="error" sx={{ my: 2 }}>
            {error}
          </Alert>
        )}

        {/* News list */}
        {!loading && !error && news.length === 0 && (
          <Alert severity="info" sx={{ my: 2 }}>
            No news articles found.
          </Alert>
        )}

        {!loading && !error && news.length > 0 && (
          <Grid container spacing={3}>
            {news.map((item) => (
              <Grid item xs={12} md={6} lg={4} key={item.id}>
                <NewsItem news={item} onReadMore={onReadMore} />
              </Grid>
            ))}
          </Grid>
        )}

        {/* Pagination */}
        {!loading && !error && totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Pagination 
              count={totalPages} 
              page={page} 
              onChange={handlePageChange} 
              color="primary" 
              showFirstButton 
              showLastButton
            />
          </Box>
        )}
      </Box>
    </Container>
  );
};

NewsList.propTypes = {
  news: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      summary: PropTypes.string.isRequired,
      published_at: PropTypes.string.isRequired,
      source: PropTypes.string.isRequired,
      category: PropTypes.string,
      image_url: PropTypes.string
    })
  ).isRequired,
  loading: PropTypes.bool,
  error: PropTypes.string,
  page: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  onPageChange: PropTypes.func.isRequired,
  onReadMore: PropTypes.func.isRequired,
  title: PropTypes.string
};

NewsList.defaultProps = {
  loading: false,
  error: null,
  title: 'Latest News'
};

export default NewsList;