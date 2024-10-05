from flask import Flask, render_template, request, jsonify
from .prompt_manager import PromptManager
from .llm_call import call_llm_api
import threading
import webbrowser
import json

class DebugTool:
    def __init__(self, prompts_dir='prompts'):
        self.app = Flask(__name__)
        self.prompt_manager = PromptManager(prompts_dir)
        
        @self.app.route('/', methods=['GET', 'POST'])
        def debug_prompt():
            if request.method == 'POST':
                prompt_id = request.form['prompt_id']
                prompt_text = request.form['prompt_text']
                context = json.loads(request.form['context'])
                
                new_version = self.prompt_manager.save_prompt(prompt_id, prompt_text)
                rendered_prompt = self.prompt_manager.render_prompt(prompt_id, str(new_version), context)
                
                # Call the OpenAI API
                api_response = call_llm_api(rendered_prompt)
                
                return jsonify({
                    'rendered_prompt': rendered_prompt,
                    'version': new_version,
                    'api_response': api_response
                })
            
            return render_template('debug_tool.html', 
                                   prompt_id=self.current_prompt_id, 
                                   initial_prompt=self.current_initial_prompt, 
                                   context=json.dumps(self.current_context, indent=2))
    
    def run(self, prompt_id, initial_prompt, context):
        self.current_prompt_id = prompt_id
        self.current_initial_prompt = initial_prompt
        self.current_context = context

        # Start the Flask app in a separate thread
        threading.Thread(target=self.app.run, daemon=True).start()
        
        # Open the debug tool in the default web browser
        webbrowser.open('http://127.0.0.1:5000')
        
        # Wait for user input to continue
        input("Press Enter to continue after finishing with the debug tool...")
        
        # Return the latest version of the prompt
        latest_version = self.prompt_manager.list_versions(prompt_id)[0]
        return self.prompt_manager.get_prompt(prompt_id, str(latest_version)).render(context)