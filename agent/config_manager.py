"""
Module de gestion de la configuration.
Gère les paramètres du projet et de l'environnement.
"""
import json
from pathlib import Path
from typing import Dict, Optional

class ConfigManager:
    """Gère la configuration de l'agent de debugging."""
    
    def __init__(self, config_file: Path = Path("debug_agent_config.json")):
        """
        Initialise le gestionnaire de configuration.
        
        Args:
            config_file: Chemin du fichier de configuration
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """
        Charge la configuration depuis le fichier.
        
        Returns:
            Dictionnaire de configuration
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[v0] Error loading config: {e}")
                return self._get_default_config()
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """
        Retourne la configuration par défaut.
        
        Returns:
            Configuration par défaut
        """
        return {
            "project_path": "",
            "venv_name": "venv",
            "script_to_debug": "",
            "timeout": 30,
            "create_backups": True,
            "auto_apply_fixes": False
        }
    
    def save_config(self):
        """Sauvegarde la configuration dans le fichier."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            print(f"[v0] Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"[v0] Error saving config: {e}")
    
    def get(self, key: str, default=None):
        """
        Récupère une valeur de configuration.
        
        Args:
            key: Clé de configuration
            default: Valeur par défaut si la clé n'existe pas
        
        Returns:
            Valeur de configuration
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """
        Définit une valeur de configuration.
        
        Args:
            key: Clé de configuration
            value: Valeur à définir
        """
        self.config[key] = value
    
    def get_project_path(self) -> Optional[Path]:
        """Retourne le chemin du projet ou None."""
        path_str = self.config.get("project_path", "")
        if path_str:
            return Path(path_str)
        return None
    
    def get_venv_path(self) -> Optional[Path]:
        """Retourne le chemin de l'environnement virtuel ou None."""
        project_path = self.get_project_path()
        if project_path:
            venv_name = self.config.get("venv_name", "venv")
            return project_path / venv_name
        return None
    
    def get_script_path(self) -> Optional[Path]:
        """Retourne le chemin du script à débugger ou None."""
        project_path = self.get_project_path()
        script_name = self.config.get("script_to_debug", "")
        if project_path and script_name:
            return project_path / script_name
        return None
