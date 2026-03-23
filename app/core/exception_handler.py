import logging
from functools import wraps
import inspect

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


def _handle_exception(self, e: Exception):
    if isinstance(e, IntegrityError):
        self.db.rollback()
        logger.error(f"IntegrityError: {e}")
        if "UNIQUE constraint failed: users.email" in str(e):
            raise HTTPException(409, detail="Duplicate field: email")
        elif "Duplicate entry" in str(e):
            raise HTTPException(409, detail="Duplicate email, use another email")
        else:
            raise HTTPException(400, detail="Integrity error")

    elif isinstance(e, SQLAlchemyError):
        self.db.rollback()
        logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(500, detail="Database error")

    elif isinstance(e, ValidationError):
        logger.warning(f"Pydantic ValidationError: {e}")
        raise HTTPException(422, detail="Invalid data format")

    elif isinstance(e, ValueError):
        self.db.rollback()
        logger.warning(f"ValueError: {e}")
        raise HTTPException(422, detail=str(e))

    elif isinstance(e, TypeError):
        self.db.rollback()
        logger.warning(f"TypeError: {e}")
        raise HTTPException(422, detail="Type mismatch")

    elif isinstance(e, KeyError):
        self.db.rollback()
        logger.warning(f"KeyError: {e}")
        raise HTTPException(400, detail=f"Missing key: {str(e)}")

    elif isinstance(e, AttributeError):
        self.db.rollback()
        logger.error(f"AttributeError: {e}")
        raise HTTPException(500, detail="Attribute not found")

    elif isinstance(e, FileNotFoundError):
        logger.error(f"FileNotFoundError: {e}")
        raise HTTPException(404, detail="Requested file not found")

    elif isinstance(e, PermissionError):
        logger.error(f"PermissionError: {e}")
        raise HTTPException(403, detail="Permission denied")

    elif isinstance(e, HTTPException):
        raise e

    else:
        self.db.rollback()
        logger.critical(f"Unhandled Exception: {e}")
        raise HTTPException(500, detail="Internal server error")


def db_exception_handler(func):
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            self = args[0]
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                _handle_exception(self, e)
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            self = args[0]
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _handle_exception(self, e)
        return sync_wrapper
