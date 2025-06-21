import logging

from const import const
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from openai import AsyncOpenAI
from contextlib import asynccontextmanager

from app.event_handler import EventCreationHandler, EventConfirmation
from mcp_client.client import MCPOpenAIClient

# configure the loggings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#
# intance for keeping the OpenAI instance & MCP client instance. 
openai_client = None
mcp_client_instance = None

# Lifespan event handler for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Manage application lifespan - startup and shutdown events.
    """
    global mcp_client_instance
    global openai_client
    
    # Startup
    logger.info("🚀 Starting FastAPI application...")
    try:
        # Initialize OpenAI client
        logger.info("📡 Initializing OpenAI client...")
        openai_client = AsyncOpenAI(api_key=const.OPEN_AI_API_KEY)
        app.state.openai_client = openai_client
        logger.info("✅ OpenAI client initialized successfully")
        #
        # Initialize MCP client
        logger.info("📡 Initializing MCP client...")
        mcp_client_instance = MCPOpenAIClient(
            model=const.OPEN_AI_MODEL,  # Use the model defined in const
            openai_client=openai_client  # Pass the OpenAI client instance
        )
        await mcp_client_instance.connect_to_server("mcp_server/server.py")  
        # Store in app state
        app.state.mcp_client = mcp_client_instance
        logger.info("✅ MCP client initialized successfully")
        logger.info("✅ FastAPI application startup complete")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize MCP client: {e}")
        raise
    #
    yield  # Application runs here.
    #
    # Shutdown
    logger.info("🛑 Shutting down FastAPI application...")
    try:
        if mcp_client_instance:
            await mcp_client_instance.cleanup()
            logger.info("✅ MCP client cleaned up successfully")
    except Exception as e:
        logger.error(f"❌ Error during MCP client cleanup: {e}")
    #
    logger.info("✅ FastAPI application shutdown complete")


# Create FastAPI app with lifespan event handler
app = FastAPI(
    title="Calendar Event Planner API",
    description="A FastAPI application with MCP integration for calendar event planning",
    version="1.0.0",
    lifespan=lifespan
)


class UserPromptTxt(BaseModel):
    desciption: str

# dependency injection for OpenAI model
def get_openai_model():
    if not hasattr(app.state, 'openai_model'):
        raise RuntimeError("OpenAI model not initialized")
    return app.state.openai_model

# dependency injection for MCP client
def get_mcp_client():
    if not hasattr(app.state, 'mcp_client'):
        raise RuntimeError("MCP client not initialized")
    return app.state.mcp_client

#
# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hello World", "app": "Calander Event Planner!"}

@app.post("/event-create", response_model=EventConfirmation)
async def create_event(
    user_prompt: UserPromptTxt,
    openai_model: AsyncOpenAI = Depends(get_openai_model),
    mcp_client_instance: MCPOpenAIClient = Depends(get_mcp_client)
    ):
    # simulate event creation logic ...
    event_handler = EventCreationHandler(
        openai_client=openai_model,
        mcp_client=mcp_client_instance
    )
    event_confirmation: EventConfirmation = await event_handler.initialize_event(user_prompt.desciption)
    if event_confirmation is None:
        return {
            "confirmation_message": "Failed to create event. Please try again.",
            "calendar_link": None
        }
    return event_confirmation
#
#
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.1", port=5050)
    print("Server is running on http://127.0.1:5050")
