"""
Module d'analyse IA - Interface avec Groq pour obtenir des corrections.
"""
import json
import os
from typing import Dict, List, Optional
from groq import Groq
import re



class AIAnalyzer:
    """
    Analyseur IA qui communique avec Groq pour obtenir des corrections.
    
    Retourne un JSON structuré avec:
    - lines_to_delete: Liste de {line_number, content, explanation}
    - lines_to_add: Liste de {line_number, content, explanation}
    - pedagogical_explanation: Explication en français
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialise l'analyseur IA.
        
        Args:
            api_key: Clé API Groq (utilise GROQ_API_KEY si non fournie)
            model: Modèle à utiliser
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not provided and GROQ_API_KEY not set")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
    
    def analyze_error(self, code: str, error: str, file_path: str) -> Dict:
        """
        Analyse une erreur et propose des corrections.
        
        Args:
            code: Code source complet
            error: Message d'erreur
            file_path: Chemin du fichier
        
        Returns:
            Dictionnaire contenant l'analyse et les corrections
        """
        print(f"[v0] Analyzing error with AI model: {self.model}")
        
        # Construire le prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(code, error, file_path)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            print(f"[v0] Received response from Groq AI")
            
            corrections_json = self._extract_json(response_text)
            
            validated = self._validate_corrections(corrections_json)
            
            return validated
            
        except Exception as e:
            print(f"[v0] Error calling Groq API: {e}")
            return {
                "error_type": "API Error",
                "analysis": f"Failed to analyze error: {str(e)}",
                "is_code_fixable": False,
                "corrections": []
            }
    
    def analyze(self, source_code: str, traceback: str) -> Dict:
        """
        Analyse une erreur et propose des corrections.
        
        Args:
            source_code: Code source avec numéros de lignes
            traceback: Stack trace de l'erreur
        
        Returns:
            JSON avec les corrections proposées
        """
        system_prompt = """Tu es un agent spécialisé dans la correction de scripts Python.

Tu reçois:
1. Le contenu complet d'un script Python, avec les numéros de lignes
2. Le message d'erreur ou traceback généré lors de l'exécution

OBJECTIF:
- Déterminer si le bug provient du code lui-même ou d'un problème externe (réseau, API, dépendances, permissions, environnement, etc.)

- Si le bug provient du code:
  * Ne JAMAIS réécrire le script entier
  * Proposer uniquement:
    - Les lignes exactes à supprimer (avec leur numéro + leur contenu exact)
    - Les lignes à ajouter (avec le numéro où les insérer + le contenu exact)
  * Fournir des explications pédagogiques en français sur la nature du bug et les corrections proposées

- Si le bug ne provient PAS du code:
  * N'AJOUTER AUCUNE suppression, NI ajout
  * Expliquer pédagogiquement le problème externe
  * Donner des recommandations dans la section "not_related_to_code"

RÉPONDS TOUJOURS EN JSON VALIDE:
{
    "is_code_bug": true/false,
    "error_type": "SyntaxError/NameError/etc.",
    "analysis": "Explication détaillée en français",
    "lines_to_delete": [
        {"line_number": 5, "content": "print(x)", "explanation": "Variable x non définie"}
    ],
    "lines_to_add": [
        {"line_number": 4, "content": "x = 10", "explanation": "Initialisation de x"}
    ],
    "not_related_to_code": "Explication si problème externe (vide si is_code_bug=true)"
}"""
        
        user_prompt = f"""CODE SOURCE:
{source_code}

ERREUR / TRACEBACK:
{traceback}

Analyse cette erreur et propose des corrections selon les règles."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Extraire le JSON
            json_match = re.search(r'\`\`\`json\s*(\{.*?\})\s*\`\`\`', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                json_str = json_match.group(0) if json_match else content
            
            result = json.loads(json_str)
            return self._validate_response(result)
            
        except Exception as e:
            return {
                "is_code_bug": False,
                "error_type": "AI_ERROR",
                "analysis": f"Erreur lors de l'analyse: {str(e)}",
                "lines_to_delete": [],
                "lines_to_add": [],
                "not_related_to_code": f"Erreur API: {str(e)}"
            }
    
    def _build_system_prompt(self) -> str:
        return """Tu es un expert en debugging Python. Ton rôle est d'analyser les erreurs d'exécution et de proposer des corrections précises.

RÈGLES STRICTES:
1. Analyse uniquement les erreurs d'exécution (runtime errors)
2. Propose des corrections minimales et précises
3. Réponds TOUJOURS en JSON valide avec cette structure exacte:
{
    "error_type": "type d'erreur (SyntaxError, NameError, etc.)",
    "analysis": "analyse détaillée de l'erreur en français",
    "is_code_fixable": true/false,
    "corrections": [
        {
            "line_number": numéro de ligne (int),
            "old_code": "code exact à remplacer (string)",
            "new_code": "nouveau code (string)",
            "explanation": "explication claire du changement"
        }
    ]
}

4. Si is_code_fixable est false, corrections doit être une liste vide []
5. Si l'erreur nécessite une action hors code (installer package, créer fichier), indique-le dans analysis et mets is_code_fixable à false
6. Les numéros de ligne doivent correspondre exactement au code fourni
7. Le old_code doit correspondre EXACTEMENT à la ligne dans le code (sans les espaces de début)
8. Ne propose que des modifications nécessaires pour corriger l'erreur"""
    
    def _build_user_prompt(self, code: str, error: str, file_path: str) -> str:
        code_lines = code.split('\n')
        numbered_code = '\n'.join([f"{i+1:3d} | {line}" for i, line in enumerate(code_lines)])
        
        return f"""Analyse cette erreur Python et propose des corrections.

FICHIER: {file_path}

CODE SOURCE (avec numéros de ligne):
{numbered_code}

ERREUR:
{error}

REMARQUES:
- Fournis une analyse détaillée de l'erreur en français.
- Propose des corrections minimales et précises.
- Réponds en JSON valide avec la structure exacte indiquée dans les règles.
- Si l'erreur nécessite une action hors code, indique-le dans l'analyse et mets is_code_fixable à false.
- Les numéros de ligne doivent correspondre exactement au code fourni.
- Le old_code doit correspondre EXACTEMENT à la ligne dans le code (sans les espaces de début).
- Ne propose que des modifications nécessaires pour corriger l'erreur."""
    
    def _extract_json(self, response_text: str) -> Dict:
        import re
        
        json_match = re.search(r'\`\`\`json\s*(\{.*?\})\s*\`\`\`', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"[v0] Failed to parse JSON: {e}")
            print(f"[v0] Response was: {response_text[:500]}")
            raise ValueError(f"Invalid JSON response from AI: {e}")
    
    def _validate_corrections(self, corrections_json: Dict) -> Dict:
        required_fields = ["error_type", "analysis", "is_code_fixable", "corrections"]
        
        for field in required_fields:
            if field not in corrections_json:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(corrections_json["error_type"], str):
            raise ValueError("error_type must be a string")
        
        if not isinstance(corrections_json["analysis"], str):
            raise ValueError("analysis must be a string")
        
        if not isinstance(corrections_json["is_code_fixable"], bool):
            raise ValueError("is_code_fixable must be a boolean")
        
        if not isinstance(corrections_json["corrections"], list):
            raise ValueError("corrections must be a list")
        
        for i, correction in enumerate(corrections_json["corrections"]):
            if not isinstance(correction, dict):
                raise ValueError(f"Correction {i} must be a dictionary")
            
            required_correction_fields = ["line_number", "old_code", "new_code", "explanation"]
            for field in required_correction_fields:
                if field not in correction:
                    raise ValueError(f"Correction {i} missing field: {field}")
            
            if not isinstance(correction["line_number"], int):
                raise ValueError(f"Correction {i} line_number must be an integer")
            
            if correction["line_number"] <= 0:
                raise ValueError(f"Correction {i} line_number must be positive")
        
        print(f"[v0] Validated {len(corrections_json['corrections'])} corrections")
        return corrections_json
    
    def _validate_response(self, response: Dict) -> Dict:
        """Valide et normalise la réponse de l'IA."""
        required = ["is_code_bug", "error_type", "analysis"]
        for field in required:
            if field not in response:
                response[field] = "" if field != "is_code_bug" else False
        
        if "lines_to_delete" not in response:
            response["lines_to_delete"] = []
        if "lines_to_add" not in response:
            response["lines_to_add"] = []
        if "not_related_to_code" not in response:
            response["not_related_to_code"] = ""
        
        return response
