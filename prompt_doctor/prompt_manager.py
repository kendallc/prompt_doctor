import os
from jinja2 import Template

class PromptManager:
    def __init__(self, initial_version='', prompts_dir='prompts'):
        self.prompts_dir = prompts_dir
    
    def get_prompt(self, prompt_id, version='latest'):
        prompt_path = os.path.join(self.prompts_dir, prompt_id, f"{version}.txt")
        with open(prompt_path, 'r') as f:
            prompt_text = f.read()
        return Template(prompt_text)
    
    def save_prompt(self, prompt_id, prompt_text):
        prompt_dir = os.path.join(self.prompts_dir, prompt_id)
        os.makedirs(prompt_dir, exist_ok=True)
        
        versions = [int(f.split('.')[0]) for f in os.listdir(prompt_dir) if f.endswith('.txt')]
        new_version = max(versions) + 1 if versions else 1
        
        prompt_path = os.path.join(prompt_dir, f"{new_version}.txt")
        with open(prompt_path, 'w') as f:
            f.write(prompt_text)
        
        return new_version
    
    def list_versions(self, prompt_id):
        prompt_dir = os.path.join(self.prompts_dir, prompt_id)
        return sorted([int(f.split('.')[0]) for f in os.listdir(prompt_dir) if f.endswith('.txt')], reverse=True)
    
    def render_prompt(self, prompt_id, version, context):
        prompt_template = self.get_prompt(prompt_id, version)
        rendered_prompt = prompt_template.render(context)
        
        return rendered_prompt
