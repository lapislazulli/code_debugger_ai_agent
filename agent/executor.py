"""
Executes Python scripts and captures output and errors.
Provides source code with line numbers for AI analysis.
"""
import subprocess
from pathlib import Path
from typing import Dict, Any


def execute_script(script_path: Path) -> Dict[str, Any]:
    """
    Execute a Python script and capture output.
    
    Args:
        script_path: Path to the Python script
        
    Returns:
        Dict with success status, stdout, stderr, and traceback
    """
    result = subprocess.run(
        ["python", str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent
    )
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "traceback": result.stderr
    }


def get_numbered_source(script_path: Path) -> str:
    """
    Read source code with line numbers.
    
    Args:
        script_path: Path to the Python file
        
    Returns:
        Source code formatted with line numbers
    """
    with open(script_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return ''.join([f"{i+1:3d} | {line}" for i, line in enumerate(lines)])
