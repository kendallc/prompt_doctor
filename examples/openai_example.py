import os
from prompt_doctor import PromptManager, DebugTool
from openai import OpenAI

# Set up OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = "gpt-4o-mini"

prompt_manager = PromptManager()
debug_tool = DebugTool(prompts_dir='prompts')

# Define a prompt ID and initial prompt text
prompt_id = "my_prompt"
initial_prompt = "This is a test prompt for {{name}}"

context = {}

refined_prompt = debug_tool.run(prompt_id, initial_prompt, context)

# Note this call may be redundant if we're using the debug tool to refine the prompt
response = client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=[
        {
            "role": "system",
            "content": "You are a friendly AI assistant. Greet the user and ask how you can help them today.",
        },
        {"role": "user", "content": refined_prompt},
    ],
)

# Print the LLM response
print(response.choices[0].message.content)