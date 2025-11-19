"""
Minimal debugging agent that reads external prompts and context.
"""
import os
import json
import subprocess
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
from config import BOLD, BLUE, RED, GREEN, YELLOW, RESET


class DebuggerAgent:
    def __init__(self, project_path, env_name, script_name):
        load_dotenv()
        self.project_path = project_path
        self.env_name = env_name
        self.script_name = script_name
        self.script_path = os.path.join(project_path, script_name)
        self.client = Groq()
        
        self.system_prompt = self._load_file("prompt.txt")
        self.context = self._load_file("context.txt")
    
    def _load_file(self, filename):
        """Load content from external file."""
        path = Path(__file__).resolve().parent / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""
    
    def _execute_script(self):
        """Execute script and capture output/errors."""
        try:
            result = subprocess.run(
                ["python", self.script_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "traceback": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Script execution timed out",
                "traceback": "Script execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "traceback": str(e)
            }
    
    def _get_numbered_source(self):
        """Get source code with line numbers."""
        with open(self.script_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "\n".join(f"{i+1:3d} | {line.rstrip()}" for i, line in enumerate(lines))
    
    def run_debug(self):
        """Debug a script: execute → analyze → propose corrections."""
        print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"DEBUGGING: {self.script_name}")
        print(f"{'='*70}\n{RESET}")
        
        # Step 1: Execute script
        print("Step 1: Executing script...\n")
        execution = self._execute_script()
        
        if execution["success"]:
            print("✅ Script executed successfully!\n")
            if execution["stdout"]:
                print("Output:")
                print(execution["stdout"])
            return
        
        print("❌ Error detected:\n")
        print(execution["stderr"])
        print()
        
        # Step 2: Get numbered source
        print("Step 2: Reading source code...\n")
        numbered_source = self._get_numbered_source()
        
        # Step 3: Analyze with AI
        print("Step 3: Analyzing with Groq AI...\n")
        analysis = self._analyze(numbered_source, execution["traceback"])
        
        # Display and apply fixes
        self._display_analysis(analysis)
        self._apply_fixes_interactive(analysis)
    
    def _analyze(self, source_code, traceback):
        """Analyze bug using AI with system prompt."""
        user_message = f"{self.context}\n\nSOURCE CODE:\n{source_code}\n\nTRACEBACK:\n{traceback}"
        
        response = self.client.messages.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "user", "content": user_message}
            ],
            system=self.system_prompt,
            max_tokens=2000
        )
        
        content = response.content[0].text
        
        try:
            analysis = json.loads(content)
        except json.JSONDecodeError:
            # Fallback if AI doesn't return valid JSON
            analysis = {
                "delete": [],
                "add": [],
                "explanations": [content],
                "not_related_to_code": []
            }
        
        return analysis
    
    def _display_analysis(self, analysis):
        """Display analysis results."""
        print(f"{BOLD}{BLUE}=== BUG ANALYSIS ==={RESET}\n")
        
        explanations = analysis.get("explanations", [])
        if isinstance(explanations, str):
            explanations = [explanations]
        
        if explanations:
            print(f"{BOLD}Explanations:{RESET}")
            for item in explanations:
                print(f"  {YELLOW}•{RESET} {item}")
            print()
        
        not_related = analysis.get("not_related_to_code", [])
        if not_related:
            print(f"{BOLD}{RED}⚠️  External Issue:{RESET}")
            for item in not_related:
                print(f"  {RED}•{RESET} {item}")
            print()
            return
        
        deletes = analysis.get("delete", [])
        if deletes:
            print(f"{BOLD}{RED}Delete:{RESET}")
            for item in deletes:
                line = item.get("line", "?")
                content = item.get("content", "").rstrip()
                print(f"  {RED}Line {line}:{RESET} {content}")
            print()
        
        adds = analysis.get("add", [])
        if adds:
            print(f"{BOLD}{GREEN}Add:{RESET}")
            for item in adds:
                line = item.get("line", "?")
                content = item.get("content", "").rstrip()
                print(f"  {GREEN}After line {line}:{RESET} {content}")
            print()
        
        print(f"{BOLD}{BLUE}=== END ==={RESET}\n")
    
    def _apply_fixes_interactive(self, analysis):
        """Ask user if they want to apply fixes."""
        if analysis.get("not_related_to_code") or (not analysis.get("delete") and not analysis.get("add")):
            return
        
        response = input("Apply fixes? (y/n) ")
        if response.lower() in ["y", "yes", ""]:
            self._apply_patches(analysis)
        else:
            print("Fixes not applied")
    
    def _apply_patches(self, analysis):
        """Apply the suggested fixes to the script."""
        with open(self.script_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        deletes = analysis.get("delete", [])
        for delete_item in sorted(deletes, key=lambda x: x.get("line", 0), reverse=True):
            line_no = delete_item.get("line", 0)
            if 1 <= line_no <= len(lines):
                lines.pop(line_no - 1)
        
        adds = analysis.get("add", [])
        for add_item in sorted(adds, key=lambda x: x.get("line", 0)):
            line_no = add_item.get("line", 0)
            content = add_item.get("content", "") + "\n"
            if 0 <= line_no <= len(lines):
                lines.insert(line_no, content)
        
        with open(self.script_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        print(f"{GREEN}✔ Script patched successfully!{RESET}")


if __name__ == "__main__":
    project_path = str(Path(__file__).resolve().parent)
    script_name = "examples/example_1.py"
    env_name = "venv"
    debugger = DebuggerAgent(project_path, env_name, script_name)
    debugger.run_debug()
