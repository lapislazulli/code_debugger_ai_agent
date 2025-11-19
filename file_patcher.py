"""
Applique les corrections aux fichiers.
"""
from pathlib import Path
from shutil import copy


class FilePatcher:
    def __init__(self):
        """Initialise le patcher."""
        pass
    
    def apply_corrections(self, script_path, corrections):
        """Applique les corrections au fichier."""
        script = Path(script_path)
        
        # Créer une sauvegarde
        backup_path = script.with_suffix('.py.bak')
        copy(script, backup_path)
        
        # Lire le fichier
        with open(script, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Appliquer les corrections (en ordre inverse pour éviter les décalages)
        for correction in sorted(corrections, key=lambda x: x['line_number'], reverse=True):
            line_num = correction['line_number'] - 1
            if 0 <= line_num < len(lines):
                lines[line_num] = correction['new_code'] + '\n'
        
        # Écrire le fichier
        with open(script, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return {
            "success": True,
            "applied_count": len(corrections),
            "backup_path": str(backup_path)
        }
