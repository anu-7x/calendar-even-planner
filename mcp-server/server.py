import logging
# from ..models import CalendarEvent
from models import CalendarEvent

from mcp.server.fastmcp import FastMCP

# we are going with `stdio`, so no need to define the host and port
mcp = FastMCP(
  name="Calandar Event Management MCP Server",
)

# adding tools
# todo: move this to separate tools file. much easier to manage tools in a separate file & code is more readable. 
@mcp.tool()
async def create_calendar_event(event: CalendarEvent) -> bool:
  """
    Responsible for creating a calendar event for provided event details by calling the relevant API.
    only allow APIs are google calendar and outlook calendar.
    Args:
        event (models.CalendarEvent): The calendar event to be created.
    Returns:
        bool: True if the event was created successfully, False otherwise.
  """
  # This is a placeholder implementation.
  # In a real implementation, you would call the relevant API to create the event.
  print(f"--> [mcp-tool][create_calendar_event] - Creating calendar event: {event.title} from {event.start_time} to {event.end_time}")
  return True

#
if __name__ == "__main__":
    logging.info("--> MCP Server is Starting ... ")
    mcp.run(transport="stdio")
    logging.info("--> MCP Server is Running ... ")
