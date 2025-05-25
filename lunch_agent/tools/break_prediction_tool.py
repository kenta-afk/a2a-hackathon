"""Break prediction tool for estimating the available lunch break time."""

import os
import random
from typing import Optional
from datetime import datetime, time
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default break duration in minutes
DEFAULT_BREAK_DURATION = int(os.getenv('DEFAULT_BREAK_DURATION', '60'))

def predict_break_duration(tool_context: Optional[ToolContext] = None) -> dict:
    """
    Predict the available break time for lunch based on time of day and other factors.
    
    In a real-world scenario, this might consider:
    - Calendar events
    - Meeting schedules
    - User preferences
    - Historical break patterns
    
    For this demo, we'll use a simple time-based algorithm.
    
    Returns:
        dict: A dictionary containing:
            - duration_minutes: Estimated break time in minutes
            - confidence: Confidence score (0-1)
            - factors: Factors considered in the prediction
    """
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    # Store current time info in context for reference
    time_info = {
        "hour": current_hour,
        "minute": current_minute,
        "weekday": weekday,
        "is_weekend": weekday >= 5
    }
    if tool_context:
        tool_context.state['current_time_info'] = time_info
    
    # Initialize factors list
    factors = []
    
    # Base duration - typical lunch break
    if weekday >= 5:  # Weekend
        base_duration = 90  # More time on weekends
        factors.append("Weekend day")
    else:  # Weekday
        base_duration = 60  # Standard hour lunch on weekdays
        factors.append("Weekday")
    
    # Time-based adjustments
    if 11 <= current_hour < 12:
        # Early lunch, might have more time
        duration_adj = 15
        factors.append("Early lunch time")
    elif 12 <= current_hour < 13:
        # Peak lunch hour, might be busy
        duration_adj = -10
        factors.append("Peak lunch hour")
    elif 13 <= current_hour < 14:
        # Late lunch, might need to hurry
        duration_adj = -15
        factors.append("Late lunch")
    elif 14 <= current_hour < 15:
        # Very late lunch, likely quick
        duration_adj = -30
        factors.append("Very late lunch")
    else:
        # Off-peak hours
        duration_adj = 0
        factors.append("Off-peak mealtime")
    
    # Apply adjustments
    duration = max(15, base_duration + duration_adj)
    
    # Add some randomness to simulate other factors
    random_adj = random.randint(-10, 10)
    duration += random_adj
    if random_adj > 0:
        factors.append("Schedule appears flexible")
    elif random_adj < 0:
        factors.append("Detected potential time constraints")
    
    # Calculate confidence based on time of day
    if 11 <= current_hour < 15:
        confidence = 0.8  # Higher confidence during typical lunch hours
    else:
        confidence = 0.6  # Lower confidence outside typical lunch hours
    
    # Store the prediction in the context for other tools to use
    prediction = {
        "duration_minutes": duration,
        "confidence": confidence,
        "factors": factors
    }
    if tool_context:
        tool_context.state['break_prediction'] = prediction
    
    return prediction
