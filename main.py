from const import const
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from openai import AsyncOpenAI
from app.event_handler import EventCreationHandler, EventConfirmation


# Create FastAPI instance
app = FastAPI(
    title="My FastAPI App",
    description="A simple FastAPI application built with uv",
    version="1.0.0"
)
#
# assigned initialize openai model to the app. 
openai = AsyncOpenAI(
    api_key=const.OPEN_AI_API_KEY,
)
# store the openai model in the app state
app.state.openai_model = openai

class UserPromptTxt(BaseModel):
    desciption: str

# dependency injection for OpenAI model
def get_openai_model():
    if not hasattr(app.state, 'openai_model'):
        raise RuntimeError("OpenAI model not initialized")
    return app.state.openai_model
#
# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hello World", "app": "Calander Event Planner!"}

@app.post("/event-create", response_model=EventConfirmation)
async def create_event(
    user_prompt: UserPromptTxt,
    openai_model: AsyncOpenAI = Depends(get_openai_model)
    ):
    # simulate event creation logic ...
    event_handler = EventCreationHandler(openai_client=openai_model)
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
