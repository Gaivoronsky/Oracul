/**
 * API service client
 * Provides methods for interacting with the backend API
 */

// Base API URL - would be configured based on environment in a real app
const API_BASE_URL = 'http://localhost:8000/api';

// Mock data for development
const mockData = {
  // Mock news data
  news: Array(100).fill().map((_, i) => ({
    id: `news-${i}`,
    title: `News Article ${i}`,
    summary: `This is a summary of news article ${i}. It contains a brief overview of the content.`,
    content: `This is the full content of news article ${i}. It contains much more detailed information about the topic.`,
    published_at: new Date(Date.now() - Math.floor(Math.random() * 7 * 24 * 60 * 60 * 1000)).toISOString(),
    source: ['CNN', 'BBC', 'Reuters', 'Associated Press', 'The Guardian'][i % 5],
    url: `https://example.com/news/${i}`,
    category: ['Politics', 'Business', 'Technology', 'Science', 'Health', 'Sports'][i % 6],
    author: `Author ${i % 10}`,
    image_url: `https://example.com/images/${i}.jpg`,
    tags: ['news', 'example', 'mock']
  })),
  
  // Mock trending news
  trending: Array(10).fill().map((_, i) => ({
    id: `trending-${i}`,
    title: `Trending News ${i}`,
    summary: `This is a trending news article ${i}. It's currently popular.`,
    published_at: new Date(Date.now() - Math.floor(Math.random() * 24 * 60 * 60 * 1000)).toISOString(),
    source: ['CNN', 'BBC', 'Reuters', 'Associated Press', 'The Guardian'][i % 5],
    url: `https://example.com/trending/${i}`,
    category: ['Politics', 'Business', 'Technology', 'Science', 'Health', 'Sports'][i % 6],
    trend_score: 100 - i,
    image_url: `https://example.com/images/trending-${i}.jpg`,
  })),
  
  // Mock sources
  sources: Array(5).fill().map((_, i) => ({
    id: `source-${i}`,
    name: ['CNN', 'BBC', 'Reuters', 'Associated Press', 'The Guardian'][i],
    url: `https://example.com/source/${i}`,
    type: ['rss', 'html', 'api'][i % 3],
    update_interval: [15, 30, 60, 120, 240][i],
    active: true
  })),
  
  // Mock stats
  stats: {
    period: 'day',
    start_time: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    end_time: new Date().toISOString(),
    interval: 'hour',
    metrics: {
      total_articles: 1250,
      total_sources: 25,
      total_categories: 10,
      average_sentiment: 0.65
    },
    time_series: Array(24).fill().map((_, i) => {
      const timestamp = new Date(Date.now() - (24 - i) * 60 * 60 * 1000).toISOString();
      const hour = new Date(timestamp).getHours();
      // More articles during working hours
      const hourFactor = 1 - Math.abs((hour - 12) / 12);
      const articles_count = Math.floor(30 + 70 * hourFactor);
      
      return {
        timestamp,
        articles_count,
        sources_count: Math.floor(articles_count / 5),
        average_sentiment: 0.5 + (hourFactor * 0.2)
      };
    })
  },
  
  // Mock category distribution
  categoryDistribution: [
    { category: 'Politics', count: 350, percentage: 28 },
    { category: 'Business', count: 275, percentage: 22 },
    { category: 'Technology', count: 200, percentage: 16 },
    { category: 'Science', count: 150, percentage: 12 },
    { category: 'Health', count: 125, percentage: 10 },
    { category: 'Sports', count: 100, percentage: 8 },
    { category: 'Entertainment', count: 50, percentage: 4 }
  ],
  
  // Mock top entities
  topEntities: [
    { entity: 'Entity 1', type: 'person', count: 100, sentiment: 0.75 },
    { entity: 'Entity 2', type: 'organization', count: 85, sentiment: 0.65 },
    { entity: 'Entity 3', type: 'location', count: 70, sentiment: 0.55 },
    { entity: 'Entity 4', type: 'event', count: 55, sentiment: 0.45 },
    { entity: 'Entity 5', type: 'other', count: 40, sentiment: 0.35 },
    { entity: 'Entity 6', type: 'person', count: 35, sentiment: 0.70 },
    { entity: 'Entity 7', type: 'organization', count: 30, sentiment: 0.60 },
    { entity: 'Entity 8', type: 'location', count: 25, sentiment: 0.50 },
    { entity: 'Entity 9', type: 'event', count: 20, sentiment: 0.40 },
    { entity: 'Entity 10', type: 'other', count: 15, sentiment: 0.30 }
  ],
  
  // Mock source performance
  sourcePerformance: [
    { source: 'Source 1', articles_count: 100, average_sentiment: 0.75, categories: ['Politics', 'Business', 'Technology'], reliability_score: 0.9 },
    { source: 'Source 2', articles_count: 85, average_sentiment: 0.70, categories: ['Politics', 'Business'], reliability_score: 0.85 },
    { source: 'Source 3', articles_count: 70, average_sentiment: 0.65, categories: ['Technology'], reliability_score: 0.8 },
    { source: 'Source 4', articles_count: 55, average_sentiment: 0.60, categories: ['Science', 'Health'], reliability_score: 0.75 },
    { source: 'Source 5', articles_count: 40, average_sentiment: 0.55, categories: ['Sports', 'Entertainment'], reliability_score: 0.7 }
  ]
};

/**
 * Helper function to simulate API delay
 */
const delay = (ms = 500) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * API client
 */
const api = {
  /**
   * Get news articles with pagination and filtering
   */
  getNews: async ({ page = 1, limit = 20, category = null, source = null } = {}) => {
    await delay();
    
    // Filter news based on category and source
    let filteredNews = [...mockData.news];
    if (category) {
      filteredNews = filteredNews.filter(item => item.category === category);
    }
    if (source) {
      filteredNews = filteredNews.filter(item => item.source === source);
    }
    
    // Calculate pagination
    const total = filteredNews.length;
    const startIndex = (page - 1) * limit;
    const endIndex = Math.min(startIndex + limit, total);
    const items = filteredNews.slice(startIndex, endIndex);
    
    return {
      items,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      },
      filters: { category, source }
    };
  },
  
  /**
   * Get a specific news article by ID
   */
  getNewsById: async (newsId) => {
    await delay();
    return mockData.news.find(item => item.id === newsId) || null;
  },
  
  /**
   * Get trending news articles
   */
  getTrendingNews: async (limit = 10) => {
    await delay();
    return mockData.trending.slice(0, limit);
  },
  
  /**
   * Search for news articles
   */
  searchNews: async ({ 
    query, 
    page = 1, 
    limit = 20, 
    sort_by = 'relevance',
    date_from = null,
    date_to = null,
    categories = [],
    sources = []
  } = {}) => {
    await delay();
    
    // In a real app, this would search using the backend
    // For now, just filter the mock data based on the query
    let results = mockData.news.filter(item => {
      // Simple search in title and summary
      const matchesQuery = query ? 
        (item.title.toLowerCase().includes(query.toLowerCase()) || 
         item.summary.toLowerCase().includes(query.toLowerCase())) : 
        true;
      
      // Filter by date range
      const publishedDate = new Date(item.published_at);
      const afterDateFrom = date_from ? publishedDate >= new Date(date_from) : true;
      const beforeDateTo = date_to ? publishedDate <= new Date(date_to) : true;
      
      // Filter by categories and sources
      const matchesCategory = categories.length > 0 ? 
        categories.includes(item.category) : true;
      const matchesSource = sources.length > 0 ? 
        sources.includes(item.source) : true;
      
      return matchesQuery && afterDateFrom && beforeDateTo && 
             matchesCategory && matchesSource;
    });
    
    // Sort results
    if (sort_by === 'date') {
      results.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
    }
    // Other sorting options would be implemented here
    
    // Calculate pagination
    const total = results.length;
    const startIndex = (page - 1) * limit;
    const endIndex = Math.min(startIndex + limit, total);
    const items = results.slice(startIndex, endIndex);
    
    return {
      query,
      items,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      },
      sort_by,
      filters: {
        date_from,
        date_to,
        categories,
        sources
      }
    };
  },
  
  /**
   * Get list of sources
   */
  getSources: async () => {
    await delay();
    return mockData.sources;
  },
  
  /**
   * Get system statistics
   */
  getStats: async (period = 'day') => {
    await delay();
    // In a real app, this would fetch different data based on the period
    return {
      ...mockData.stats,
      period
    };
  },
  
  /**
   * Get category distribution
   */
  getCategoryDistribution: async (period = 'day') => {
    await delay();
    // In a real app, this would fetch different data based on the period
    return mockData.categoryDistribution;
  },
  
  /**
   * Get top entities
   */
  getTopEntities: async (limit = 10, period = 'day') => {
    await delay();
    // In a real app, this would fetch different data based on the period
    return mockData.topEntities.slice(0, limit);
  },
  
  /**
   * Get source performance metrics
   */
  getSourcePerformance: async (limit = 10, period = 'day') => {
    await delay();
    // In a real app, this would fetch different data based on the period
    return mockData.sourcePerformance.slice(0, limit);
  }
};

export default api;