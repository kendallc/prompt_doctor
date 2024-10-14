import os
import shutil
import tempfile
import threading
import time
import unittest
import uuid
from itertools import count
from unittest.mock import MagicMock

from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import ChatCompletion, Choice
from selenium import webdriver
from selenium.webdriver.common.by import By

from prompt_doctor.debug_tool import DebugTool


def random_id():
    return str(uuid.uuid4())


# disable parallel testing:
class TestDebugTool(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(5)
        self.addCleanup(self.browser.quit)
        self.prompt_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.prompt_dir))

        # The Mocked LLM returns "LLM Response #N" for each N-th call
        self.llm_client_mock = MagicMock()
        self.llm_client_mock.chat.completions.create.side_effect = (
            ChatCompletion(
                choices=[
                    Choice(
                        finish_reason="stop",
                        index=0,
                        message=ChatCompletionMessage(
                            content=f"LLM Response #{n}",
                            role="assistant",
                        ),
                    )
                ],
                id=f"mocked_result_{n}",
                created=int(time.time()),
                model="gpt-4o-mini",
                object="chat.completion",
            )
            for n in count(1)
        )

        self.debug_tool = DebugTool(
            self.llm_client_mock, prompts_dir=self.prompt_dir, open_browser=False
        )

    def _call_create(self, *args, **kwargs):
        """
        Call create method of debug_tool in a separate thread to avoid blocking the main thread.
        The web server will be started (in another thread) when the create method is called.
        """
        self.llm_result: ChatCompletion | None = None

        def create():
            self.llm_result = self.debug_tool.create(*args, **kwargs)

        create_thread = threading.Thread(target=create, daemon=True)
        create_thread.start()
        time.sleep(1)

        self.addCleanup(create_thread.join)

    def test_new_prompt_id(self):
        """
        Invoke debug with prompt_id that doesn't exist.
        Should create one with a default template.
        """
        prompt_id = random_id()
        self._call_create(
            prompt_id,
            {"name": "Alice", "age": 25, "location": "New York"},
            model="gpt-4o-mini",
        )

        prompt_file = os.path.join(self.prompt_dir, f"{prompt_id}.txt")
        self.assertTrue(os.path.exists(prompt_file), "Prompt file not created")
        with open(prompt_file) as f:
            template_content = f.read()

        self.browser.get("http://localhost:5000")
        prompt_template = self.browser.find_element(By.ID, "prompt_template")
        self.assertEqual(
            prompt_template.text, template_content, "Prompt template not loaded"
        )

        self.browser.find_element(By.ID, "discard_and_quit").click()

        self.llm_client_mock.chat.completions.create.assert_called_once_with(
            messages=[
                {
                    "content": "Write your prompt template here using Jinja syntax",
                    "role": "user",
                }
            ],
            model="gpt-4o-mini",
        )

        self.assertEqual(
            self.llm_result.choices[0].message.content,
            "LLM Response #1",
            "LLM response not returned",
        )

    def test_discard_and_quit(self):
        """
        Invoke debug, edit, call LLM, then "discard and quit" button.
        Should invoke OpenAI API with the initial prompt.
        """
        prompt_id = random_id()
        prompt_file = os.path.join(self.prompt_dir, f"{prompt_id}.txt")
        prompt_template_1 = "{{ name }} is {{ age }} years old."
        with open(prompt_file, "w") as f:
            f.write(prompt_template_1)

        self._call_create(
            prompt_id,
            {"name": "Alice", "age": 25, "location": "New York"},
            model="gpt-4o-mini",
        )

        self.browser.get("http://localhost:5000")
        prompt_template = self.browser.find_element(By.ID, "prompt_template")
        self.assertEqual(
            prompt_template.text, prompt_template_1, "Prompt template not loaded"
        )

        rendered_prompt = self.browser.find_element(By.ID, "rendered_prompt")
        self.assertEqual(
            rendered_prompt.text,
            "Alice is 25 years old.",
            "Rendered prompt not displayed",
        )

        # Edit prompt template
        prompt_template_2 = (
            "{{ name }} is {{ age }} years old and lives in {{ location }}."
        )
        prompt_template.clear()
        prompt_template.send_keys(prompt_template_2)
        self.browser.find_element(By.ID, "call_llm").click()

        # Assert template and rendered shows new prompt:
        prompt_template = self.browser.find_element(By.ID, "prompt_template")
        self.assertEqual(
            prompt_template.text, prompt_template_2, "Prompt template not loaded"
        )

        rendered_prompt = self.browser.find_element(By.ID, "rendered_prompt")
        self.assertEqual(
            rendered_prompt.text,
            "Alice is 25 years old and lives in New York.",
            "Rendered prompt not displayed",
        )

        self.browser.find_element(By.ID, "discard_and_quit").click()

        with open(prompt_file) as f:
            self.assertEqual(f.read(), prompt_template_1, "Prompt template modified")

        self.assertEqual(
            self.llm_result.choices[0].message.content,
            "LLM Response #2",
            "LLM response not returned",
        )

    def test_edit_prompt_and_save(self):
        """
        Invoke debug, edit, click "call LLM" and then "save and quit" button.
        Should invoke OpenAI API with the initial prompt, then with the edited prompt.
        """
        prompt_id = random_id()
        prompt_file = os.path.join(self.prompt_dir, f"{prompt_id}.txt")
        prompt_template_1 = "{{ name }} is {{ age }} years old."
        with open(prompt_file, "w") as f:
            f.write(prompt_template_1)

        self._call_create(
            prompt_id,
            {"name": "Alice", "age": 25, "location": "New York"},
            model="gpt-4o-mini",
        )

        self.browser.get("http://localhost:5000")
        prompt_template = self.browser.find_element(By.ID, "prompt_template")
        self.assertEqual(
            prompt_template.text, prompt_template_1, "Prompt template not loaded"
        )

        rendered_prompt = self.browser.find_element(By.ID, "rendered_prompt")
        self.assertEqual(
            rendered_prompt.text,
            "Alice is 25 years old.",
            "Rendered prompt not displayed",
        )

        # Edit prompt template
        prompt_template_2 = (
            "{{ name }} is {{ age }} years old and lives in {{ location }}."
        )
        prompt_template.clear()
        prompt_template.send_keys(prompt_template_2)
        self.browser.find_element(By.ID, "call_llm").click()

        # Assert template and rendered shows new prompt:
        prompt_template = self.browser.find_element(By.ID, "prompt_template")
        self.assertEqual(
            prompt_template.text, prompt_template_2, "Prompt template not loaded"
        )

        rendered_prompt = self.browser.find_element(By.ID, "rendered_prompt")
        self.assertEqual(
            rendered_prompt.text,
            "Alice is 25 years old and lives in New York.",
            "Rendered prompt not displayed",
        )
        self.browser.find_element(By.ID, "save_and_quit").click()

        with open(prompt_file) as f:
            self.assertEqual(f.read(), prompt_template_2, "Prompt template not saved")

        self.assertEqual(
            self.llm_result.choices[0].message.content,
            "LLM Response #2",
            "LLM response not returned",
        )
