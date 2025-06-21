import asyncio
import json
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

OPEN_AI_API_KEY = "api-key-1234567890abcdefg"  # Replace with your actual OpenAI API key
OPEN_AI_MODEL = "gpt-4o-mini"


class MCPOpenAIClient:
    """Client for interacting with OpenAI models using MCP tools."""

    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize the OpenAI MCP client.
        Args:
            model: The OpenAI model to use.
        """
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai_client = AsyncOpenAI(
            api_key=OPEN_AI_API_KEY
        )
        self.model = OPEN_AI_MODEL
        self.stdio: Optional[Any] = None
        self.write: Optional[Any] = None

    async def connect_to_server(self, server_script_path: str = "server.py"):
        """
        Connect to an MCP server.
        Args:
            server_script_path: Path to the server script.
        """
        try:
            # Server configuration
            server_params = StdioServerParameters(
                command="python",
                args=[server_script_path],
            )

            # Connect to the server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )

            # Initialize the connection
            await self.session.initialize()

            # List available tools
            tools_result = await self.session.list_tools()
            print("Connected to server with tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")
                
        except Exception as e:
            print(f"Error connecting to server: {e}")
            await self.cleanup()
            raise

    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """
        Get available tools from the MCP server in OpenAI format.
        Returns:
            A list of tools in OpenAI format.
        """
        if not self.session:
            raise RuntimeError("Not connected to server")
            
        tools_result = await self.session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools_result.tools
        ]

    async def process_query(self, query: str) -> str:
        """
        Process a query using OpenAI and available MCP tools.
        Args:
            query: The user query.
        Returns:
            The response from OpenAI.
        """
        if not self.session:
            raise RuntimeError("Not connected to server")
            
        # Get available tools
        tools = await self.get_mcp_tools()

        # Initial OpenAI API call
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
        )

        # Get assistant's response
        assistant_message = response.choices[0].message

        # Initialize conversation with user query and assistant response
        messages = [
            {"role": "user", "content": query},
            assistant_message,
        ]

        # Handle tool calls if present
        if assistant_message.tool_calls:
            # Process each tool call
            for tool_call in assistant_message.tool_calls:
                try:
                    # Execute tool call
                    result = await self.session.call_tool(
                        tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments),
                    )

                    # Add tool response to conversation
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result.content[0].text,
                        }
                    )
                except Exception as e:
                    print(f"Error executing tool call: {e}")
                    # Add error message to conversation
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error: {str(e)}",
                        }
                    )

            # Get final response from OpenAI with tool results
            final_response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="none",  # Don't allow more tool calls
            )

            return final_response.choices[0].message.content

        # No tool calls, just return the direct response
        return assistant_message.content

    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.exit_stack.aclose()
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.cleanup()


async def main():
    """Main entry point for the client."""
    try:
        async with MCPOpenAIClient() as client:
            await client.connect_to_server("mcp_server/server.py")
            
            # Test with a sample query
            query = "Create a calendar event for a team meeting tomorrow at 2 PM"
            response = await client.process_query(query)
            print(f"\nResponse: {response}")
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    # Use asyncio.run with proper exception handling
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")