# Strands Agent - Personal Assistant

This project demonstrates how to create a personal assistant agent using the Strands Agents SDK. The agent can manage appointments using custom tools and built-in tools.

## Overview

This personal assistant agent can:
- Create appointments
- List appointments
- Update appointments
- Calculate using a built-in calculator tool
- Check the current time

## Prerequisites

- Python 3.10+
- AWS account
- Anthropic Claude 3.7 enabled on Amazon Bedrock
- IAM role with permissions to access Amazon Bedrock

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Make sure you have AWS credentials configured with access to Amazon Bedrock.

3. Run the agent:
   ```
   python main.py
   ```

## Project Structure

- `main.py`: The main script that defines the agent, tools, and runs the interactive loop
- `requirements.txt`: List of required Python packages

## Tool Definitions

This project uses the decorator approach for tool definitions:

1. `create_appointment`: Creates a new appointment with date, location, title, and description
2. `list_appointments`: Lists all available appointments
3. `update_appointment`: Updates an existing appointment based on its ID

## Example Usage

```
You: Book 'Team Meeting' for tomorrow 3pm in NYC. This meeting will discuss project updates.
Assistant: I've created an appointment for you. 
Appointment with id 123e4567-e89b-12d3-a456-426614174000 created.

You: What appointments do I have?
Assistant: Here are your appointments:
[{'id': '123e4567-e89b-12d3-a456-426614174000', 'date': '2025-05-22 15:00', 'location': 'NYC', 'title': 'Team Meeting', 'description': 'This meeting will discuss project updates.'}]

You: Update the Team Meeting location to Boston
Assistant: I've updated the appointment location to Boston.
Appointment 123e4567-e89b-12d3-a456-426614174000 updated with success.
```
