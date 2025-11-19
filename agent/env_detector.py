"""
Module de détection automatique de l'environnement projet.
Détecte Python, venv, conda, requirements, etc.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class EnvironmentDetector:
    """Détecte automatiquement l'environnement d'un projet Python."""
    
    def __init__(self, project_path: Optional[Path] = None):
        """
        Initialise le détecteur.
        
        Args:
            project_path: Chemin du projet (défaut: répertoire courant)
        """
        self.project_path = project_path or Path.cwd()
    
    def detect_all(self) -> Dict:
        """
        Détecte tous les aspects de l'environnement.
        
        Returns:
            Dictionnaire complet avec toutes les détections
        """
        return {
            "project_path": str(self.project_path),
            "python_version": self.detect_python_version(),
            "virtual_env": self.detect_virtual_env(),
            "package_manager": self.detect_package_manager(),
            "python_files": self.find_python_files(),
            "requirements": self.detect_requirements(),
            "git_repo": self.is_git_repo()
        }
    
    def detect_python_version(self) -> Dict:
        """
        Détecte la version de Python utilisée.
        
        Returns:
            Informations sur Python
        """
        try:
            version = sys.version
            version_info = {
                "major": sys.version_info.major,
                "minor": sys.version_info.minor,
                "micro": sys.version_info.micro
            }
            executable = sys.executable
            
            return {
                "found": True,
                "version": f"{version_info['major']}.{version_info['minor']}.{version_info['micro']}",
                "version_info": version_info,
                "executable": executable,
                "full_version": version
            }
        except Exception as e:
            return {
                "found": False,
                "error": str(e)
            }
    
    def detect_virtual_env(self) -> Dict:
        """
        Détecte les environnements virtuels dans le projet.
        
        Returns:
            Informations sur les venv trouvés
        """
        venv_names = ["venv", ".venv", "env", ".env", "virtualenv"]
        conda_envs = []
        
        # Chercher venv/virtualenv
        found_venvs = []
        for venv_name in venv_names:
            venv_path = self.project_path / venv_name
            if venv_path.exists() and venv_path.is_dir():
                # Vérifier que c'est bien un venv
                python_bin = venv_path / "bin" / "python"
                python_exe = venv_path / "Scripts" / "python.exe"
                
                if python_bin.exists() or python_exe.exists():
                    found_venvs.append({
                        "name": venv_name,
                        "path": str(venv_path),
                        "type": "venv",
                        "python_executable": str(python_bin if python_bin.exists() else python_exe)
                    })
        
        # Détecter si on est dans un environnement conda
        is_conda = os.environ.get("CONDA_DEFAULT_ENV") is not None
        conda_env_name = os.environ.get("CONDA_DEFAULT_ENV", "")
        
        if is_conda:
            conda_envs.append({
                "name": conda_env_name,
                "type": "conda",
                "active": True
            })
        
        # Détecter l'environnement virtuel actif
        active_venv = None
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            active_venv = {
                "prefix": sys.prefix,
                "type": "conda" if is_conda else "venv"
            }
        
        return {
            "found": len(found_venvs) > 0 or len(conda_envs) > 0,
            "venvs": found_venvs,
            "conda_envs": conda_envs,
            "active_venv": active_venv,
            "is_conda": is_conda
        }
    
    def detect_package_manager(self) -> Dict:
        """
        Détecte les gestionnaires de paquets et fichiers de dépendances.
        
        Returns:
            Informations sur les gestionnaires trouvés
        """
        files = {
            "requirements.txt": (self.project_path / "requirements.txt").exists(),
            "setup.py": (self.project_path / "setup.py").exists(),
            "pyproject.toml": (self.project_path / "pyproject.toml").exists(),
            "Pipfile": (self.project_path / "Pipfile").exists(),
            "poetry.lock": (self.project_path / "poetry.lock").exists(),
            "environment.yml": (self.project_path / "environment.yml").exists()
        }
        
        detected = []
        if files["requirements.txt"]:
            detected.append("pip")
        if files["Pipfile"]:
            detected.append("pipenv")
        if files["poetry.lock"] or files["pyproject.toml"]:
            detected.append("poetry")
        if files["environment.yml"]:
            detected.append("conda")
        
        return {
            "found": len(detected) > 0,
            "managers": detected,
            "files": files
        }
    
    def find_python_files(self, max_depth: int = 3) -> List[str]:
        """
        Trouve tous les fichiers Python dans le projet.
        
        Args:
            max_depth: Profondeur maximale de recherche
        
        Returns:
            Liste des chemins relatifs des fichiers Python
        """
        python_files = []
        
        try:
            for py_file in self.project_path.rglob("*.py"):
                # Ignorer les venv et répertoires cachés
                parts = py_file.relative_to(self.project_path).parts
                if any(part.startswith('.') or part in ['venv', 'env', '__pycache__'] for part in parts):
                    continue
                
                # Vérifier la profondeur
                if len(parts) <= max_depth:
                    python_files.append(str(py_file.relative_to(self.project_path)))
        except Exception as e:
            print(f"Error finding Python files: {e}")
        
        return sorted(python_files)
    
    def detect_requirements(self) -> Dict:
        """
        Lit et analyse le fichier requirements.txt s'il existe.
        
        Returns:
            Liste des dépendances
        """
        req_file = self.project_path / "requirements.txt"
        
        if not req_file.exists():
            return {
                "found": False,
                "packages": []
            }
        
        try:
            with open(req_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            packages = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    packages.append(line)
            
            return {
                "found": True,
                "packages": packages,
                "count": len(packages)
            }
        except Exception as e:
            return {
                "found": True,
                "error": str(e),
                "packages": []
            }
    
    def is_git_repo(self) -> bool:
        """Vérifie si le projet est un dépôt Git."""
        return (self.project_path / ".git").exists()
    
    def get_python_executable(self) -> str:
        """
        Retourne le chemin vers l'exécutable Python à utiliser.
        Préfère le venv s'il existe, sinon utilise le Python système.
        
        Returns:
            Chemin vers l'exécutable Python
        """
        venv_info = self.detect_virtual_env()
        
        # Si un venv est trouvé, utiliser son Python
        if venv_info["found"] and venv_info["venvs"]:
            return venv_info["venvs"][0]["python_executable"]
        
        # Sinon utiliser le Python système
        return sys.executable
