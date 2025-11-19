"""
Module de patching de fichiers.
Applique les corrections proposées par l'IA sur les fichiers sources.
"""
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class FilePatcher:
    """Applique des corrections sur des fichiers Python."""
    
    def __init__(self, create_backup: bool = True):
        """
        Initialise le patcher.
        
        Args:
            create_backup: Si True, crée une sauvegarde avant modification
        """
        self.create_backup = create_backup
    
    def apply_corrections(self, file_path: Path, corrections: List[Dict]) -> Dict:
        """
        Applique une liste de corrections sur un fichier.
        
        Args:
            file_path: Chemin du fichier à corriger
            corrections: Liste des corrections au format:
                {
                    "line_number": int,
                    "old_code": str,
                    "new_code": str,
                    "explanation": str
                }
        
        Returns:
            Résultat de l'application avec succès/échec
        """
        if not file_path.exists():
            return {
                "success": False,
                "message": f"File not found: {file_path}",
                "applied_count": 0
            }
        
        # Créer une sauvegarde si demandé
        backup_path = None
        if self.create_backup:
            backup_path = self._create_backup(file_path)
            print(f"[v0] Backup created: {backup_path}")
        
        try:
            # Lire le contenu du fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Trier les corrections par numéro de ligne (ordre décroissant)
            # pour éviter les problèmes de décalage
            sorted_corrections = sorted(corrections, key=lambda x: x["line_number"], reverse=True)
            
            applied_count = 0
            failed_corrections = []
            
            # Appliquer chaque correction
            for correction in sorted_corrections:
                line_num = correction["line_number"]
                old_code = correction["old_code"]
                new_code = correction["new_code"]
                
                # Vérifier que le numéro de ligne est valide
                if line_num < 1 or line_num > len(lines):
                    failed_corrections.append({
                        "line": line_num,
                        "reason": f"Invalid line number (file has {len(lines)} lines)"
                    })
                    continue
                
                # Convertir en index 0-based
                line_index = line_num - 1
                current_line = lines[line_index].rstrip('\n')
                
                # Vérifier que la ligne correspond à old_code
                if current_line.strip() != old_code.strip():
                    failed_corrections.append({
                        "line": line_num,
                        "reason": f"Line content mismatch. Expected: '{old_code}', Got: '{current_line.strip()}'"
                    })
                    continue
                
                # Appliquer la correction en préservant l'indentation
                indent = len(current_line) - len(current_line.lstrip())
                lines[line_index] = ' ' * indent + new_code + '\n'
                applied_count += 1
                
                print(f"[v0] Applied correction at line {line_num}")
            
            # Écrire le fichier corrigé
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            if failed_corrections:
                print(f"[v0] Warning: {len(failed_corrections)} corrections failed")
                for fail in failed_corrections:
                    print(f"  Line {fail['line']}: {fail['reason']}")
            
            return {
                "success": True,
                "message": f"Applied {applied_count}/{len(corrections)} corrections",
                "applied_count": applied_count,
                "failed_corrections": failed_corrections,
                "backup_path": backup_path
            }
            
        except Exception as e:
            # En cas d'erreur, restaurer la sauvegarde si elle existe
            if backup_path and backup_path.exists():
                print(f"[v0] Error occurred, restoring backup...")
                shutil.copy2(backup_path, file_path)
            
            return {
                "success": False,
                "message": f"Error applying corrections: {str(e)}",
                "applied_count": 0,
                "backup_path": backup_path
            }
    
    def _create_backup(self, file_path: Path) -> Path:
        """
        Crée une copie de sauvegarde du fichier.
        
        Args:
            file_path: Chemin du fichier à sauvegarder
        
        Returns:
            Chemin du fichier de sauvegarde
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = file_path.parent / ".backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}.backup"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def restore_backup(self, file_path: Path, backup_path: Path) -> bool:
        """
        Restaure un fichier depuis une sauvegarde.
        
        Args:
            file_path: Chemin du fichier à restaurer
            backup_path: Chemin de la sauvegarde
        
        Returns:
            True si la restauration a réussi
        """
        try:
            if not backup_path.exists():
                print(f"[v0] Backup not found: {backup_path}")
                return False
            
            shutil.copy2(backup_path, file_path)
            print(f"[v0] Restored {file_path} from backup")
            return True
            
        except Exception as e:
            print(f"[v0] Error restoring backup: {e}")
            return False
