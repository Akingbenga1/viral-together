"""
Safe query helper functions to replace problematic SQLAlchemy methods.
These functions handle edge cases and provide more robust error handling.
"""
from typing import Optional, List, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncResult
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T', bound=DeclarativeBase)

class SafeQueryHelpers:
    """
    Safe query helper methods that handle edge cases better than standard SQLAlchemy methods.
    """
    
    @staticmethod
    async def safe_scalar_one_or_none(result: AsyncResult) -> Optional[T]:
        """
        Safely get one scalar result or None, handling multiple rows gracefully.
        
        This replaces scalar_one_or_none() which throws errors on multiple rows.
        Instead, it returns the first result if multiple rows are found.
        
        Args:
            result: SQLAlchemy AsyncResult object
            
        Returns:
            The first scalar result or None if no results found
        """
        try:
            # First try the standard method
            return result.scalar_one_or_none()
        except Exception:
            # If that fails (multiple rows), try to get the first one
            try:
                return result.unique().scalars().first()
            except Exception:
                # If all else fails, return None
                return None
    
    @staticmethod
    async def safe_scalars_all(result: AsyncResult) -> List[T]:
        """
        Safely get all scalar results, handling relationship issues.
        
        This replaces scalars().all() and handles unique() properly.
        
        Args:
            result: SQLAlchemy AsyncResult object
            
        Returns:
            List of scalar results
        """
        try:
            return result.unique().scalars().all()
        except Exception:
            # Fallback to basic scalars().all() if unique() fails
            try:
                return result.scalars().all()
            except Exception:
                return []
    
    @staticmethod
    async def safe_scalars_first(result: AsyncResult) -> Optional[T]:
        """
        Safely get the first scalar result or None.
        
        This is more robust than scalars().first() and handles relationship issues.
        
        Args:
            result: SQLAlchemy AsyncResult object
            
        Returns:
            The first scalar result or None if no results found
        """
        try:
            return result.unique().scalars().first()
        except Exception:
            # Fallback to basic scalars().first() if unique() fails
            try:
                return result.scalars().first()
            except Exception:
                return None
    
    @staticmethod
    async def safe_scalars_one(result: AsyncResult) -> T:
        """
        Safely get exactly one scalar result, with better error handling.
        
        This replaces scalars().one() with more informative error messages.
        
        Args:
            result: SQLAlchemy AsyncResult object
            
        Returns:
            The scalar result
            
        Raises:
            ValueError: If no results or multiple results found (with better error messages)
        """
        try:
            return result.unique().scalars().one()
        except Exception as e:
            # Provide more informative error messages
            if "No row was found" in str(e):
                raise ValueError("Expected exactly one result, but found none")
            elif "Multiple rows were found" in str(e):
                raise ValueError("Expected exactly one result, but found multiple rows")
            else:
                raise ValueError(f"Query error: {str(e)}")

# Convenience functions for easy import
async def safe_scalar_one_or_none(result: AsyncResult) -> Optional[T]:
    """Convenience function for safe_scalar_one_or_none"""
    return await SafeQueryHelpers.safe_scalar_one_or_none(result)

async def safe_scalars_all(result: AsyncResult) -> List[T]:
    """Convenience function for safe_scalars_all"""
    return await SafeQueryHelpers.safe_scalars_all(result)

async def safe_scalars_first(result: AsyncResult) -> Optional[T]:
    """Convenience function for safe_scalars_first"""
    return await SafeQueryHelpers.safe_scalars_first(result)

async def safe_scalars_one(result: AsyncResult) -> T:
    """Convenience function for safe_scalars_one"""
    return await SafeQueryHelpers.safe_scalars_one(result)
