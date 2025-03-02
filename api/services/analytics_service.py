"""
Analytics service.
Provides business logic for analytics-related operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class AnalyticsService:
    """
    Service for handling analytics-related operations.
    """
    
    async def get_stats(self, period: str = "day") -> Dict[str, Any]:
        """
        Get system statistics for a specified period.
        
        Args:
            period: Time period for statistics (day, week, month, year)
            
        Returns:
            Dictionary with statistics data
        """
        # In a real implementation, this would query the database
        # For now, return mock data
        
        # Determine time range based on period
        now = datetime.now()
        if period == "day":
            start_time = now - timedelta(days=1)
            interval = "hour"
        elif period == "week":
            start_time = now - timedelta(weeks=1)
            interval = "day"
        elif period == "month":
            start_time = now - timedelta(days=30)
            interval = "day"
        elif period == "year":
            start_time = now - timedelta(days=365)
            interval = "month"
        else:
            start_time = now - timedelta(days=1)
            interval = "hour"
            
        # Generate mock time series data
        time_series = self._generate_time_series(start_time, now, interval)
            
        return {
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "interval": interval,
            "metrics": {
                "total_articles": sum(point["articles_count"] for point in time_series),
                "total_sources": 25,  # Mock value
                "total_categories": 10,  # Mock value
                "average_sentiment": 0.65  # Mock value
            },
            "time_series": time_series
        }
    
    async def get_top_entities(self, limit: int = 10, period: str = "day") -> List[Dict[str, Any]]:
        """
        Get top entities mentioned in news articles.
        
        Args:
            limit: Maximum number of entities to return
            period: Time period for statistics (day, week, month, year)
            
        Returns:
            List of top entities with counts
        """
        # In a real implementation, this would query the database
        # For now, return mock data
        return [
            {
                "entity": f"Entity {i}",
                "type": ["person", "organization", "location", "event", "other"][i % 5],
                "count": 100 - (i * 5),
                "sentiment": 0.5 + (i * 0.05)
            }
            for i in range(limit)
        ]
    
    async def get_category_distribution(self, period: str = "day") -> List[Dict[str, Any]]:
        """
        Get distribution of news articles by category.
        
        Args:
            period: Time period for statistics (day, week, month, year)
            
        Returns:
            List of categories with counts
        """
        # In a real implementation, this would query the database
        # For now, return mock data
        categories = [
            "Politics", "Business", "Technology", "Science", 
            "Health", "Sports", "Entertainment", "World", 
            "Environment", "Education"
        ]
        
        total = 1000  # Mock total
        remaining = total
        result = []
        
        for i, category in enumerate(categories):
            # Last category gets the remainder
            if i == len(categories) - 1:
                count = remaining
            else:
                # Distribute with decreasing counts
                count = int(total / (i + 2))
                remaining -= count
                
            result.append({
                "category": category,
                "count": count,
                "percentage": round(count / total * 100, 2)
            })
            
        return result
    
    async def get_source_performance(self, limit: int = 10, period: str = "day") -> List[Dict[str, Any]]:
        """
        Get performance metrics for news sources.
        
        Args:
            limit: Maximum number of sources to return
            period: Time period for statistics (day, week, month, year)
            
        Returns:
            List of sources with performance metrics
        """
        # In a real implementation, this would query the database
        # For now, return mock data
        return [
            {
                "source": f"Source {i}",
                "articles_count": 100 - (i * 7),
                "average_sentiment": 0.5 + (i * 0.04),
                "categories": ["Politics", "Business", "Technology"][:3 - (i % 3)],
                "reliability_score": 0.9 - (i * 0.05)
            }
            for i in range(limit)
        ]
    
    def _generate_time_series(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        interval: str
    ) -> List[Dict[str, Any]]:
        """
        Generate mock time series data.
        
        Args:
            start_time: Start time
            end_time: End time
            interval: Interval type (hour, day, month)
            
        Returns:
            List of time series data points
        """
        result = []
        current = start_time
        
        while current < end_time:
            if interval == "hour":
                next_point = current + timedelta(hours=1)
            elif interval == "day":
                next_point = current + timedelta(days=1)
            elif interval == "month":
                # Approximate a month as 30 days
                next_point = current + timedelta(days=30)
            else:
                next_point = current + timedelta(hours=1)
                
            # Generate random-ish but somewhat realistic data
            hour_factor = current.hour / 24.0  # Time of day factor
            weekday_factor = current.weekday() / 7.0  # Day of week factor
            
            # More articles during working hours and weekdays
            base_count = 50
            time_multiplier = 1.5 - abs(hour_factor - 0.5) * 2  # Peak at noon
            day_multiplier = 1.3 - (weekday_factor * 0.6)  # More on weekdays
            
            articles_count = int(base_count * time_multiplier * day_multiplier)
            
            result.append({
                "timestamp": current.isoformat(),
                "articles_count": articles_count,
                "sources_count": int(articles_count / 5),
                "average_sentiment": 0.5 + (hour_factor * 0.2)  # More positive during the day
            })
            
            current = next_point
            
        return result