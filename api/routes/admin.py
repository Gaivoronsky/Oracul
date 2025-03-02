"""
Admin API routes.
Contains endpoints for administrative operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from typing import List, Optional

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/sources")
async def list_sources():
    """
    List all configured news sources.
    """
    return {"message": "List of sources"}


@router.post("/sources")
async def add_source(source_data: dict = Body(...)):
    """
    Add a new news source.
    """
    return {"message": "Source added", "source": source_data}


@router.put("/sources/{source_id}")
async def update_source(source_id: str, source_data: dict = Body(...)):
    """
    Update an existing news source.
    """
    return {"message": f"Source {source_id} updated", "source": source_data}


@router.delete("/sources/{source_id}")
async def delete_source(source_id: str):
    """
    Delete a news source.
    """
    return {"message": f"Source {source_id} deleted"}


@router.get("/stats")
async def get_stats(
    period: str = Query("day", regex="^(day|week|month|year)$")
):
    """
    Get system statistics for a specified period.
    """
    return {"message": f"Statistics for period: {period}"}


@router.post("/crawl")
async def trigger_crawl(sources: Optional[List[str]] = Body(None)):
    """
    Manually trigger a crawl operation.
    """
    if sources:
        return {"message": f"Crawl triggered for sources: {sources}"}
    return {"message": "Crawl triggered for all sources"}