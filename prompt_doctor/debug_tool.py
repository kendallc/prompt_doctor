import json
import logging
import threading
import webbrowser
from pathlib import Path

from flask import Flask, render_template, request, redirect
from jinja2 import Template
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from werkzeug.serving import make_server

logger = logging.getLogger(__name__)


class DebugTool:

    def __init__(self, oai_client: OpenAI, prompts_dir="prompts", open_browser=True):
        self.llm_client = oai_client
        self.prompts_dir = Path(prompts_dir)
        self.open_browser = open_browser

    def _call_llm(self, prompt: str, **oai_kwargs) -> ChatCompletion:
        # TODO: extend template to support multiple messages/roles
        return self.llm_client.chat.completions.create(
            messages=[{"content": prompt, "role": "user"}],
            **oai_kwargs)

    def create(self, prompt_id: str, context: dict, **oai_kwargs) -> ChatCompletion:

        if "messages" in oai_kwargs:
            raise ValueError(
                "The 'messages' parameter is not supported in the debug tool. Use 'template_name' instead.")

        prompt_file_name = self.prompts_dir / (prompt_id + ".txt")

        # Create prompt if it doesn't exist
        if not prompt_file_name.exists():
            with prompt_file_name.open("w") as f:
                f.write("Write your prompt template here using Jinja syntax")

        # Read the prompt template
        with prompt_file_name.open("r") as f:
            current_prompt_template = f.read()

        # Render and call the LLM
        current_rendered_prompt = Template(current_prompt_template).render(context)
        current_llm_response = self._call_llm(current_rendered_prompt, **oai_kwargs)

        server_lock = threading.Semaphore(0)

        app = Flask(__name__)

        @app.route("/done", methods=["GET"])
        def done():
            server_lock.release()
            return "You can close this tab now."

        @app.route("/", methods=["GET", "POST"])
        def debug_prompt():
            nonlocal current_prompt_template, current_rendered_prompt, current_llm_response

            if request.method == "POST":
                match request.form["action"]:
                    case "call_llm":
                        current_prompt_template = request.form["prompt_template"]
                        current_rendered_prompt = Template(current_prompt_template).render(context)
                        current_llm_response = self._call_llm(current_rendered_prompt, **oai_kwargs)
                        redirect("/")
                    case "save_and_quit":
                        with prompt_file_name.open("w") as f:
                            f.write(request.form["prompt_template"])
                        return redirect("/done")
                    case "discard_and_quit":
                        return redirect("/done")
                    case _:
                        raise ValueError("Invalid action")

            return render_template(
                "debug_tool.html",
                prompt_id=prompt_id,
                prompt_template=current_prompt_template,
                rendered_prompt=current_rendered_prompt,
                context=json.dumps(context, indent=2),
                llm_response=current_llm_response.model_dump_json(indent=2)
            )

        # Start the Flask app in a separate thread
        server = make_server("localhost", 5000, app)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        logger.info("Debug tool started at http://127.0.0.1:5000")

        # Open the debug tool in the default web browser
        if self.open_browser:
            webbrowser.open("http://127.0.0.1:5000")

        # Wait for the server to finish
        server_lock.acquire(blocking=True)
        server.shutdown()
        server_thread.join()
        logger.info("Debug tool closed")

        # Return the latest LLM response
        return current_llm_response
