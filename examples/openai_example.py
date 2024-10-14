import os
from prompt_doctor import DebugTool
from openai import OpenAI

# Set up OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = "gpt-4o-mini"

debug_tool = DebugTool(client, prompts_dir='prompts')

# Define a prompt ID and initial prompt text
prompt_id = "my_prompt"
context = {"name": "Alice", "age": 25, "location": "New York"}

# Note this call may be redundant if we're using the debug tool to refine the prompt
response = debug_tool.create(
    model=OPENAI_MODEL,
    prompt_id=prompt_id,
    context=context,
)

# Print the LLM response
print(response.choices[0].message.content)
