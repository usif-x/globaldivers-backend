from slowapi import Limiter
from slowapi.util import get_remote_address

# Define and export the limiter instance from this central file
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
