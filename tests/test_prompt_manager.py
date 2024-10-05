import unittest
import os
import shutil
from prompt_doctor.prompt_manager import PromptManager


class TestPromptManager(unittest.TestCase):
    def setUp(self):
        self.test_prompts_dir = "test_prompts"
        self.prompt_manager = PromptManager(prompts_dir=self.test_prompts_dir)

        # Create a test prompt
        os.makedirs(os.path.join(self.test_prompts_dir, "test_prompt"), exist_ok=True)
        with open(
            os.path.join(self.test_prompts_dir, "test_prompt", "1.txt"), "w"
        ) as f:
            f.write("This is a {{ adjective }} test prompt.")

    def tearDown(self):
        # Clean up the test prompts directory
        shutil.rmtree(self.test_prompts_dir)

    def test_initialization(self):
        self.assertEqual(self.prompt_manager.prompts_dir, self.test_prompts_dir)

    def test_get_prompt(self):
        prompt = self.prompt_manager.get_prompt("test_prompt", "1")
        self.assertEqual(
            prompt.render({"adjective": "great"}), "This is a great test prompt."
        )

    def test_save_prompt(self):
        new_version = self.prompt_manager.save_prompt(
            "test_prompt", "This is a {{ adjective }} updated prompt."
        )
        self.assertEqual(new_version, 2)

        prompt = self.prompt_manager.get_prompt("test_prompt", "2")
        self.assertEqual(
            prompt.render({"adjective": "fantastic"}),
            "This is a fantastic updated prompt.",
        )

    def test_list_versions(self):
        versions = self.prompt_manager.list_versions("test_prompt")
        self.assertEqual(versions, [1])

        self.prompt_manager.save_prompt("test_prompt", "New version")
        versions = self.prompt_manager.list_versions("test_prompt")
        self.assertEqual(versions, [2, 1])

    def test_render_prompt(self):
        rendered_prompt = self.prompt_manager.render_prompt(
            "test_prompt", "1", {"adjective": "wonderful"}
        )
        self.assertEqual(rendered_prompt, "This is a wonderful test prompt.")


if __name__ == "__main__":
    unittest.main()
