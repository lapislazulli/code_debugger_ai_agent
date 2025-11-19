"""
Main entry point - AI-powered Python debugger.
Executes scripts, analyzes errors with Groq AI, and applies fixes.

Usage:
    python main.py examples/example_1.py
"""
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from executor import execute_script, get_numbered_source
from ai_analyzer import AIAnalyzer
from file_patcher import FilePatcher
from config import BOLD, BLUE, RED, GREEN, YELLOW, RESET

load_dotenv()


def debug_script(script_path: Path) -> Optional[dict]:
    """Debug a Python script and optionally apply AI-suggested fixes."""
    if not script_path.exists():
        print(f"{RED}Error: {script_path} not found{RESET}")
        return None
    
    # Step 1: Execute script
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"DEBUGGING: {script_path.name}")
    print(f"{'='*70}{RESET}\n")
    
    print(f"{YELLOW}Step 1: Executing script...{RESET}\n")
    execution = execute_script(script_path)
    
    if execution["success"]:
        print(f"{GREEN}✓ Success - no errors!{RESET}\n")
        if execution["stdout"]:
            print("Output:")
            print(execution["stdout"])
        return execution
    
    print(f"{RED}✗ Error detected:{RESET}\n")
    print(execution["stderr"])
    print()
    
    # Step 2: Analyze with AI
    print(f"{YELLOW}Step 2: Analyzing with AI...{RESET}\n")
    
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print(f"{RED}Error: GROQ_API_KEY not set{RESET}")
        return None
    
    try:
        analyzer = AIAnalyzer(groq_key)
        numbered_source = get_numbered_source(script_path)
        analysis = analyzer.analyze(numbered_source, execution["traceback"])
        
        # Display results
        print(f"{BOLD}Error Type: {analysis['error_type']}{RESET}")
        print(f"{BOLD}Analysis:{RESET}")
        print(analysis["analysis"])
        print()
        
        if analysis["is_code_bug"]:
            if analysis.get("lines_to_delete"):
                print(f"{RED}Lines to remove:{RESET}")
                for item in analysis["lines_to_delete"]:
                    print(f"  Line {item['line_number']}: {item['content']}")
                print()
            
            if analysis.get("lines_to_add"):
                print(f"{GREEN}Lines to add:{RESET}")
                for item in analysis["lines_to_add"]:
                    print(f"  Line {item['line_number']}: {item['content']}")
                print()
            
            # Ask to apply fixes
            response = input(f"{BOLD}Apply fixes? (y/n): {RESET}").strip().lower()
            if response in ['y', 'yes', '']:
                patcher = FilePatcher()
                corrections = []
                
                for delete in analysis.get("lines_to_delete", []):
                    corrections.append({
                        "line_number": delete["line_number"],
                        "new_code": ""
                    })
                
                for add in analysis.get("lines_to_add", []):
                    corrections.append({
                        "line_number": add["line_number"],
                        "new_code": add["content"]
                    })
                
                fix_result = patcher.apply_corrections(script_path, corrections)
                if fix_result["success"]:
                    print(f"{GREEN}✓ Applied {fix_result['applied_count']} correction(s){RESET}")
                    print(f"  Backup: {fix_result['backup_path']}")
                else:
                    print(f"{RED}✗ Failed to apply fixes{RESET}")
        else:
            print(f"{YELLOW}⚠ Issue is external to code:{RESET}")
            print(analysis["not_related_to_code"])
    
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        return None


def main():
    if len(sys.argv) < 2:
        print(f"{BOLD}{BLUE}Usage: python main.py <script_path>{RESET}")
        print(f"Example: python main.py examples/example_1.py")
        return
    
    script_path = Path(sys.argv[1])
    debug_script(script_path)


if __name__ == "__main__":
    main()
