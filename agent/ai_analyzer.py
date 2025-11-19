"""
AI-powered error analysis using Groq.
Loads system context and user prompt from external files.
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, Any
from groq import Groq


class AIAnalyzer:
    """Analyzes Python errors using Groq AI with external prompt files."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the AI analyzer.
        
        Args:
            api_key: Groq API key (uses GROQ_API_KEY env if not provided)
            
        Raises:
            ValueError: If API key is not found
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
        
        self.system_prompt = self._load_file("context.txt")
        self.user_prompt_template = self._load_file("prompt.txt")
    
    def _load_file(self, filename: str) -> str:
        """Load content from a text file."""
        path = Path(filename)
        if not path.exists():
            return ""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def analyze(self, source_code: str, traceback: str) -> Dict[str, Any]:
        """Analyse une erreur et propose des corrections."""
        user_prompt = f"""CODE SOURCE:
{source_code}

ERREUR:
{traceback}

{self.user_prompt_template}"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # Extraire et parser le JSON
        json_str = re.search(r'\{.*\}', content, re.DOTALL)
        if json_str:
            result = json.loads(json_str.group(0))
        else:
            result = json.loads(content)
        
        # Formater la réponse
        return {
            "error_type": result.get("error_type", "Unknown"),
            "analysis": "\n".join(result.get("explanations", [])),
            "is_code_bug": len(result.get("delete", [])) > 0 or len(result.get("add", [])) > 0,
            "lines_to_delete": [{"line_number": item.get("line"), "content": item.get("content"), "explanation": ""} for item in result.get("delete", [])],
            "lines_to_add": [{"line_number": item.get("line"), "content": item.get("content"), "explanation": ""} for item in result.get("add", [])],
            "not_related_to_code": "\n".join(result.get("not_related_to_code", []))
        }
