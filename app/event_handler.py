
from datetime import datetime
from typing import Optional, Any
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from const.const import OPEN_AI_MODEL

from mcp_client.client import MCPOpenAIClient
from models import EventConfirmation, EventExtraction, EventDetails

# todo: remove these!
'''
class EventConfirmation(BaseModel):
    """Third LLM call: Generate confirmation message"""
    confirmation_message: str = Field(
        description="Natural language confirmation message"
    )
    calendar_link: Optional[str] = Field(
        description="Generated calendar link if applicable"
    )

class EventExtraction(BaseModel):
    """First LLM call: Extract basic event information"""
    description: str = Field(description="Raw description of the event")
    is_calendar_event: bool = Field(
        description="Whether this text describes a calendar event"
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")

class EventDetails(BaseModel):
    """Second LLM call: Parse specific event details"""
    name: str = Field(description="Name of the event")
    date: str = Field(
        description="Date and time of the event. Use ISO 8601 to format this value."
    )
    duration_minutes: int = Field(description="Expected duration in minutes")
    participants: list[str] = Field(description="List of participants")
'''

class EventCreationHandler:
  def __init__(self, openai_client: AsyncOpenAI, mcp_client: MCPOpenAIClient):
    self.openai_client = openai_client
    self.mcp_client = mcp_client
    self.model = OPEN_AI_MODEL

  async def initialize_event(self, user_prompt: str) -> Optional[EventConfirmation]:
    result: Optional[EventConfirmation] | None = await self.__process_calendar_event(user_prompt)
    return result

  async def __evaluate_event_extraction(self, user_prompt: str) -> EventExtraction:
    print(f" --> [__evaluate_event_extraction] evaluating the event before processing: {user_prompt}")
    today: datetime = datetime.now()
    date_context: str = f"Today is {today.strftime('%A, %B %d, %Y')}."
    #
    completion = await self.openai_client.beta.chat.completions.parse(
       model=self.model,
       messages=[
          { # system prompt
             "role": "system",
             "content": f"{date_context} Analyze if the text describes a calendar event.",
          },
          { # user prompt
             "role": "user",
             "content": user_prompt,
          }
       ],
       response_format=EventExtraction,
    )
    result: EventExtraction = completion.choices[0].message.parsed
    print(
        f" --> [__evaluate_event_extraction] Extraction complete - Is calendar event: {result.is_calendar_event}, Confidence: {result.confidence_score:.2f}"
    )
    return result

  async def __parse_event_details(self, user_prompt: str) -> EventDetails:
    print(f" --> [__parse_event_details] Parsing event details from: {user_prompt}")
    today: datetime = datetime.now()
    date_context: str = f"Today is {today.strftime('%A, %B %d, %Y')}."
    #
    completion = await self.openai_client.beta.chat.completions.parse(
       model=self.model,
       messages=[
          { # system prompt
             "role": "system",
             "content": f"{date_context} Extract detailed event information. When dates reference 'next Tuesday' or similar relative dates, use this current date as reference.",
          },
          { # user prompt
             "role": "user",
             "content": user_prompt,
          }
       ],
       response_format=EventDetails,
    )
    #
    result: EventDetails = completion.choices[0].message.parsed
    print(f" --> [__parse_event_details] Event details parsed: {result}")
    return result

  async def __event_creation(self, event_details: EventDetails) -> EventConfirmation:
    print(f" --> [__event_creation] Creating calendar event with details: {event_details}")
    # Here you would typically create the event in your calendar system
    # todo: this is where we going to use the MCP client to create the event in the calendar using tools.
    llm_promopt: list[dict[str, Any]] = [
         { # system prompt
               "role": "system",
               "content": "Create a calendar event with the provided details.",
         },
         { # user prompt
               "role": "user",
               "content": f"Create an event named '{event_details.name}' on {event_details.date} for {event_details.duration_minutes} minutes with participants: {', '.join(event_details.participants)}.",
         }
    ]
    
    # For demonstration, we will just return a mock confirmation
    confirmation = EventConfirmation(
        confirmation_message=f"Event '{event_details.name}' created successfully on {event_details.date}.",
        calendar_link="https://example.com/calendar/event12345"
    )
    print(f" --> [__event_creation] Event creation confirmed: {confirmation}")
    return confirmation

  async def __process_calendar_event(self, user_prompt: str) -> None | EventConfirmation:
    print(f" --> [__process_calendar_event] Processing calendar event: {user_prompt}")
    # first LLM call
    extraction_result: EventExtraction = await self.__evaluate_event_extraction(user_prompt)
    if (
       not extraction_result.is_calendar_event or
       extraction_result.confidence_score < 0.7
    ): 
       print(f" --> [__process_calendar_event] Not a valid calendar event: {user_prompt}")
       return None
    #
    print(f" --> [__process_calendar_event] Valid calendar event detected: {user_prompt}")

    # second LLM call to parse specific event details
    event_details: EventDetails = await self.__parse_event_details(extraction_result.description)
    print(f" --> [__process_calendar_event] Event details extracted: {event_details}")

    # third LLM call to create the event
    confirmation: EventConfirmation = await self.__event_creation(event_details)
    print(f" --> [__process_calendar_event] Event creation confirmed: {confirmation}")

    #
    return confirmation
