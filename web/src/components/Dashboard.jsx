import React from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  Paper, 
  Typography, 
  Grid, 
  Card, 
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  LinearProgress,
  Chip
} from '@mui/material';
import {
  Article as ArticleIcon,
  Source as SourceIcon,
  Category as CategoryIcon,
  TrendingUp as TrendingUpIcon,
  Language as LanguageIcon
} from '@mui/icons-material';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

/**
 * Dashboard component displays analytics and statistics
 */
const Dashboard = ({ 
  stats, 
  categoryDistribution, 
  topEntities, 
  sourcePerformance,
  loading 
}) => {
  // Colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#8DD1E1', '#A4DE6C', '#D0ED57'];
  
  // Format data for pie chart
  const pieData = categoryDistribution.map(item => ({
    name: item.category,
    value: item.count
  }));
  
  // Format data for bar chart
  const barData = sourcePerformance.map(item => ({
    name: item.source,
    articles: item.articles_count,
    sentiment: Math.round(item.average_sentiment * 100)
  }));

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom component="div">
        Analytics Dashboard
      </Typography>
      <Divider sx={{ mb: 3 }} />
      
      {/* Key metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <ArticleIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
              <Box>
                <Typography variant="h4" component="div">
                  {stats.metrics.total_articles}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Articles
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <SourceIcon color="secondary" sx={{ fontSize: 40, mr: 2 }} />
              <Box>
                <Typography variant="h4" component="div">
                  {stats.metrics.total_sources}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Sources
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <CategoryIcon color="success" sx={{ fontSize: 40, mr: 2 }} />
              <Box>
                <Typography variant="h4" component="div">
                  {stats.metrics.total_categories}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Categories
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <TrendingUpIcon color="error" sx={{ fontSize: 40, mr: 2 }} />
              <Box>
                <Typography variant="h4" component="div">
                  {Math.round(stats.metrics.average_sentiment * 100)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg. Sentiment
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
      
      {/* Charts and lists */}
      <Grid container spacing={3}>
        {/* Category distribution chart */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Category Distribution
            </Typography>
            <ResponsiveContainer width="100%" height="90%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        
        {/* Source performance chart */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Source Performance
            </Typography>
            <ResponsiveContainer width="100%" height="90%">
              <BarChart
                data={barData}
                margin={{
                  top: 5,
                  right: 30,
                  left: 20,
                  bottom: 5,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="articles" fill="#8884d8" name="Articles" />
                <Bar dataKey="sentiment" fill="#82ca9d" name="Sentiment %" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        
        {/* Top entities list */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top Entities
            </Typography>
            <List>
              {topEntities.map((entity, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemIcon>
                      <LanguageIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary={entity.entity} 
                      secondary={`Mentions: ${entity.count}`} 
                    />
                    <Chip 
                      label={entity.type} 
                      size="small" 
                      color={
                        entity.type === 'person' ? 'primary' :
                        entity.type === 'organization' ? 'secondary' :
                        entity.type === 'location' ? 'success' :
                        'default'
                      } 
                    />
                    <Box sx={{ ml: 2, width: 100 }}>
                      <Typography variant="body2" color="text.secondary" align="center">
                        Sentiment
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={entity.sentiment * 100} 
                        color={
                          entity.sentiment > 0.6 ? 'success' :
                          entity.sentiment > 0.4 ? 'primary' :
                          'error'
                        }
                        sx={{ height: 8, borderRadius: 5 }}
                      />
                    </Box>
                  </ListItem>
                  {index < topEntities.length - 1 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))}
            </List>
          </Paper>
        </Grid>
        
        {/* Time series data */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Activity Timeline
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Period: {stats.period} ({new Date(stats.start_time).toLocaleDateString()} - {new Date(stats.end_time).toLocaleDateString()})
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={stats.time_series}
                margin={{
                  top: 5,
                  right: 30,
                  left: 20,
                  bottom: 5,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(timestamp) => new Date(timestamp).toLocaleDateString()}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(timestamp) => new Date(timestamp).toLocaleString()}
                />
                <Bar dataKey="articles_count" name="Articles" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

Dashboard.propTypes = {
  stats: PropTypes.shape({
    period: PropTypes.string.isRequired,
    start_time: PropTypes.string.isRequired,
    end_time: PropTypes.string.isRequired,
    interval: PropTypes.string.isRequired,
    metrics: PropTypes.shape({
      total_articles: PropTypes.number.isRequired,
      total_sources: PropTypes.number.isRequired,
      total_categories: PropTypes.number.isRequired,
      average_sentiment: PropTypes.number.isRequired
    }).isRequired,
    time_series: PropTypes.arrayOf(
      PropTypes.shape({
        timestamp: PropTypes.string.isRequired,
        articles_count: PropTypes.number.isRequired,
        sources_count: PropTypes.number.isRequired,
        average_sentiment: PropTypes.number.isRequired
      })
    ).isRequired
  }).isRequired,
  categoryDistribution: PropTypes.arrayOf(
    PropTypes.shape({
      category: PropTypes.string.isRequired,
      count: PropTypes.number.isRequired,
      percentage: PropTypes.number.isRequired
    })
  ).isRequired,
  topEntities: PropTypes.arrayOf(
    PropTypes.shape({
      entity: PropTypes.string.isRequired,
      type: PropTypes.string.isRequired,
      count: PropTypes.number.isRequired,
      sentiment: PropTypes.number.isRequired
    })
  ).isRequired,
  sourcePerformance: PropTypes.arrayOf(
    PropTypes.shape({
      source: PropTypes.string.isRequired,
      articles_count: PropTypes.number.isRequired,
      average_sentiment: PropTypes.number.isRequired,
      categories: PropTypes.arrayOf(PropTypes.string).isRequired,
      reliability_score: PropTypes.number.isRequired
    })
  ).isRequired,
  loading: PropTypes.bool
};

Dashboard.defaultProps = {
  loading: false
};

export default Dashboard;