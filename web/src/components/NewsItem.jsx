import React from 'react';
import PropTypes from 'prop-types';
import { 
  Card, 
  CardContent, 
  CardMedia, 
  Typography, 
  CardActionArea, 
  CardActions,
  Button,
  Chip,
  Box
} from '@mui/material';
import { formatDistanceToNow } from 'date-fns';

/**
 * NewsItem component displays a single news article in a card format
 */
const NewsItem = ({ news, onReadMore }) => {
  const { 
    id, 
    title, 
    summary, 
    published_at, 
    source, 
    category,
    image_url
  } = news;

  // Format the published date as a relative time (e.g., "2 hours ago")
  const formattedDate = formatDistanceToNow(new Date(published_at), { addSuffix: true });

  return (
    <Card sx={{ maxWidth: '100%', mb: 2 }}>
      {image_url && (
        <CardMedia
          component="img"
          height="140"
          image={image_url}
          alt={title}
        />
      )}
      <CardContent>
        <Typography gutterBottom variant="h5" component="div">
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {summary}
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="caption" color="text.secondary">
            {source} • {formattedDate}
          </Typography>
          {category && (
            <Chip 
              label={category} 
              size="small" 
              color="primary" 
              variant="outlined" 
            />
          )}
        </Box>
      </CardContent>
      <CardActions>
        <Button 
          size="small" 
          color="primary" 
          onClick={() => onReadMore(id)}
        >
          Read More
        </Button>
        <Button size="small" color="secondary">
          Share
        </Button>
      </CardActions>
    </Card>
  );
};

NewsItem.propTypes = {
  news: PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    summary: PropTypes.string.isRequired,
    published_at: PropTypes.string.isRequired,
    source: PropTypes.string.isRequired,
    category: PropTypes.string,
    image_url: PropTypes.string
  }).isRequired,
  onReadMore: PropTypes.func.isRequired
};

export default NewsItem;