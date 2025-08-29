from datetime import datetime
import json

def datetime_encoder(obj):
    """Custom JSON encoder for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def json_dumps(obj):
    """Helper function to dump JSON with datetime support"""
    return json.dumps(obj, default=datetime_encoder)