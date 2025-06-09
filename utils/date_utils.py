from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def format_datetime(iso_string: str) -> str:
    """Format ISO datetime string to readable format"""
    try:
        if not iso_string or iso_string == "N/A":
            return "N/A"
            
        # Try different datetime formats
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]:
            try:
                dt = datetime.strptime(iso_string, fmt)
                return dt.strftime("%b-%d, %Y | %I:%M %p")
            except ValueError:
                continue
                
        # If no format matches, return original string
        return iso_string
        
    except Exception as e:
        logger.warning(f"Date formatting error for '{iso_string}': {e}")
        return "N/A"

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Validate that end date is after start date"""
    return end_date > start_date

def get_trip_duration(start_date: datetime, end_date: datetime) -> int:
    """Calculate trip duration in days"""
    return (end_date - start_date).days