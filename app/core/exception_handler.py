import logging
from functools import wraps

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


def db_exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]

        try:
            return func(*args, **kwargs)

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"IntegrityError: {e}")
            if "UNIQUE constraint failed: users.email" in str(e):
                raise HTTPException(409, detail="Duplicate field: email")
            elif "Duplicate entry" in str(e):
                raise HTTPException(409, detail="Duplicate email, use another email")
            else:
                raise HTTPException(400, detail="Integrity error")

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemyError: {e}")
            raise HTTPException(500, detail="Database error")

        except ValidationError as e:
            logger.warning(f"Pydantic ValidationError: {e}")
            raise HTTPException(422, detail="Invalid data format")

        except ValueError as e:
            self.db.rollback()
            logger.warning(f"ValueError: {e}")
            raise HTTPException(422, detail=str(e))

        except TypeError as e:
            self.db.rollback()
            logger.warning(f"TypeError: {e}")
            raise HTTPException(422, detail="Type mismatch")

        except KeyError as e:
            self.db.rollback()
            logger.warning(f"KeyError: {e}")
            raise HTTPException(400, detail=f"Missing key: {str(e)}")

        except AttributeError as e:
            self.db.rollback()
            logger.error(f"AttributeError: {e}")
            raise HTTPException(500, detail="Attribute not found")

        except FileNotFoundError as e:
            logger.error(f"FileNotFoundError: {e}")
            raise HTTPException(404, detail="Requested file not found")

        except PermissionError as e:
            logger.error(f"PermissionError: {e}")
            raise HTTPException(403, detail="Permission denied")

        except HTTPException as e:
            raise e

        except Exception as e:
            self.db.rollback()
            logger.critical(f"Unhandled Exception: {e}")
            raise HTTPException(500, detail="Internal server error")

    return wrapper
