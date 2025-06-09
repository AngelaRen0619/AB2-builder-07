"""
Test script for the Strands Agent personal assistant.
This script demonstrates how to use the agent with specific examples.
"""

import os
from main import create_appointment, list_appointments, update_appointment
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import calculator, current_time


def print_agent_response(agent, result):
    """Helper function to print agent responses correctly."""
    print("Response:", end=" ")
    if hasattr(result, 'content'):
        # For newer versions of strands
        print(result.content)
    else:
        # For older versions or different return structure
        # Get the last assistant message
        last_assistant_message = None
        for message in agent.messages:
            if message.get("role") == "assistant":
                last_assistant_message = message
        
        if last_assistant_message:
            # Extract text content from the message
            response_text = ""
            for content_item in last_assistant_message.get("content", []):
                if "text" in content_item:
                    response_text += content_item["text"]
            
            print(response_text)
        else:
            print("No response available")


def test_agent():
    """Test the personal assistant agent with specific examples."""
    # Define system prompt
    system_prompt = """You are a helpful personal assistant that specializes in managing my appointments and calendar. 
You have access to appointment management tools, a calculator, and can check the current time to help me organize my schedule effectively. 
Always provide the appointment id so that I can update it if required"""

    # Define the model
    model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        max_tokens=64000,
        additional_request_fields={
            "thinking": {
                "type": "disabled",
            }
        },
    )

    # Create the agent
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            current_time,
            calculator,
            create_appointment,
            list_appointments,
            update_appointment,
        ],
    )

    print("=== Testing Personal Assistant Agent ===")
    
    # Test 1: Simple calculation
    print("\n--- Test 1: Simple calculation ---")
    result = agent("How much is 2+2?")
    print_agent_response(agent, result)
    
    # Test 2: Create an appointment
    print("\n--- Test 2: Create an appointment ---")
    result = agent("Book 'Agent fun' for tomorrow 3pm in NYC. This meeting will discuss all the fun things that an agent can do")
    print_agent_response(agent, result)
    
    # Test 3: List appointments
    print("\n--- Test 3: List appointments ---")
    result = agent("What appointments do I have?")
    print_agent_response(agent, result)
    
    # Test 4: Update an appointment
    print("\n--- Test 4: Update an appointment ---")
    result = agent("Oh no! My bad, 'Agent fun' is actually happening in DC")
    print_agent_response(agent, result)
    
    # Test 5: Check current time
    print("\n--- Test 5: Check current time ---")
    result = agent("What time is it right now?")
    print_agent_response(agent, result)
    
    print("\n=== Testing Complete ===")


if __name__ == "__main__":
    # Remove any existing database for clean testing
    if os.path.exists("appointments.db"):
        os.remove("appointments.db")
        
    test_agent()
