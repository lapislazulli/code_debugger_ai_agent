"""
Détecte l'environnement du projet (Python, venvs, dépendances).
"""
import subprocess
import sys
from pathlib import Path


class EnvironmentDetector:
    def __init__(self, project_path=None):
        """Initialise le détecteur."""
        self.project_path = Path(project_path) if project_path else Path.cwd()
    
    def detect_all(self):
        """Détecte tous les éléments de l'environnement."""
        return {
            "python_version": self._detect_python(),
            "virtual_env": self._detect_venv(),
            "package_manager": self._detect_package_manager(),
            "requirements": self._detect_requirements(),
            "python_files": self._find_python_files()
        }
    
    def _detect_python(self):
        """Détecte la version Python."""
        return {
            "found": True,
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "executable": sys.executable
        }
    
    def _detect_venv(self):
        """Détecte les environnements virtuels."""
        venvs = []
        for venv_name in ['venv', '.venv', 'env', 'smart_debugger_env']:
            venv_path = self.project_path / venv_name
            if venv_path.exists():
                venvs.append({
                    "name": venv_name,
                    "path": str(venv_path),
                    "type": "venv",
                    "python_executable": str(venv_path / "bin" / "python")
                })
        
        return {
            "found": len(venvs) > 0,
            "venvs": venvs,
            "conda_envs": []
        }
    
    def _detect_package_manager(self):
        """Détecte les gestionnaires de paquets."""
        managers = []
        files = {}
        
        if (self.project_path / "requirements.txt").exists():
            managers.append("pip")
            files["requirements.txt"] = True
        if (self.project_path / "Pipfile").exists():
            managers.append("pipenv")
            files["Pipfile"] = True
        if (self.project_path / "pyproject.toml").exists():
            managers.append("poetry")
            files["pyproject.toml"] = True
        
        return {
            "found": len(managers) > 0,
            "managers": managers,
            "files": files
        }
    
    def _detect_requirements(self):
        """Détecte les dépendances."""
        req_path = self.project_path / "requirements.txt"
        if req_path.exists():
            with open(req_path, 'r') as f:
                packages = [line.strip() for line in f if line.strip()]
            return {
                "found": True,
                "count": len(packages),
                "packages": packages
            }
        return {"found": False, "count": 0, "packages": []}
    
    def _find_python_files(self):
        """Trouve tous les fichiers Python."""
        files = []
        for py_file in self.project_path.rglob("*.py"):
            if "venv" not in str(py_file) and "__pycache__" not in str(py_file):
                files.append(str(py_file.relative_to(self.project_path)))
        return sorted(files)
