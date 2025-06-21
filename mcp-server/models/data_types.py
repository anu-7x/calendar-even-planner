from pydantic import BaseModel, Field
from typing import List, Optional

class CalendarEvent(BaseModel):
    domain_type: str = Field(..., description="Type of the domain for the event")
    title: str = Field(..., description="Title of the calendar event")
    start_time: str = Field(..., description="Start time of the event in ISO format")
    end_time: str = Field(..., description="End time of the event in ISO format")
    location: Optional[str] = Field("", description="Location of the event")
    description: Optional[str] = Field("", description="Description of the event")
    attendees: Optional[List[str]] = Field(None, description="List of attendees for the event")
    organizer: Optional[str] = Field("", description="Organizer of the event")
