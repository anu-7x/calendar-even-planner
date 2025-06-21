# calendar-even-planner
AI-System which use to assign calendar events for users 


workflow
---------
0. user send req to add a calendar event
1. get the event & evaluate it & identify it is a valid calendar event or not.
2. if valid, then call LLM again to get events details for a given format. 
3. then using the MCP client, get a tool to set the calander event
4. tigger the tool & set the event
5. send the success response to the user!
