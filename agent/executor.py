"""
Module d'exécution de scripts Python.
Gère l'exécution dans un environnement virtuel et la capture des erreurs.
"""
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


def run_script(*args) -> Tuple[str, str]:
    """
    Exécute un script Python et retourne stdout/stderr.
    
    Cette fonction suit exactement l'approche du professeur:
    - Simple appel subprocess.run()
    - Capture de stdout et stderr
    - Retour d'un tuple (stdout, stderr)
    
    Args:
        *args: Arguments pour subprocess (ex: 'python', 'script.py')
    
    Returns:
        Tuple (stdout, stderr)
    """
    result = subprocess.run(
        args,
        capture_output=True,
        text=True
    )
    return result.stdout, result.stderr


class ScriptExecutor:
    """Exécute des scripts Python et capture leurs sorties."""
    
    def __init__(self, venv_path: Optional[Path] = None, python_cmd: str = "python3"):
        """
        Initialise l'exécuteur.
        
        Args:
            venv_path: Chemin vers l'environnement virtuel (optionnel)
            python_cmd: Commande Python à utiliser (python, python3, etc.)
        """
        self.venv_path = venv_path
        self.python_cmd = python_cmd
        self.python_executable = self._find_python_executable()
    
    def _find_python_executable(self) -> str:
        """
        Trouve l'exécutable Python à utiliser.
        
        Returns:
            Chemin vers l'exécutable Python
        """
        if self.venv_path and self.venv_path.exists():
            # Chercher dans l'environnement virtuel
            if (self.venv_path / "bin" / "python").exists():
                return str(self.venv_path / "bin" / "python")
            elif (self.venv_path / "Scripts" / "python.exe").exists():
                return str(self.venv_path / "Scripts" / "python.exe")
        
        # Utiliser le Python système par défaut
        return self.python_cmd
    
    def execute_script(self, script_path: Path, timeout: int = 30) -> Dict[str, any]:
        """
        Exécute un script Python et capture ses sorties.
        
        Args:
            script_path: Chemin vers le script à exécuter
            timeout: Timeout en secondes (défaut: 30)
        
        Returns:
            Dictionnaire contenant:
                - success: bool indiquant si l'exécution a réussi
                - stdout: sortie standard
                - stderr: sortie d'erreur
                - return_code: code de retour du processus
                - error_type: type d'erreur détecté (si applicable)
        """
        print(f"[v0] Executing script: {script_path}")
        print(f"[v0] Using Python: {self.python_executable}")
        
        if not script_path.exists():
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Script not found: {script_path}",
                "return_code": -1,
                "error_type": "FileNotFoundError"
            }
        
        try:
            # Exécuter le script
            result = subprocess.run(
                [self.python_executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=script_path.parent  # Exécuter dans le répertoire du script
            )
            
            success = result.returncode == 0
            
            # Détecter le type d'erreur si applicable
            error_type = None
            if not success and result.stderr:
                error_type = self._detect_error_type(result.stderr)
            
            print(f"[v0] Execution completed with return code: {result.returncode}")
            
            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "error_type": error_type
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Script execution timed out after {timeout} seconds",
                "return_code": -1,
                "error_type": "TimeoutError"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "error_type": type(e).__name__
            }
    
    def _detect_error_type(self, stderr: str) -> str:
        """
        Détecte le type d'erreur à partir du stderr.
        
        Args:
            stderr: Sortie d'erreur
        
        Returns:
            Type d'erreur détecté
        """
        error_keywords = {
            "SyntaxError": "SyntaxError",
            "NameError": "NameError",
            "TypeError": "TypeError",
            "ValueError": "ValueError",
            "AttributeError": "AttributeError",
            "ImportError": "ImportError",
            "ModuleNotFoundError": "ModuleNotFoundError",
            "IndexError": "IndexError",
            "KeyError": "KeyError",
            "ZeroDivisionError": "ZeroDivisionError",
            "FileNotFoundError": "FileNotFoundError",
            "IndentationError": "IndentationError"
        }
        
        for keyword, error_type in error_keywords.items():
            if keyword in stderr:
                return error_type
        
        return "UnknownError"
    
    def validate_venv(self) -> Tuple[bool, str]:
        """
        Valide que l'environnement virtuel est correctement configuré.
        
        Returns:
            Tuple (is_valid, message)
        """
        if not self.venv_path:
            return False, "No virtual environment specified"
        
        if not self.venv_path.exists():
            return False, f"Virtual environment not found: {self.venv_path}"
        
        # Vérifier la présence de l'exécutable Python
        python_bin = self.venv_path / "bin" / "python"
        python_exe = self.venv_path / "Scripts" / "python.exe"
        
        if not python_bin.exists() and not python_exe.exists():
            return False, "Python executable not found in virtual environment"
        
        return True, "Virtual environment is valid"
    
    def execute(self, script_path: Path) -> dict:
        """
        Exécute un script et retourne les résultats.
        
        Args:
            script_path: Chemin vers le script à exécuter
        
        Returns:
            Dictionnaire avec stdout, stderr et success
        """
        if not script_path.exists():
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Script not found: {script_path}",
                "traceback": f"FileNotFoundError: {script_path}"
            }
        
        stdout, stderr = run_script(self.python_cmd, str(script_path))
        
        # Déterminer le succès
        success = len(stderr) == 0
        
        return {
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "traceback": stderr if not success else None
        }
    
    def read_source_code(self, script_path: Path) -> str:
        """
        Lit le code source d'un script.
        
        Args:
            script_path: Chemin du script
        
        Returns:
            Contenu du fichier
        """
        with open(script_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_numbered_source(self, script_path: Path) -> str:
        """
        Retourne le code source avec numéros de ligne.
        
        Args:
            script_path: Chemin du script
        
        Returns:
            Code numéroté
        """
        code = self.read_source_code(script_path)
        lines = code.split('\n')
        return '\n'.join([f"{i+1:3d} | {line}" for i, line in enumerate(lines)])
