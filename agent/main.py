"""
Agent de debugging automatique - Architecture simplifiée.

Flow:
1. Exécuter le script bugué (Executor)
2. Envoyer code source + traceback à l'IA (AIAnalyzer)
3. Recevoir JSON avec lignes à supprimer/ajouter
4. Appliquer les corrections (FilePatcher)
"""
import os
from pathlib import Path
from typing import Dict, Optional
from agent.executor import ScriptExecutor
from agent.ai_analyzer import AIAnalyzer
from agent.file_patcher import FilePatcher
from dotenv import load_dotenv
load_dotenv()



class DebugAgent:
    """Agent de debugging automatique."""
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Initialise l'agent.
        
        Args:
            groq_api_key: Clé API Groq (ou utilise GROQ_API_KEY)
        """
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY required")
        
        self.executor = ScriptExecutor()
        self.analyzer = AIAnalyzer(api_key)
        self.patcher = FilePatcher(create_backup=True)
    
    def debug(self, script_path: str) -> Dict:
        """
        Débugge un script: exécute → analyse → propose corrections.
        
        Args:
            script_path: Chemin vers le script à débugger
        
        Returns:
            Résultats complets du debugging
        """
        script = Path(script_path)
        
        if not script.exists():
            return {
                "success": False,
                "error": f"Script introuvable: {script_path}"
            }
        
        print(f"\n{'='*70}")
        print(f"DEBUGGING: {script.name}")
        print(f"{'='*70}\n")
        
        # ÉTAPE 1: Exécuter le script bugué
        print("📍 Étape 1: Exécution du script...\n")
        execution = self.executor.execute(script)
        
        if execution["success"]:
            print("✅ Script exécuté avec succès - aucune erreur!\n")
            if execution["stdout"]:
                print("Sortie:")
                print(execution["stdout"])
            return {
                "success": True,
                "needs_fixing": False,
                "execution": execution
            }
        
        print("❌ Erreur détectée:\n")
        print(execution["stderr"])
        print()
        
        # ÉTAPE 2: Lire le code source avec numéros de ligne
        print("📍 Étape 2: Lecture du code source...\n")
        numbered_source = self.executor.get_numbered_source(script)
        
        # ÉTAPE 3: Envoyer à l'IA pour analyse
        print("📍 Étape 3: Analyse avec Groq AI (Llama 3.3 70B)...\n")
        analysis = self.analyzer.analyze(numbered_source, execution["traceback"])
        
        # Afficher l'analyse
        print(f"Type d'erreur: {analysis['error_type']}")
        print(f"Bug dans le code: {'Oui' if analysis['is_code_bug'] else 'Non'}\n")
        print(f"📝 Analyse:\n{analysis['analysis']}\n")
        
        if not analysis["is_code_bug"]:
            print("⚠️  Problème externe au code:")
            print(analysis["not_related_to_code"])
            print()
        elif analysis["lines_to_delete"] or analysis["lines_to_add"]:
            print("🔧 Corrections proposées:\n")
            
            for item in analysis["lines_to_delete"]:
                print(f"  ❌ Ligne {item['line_number']}: {item['content']}")
                print(f"     → {item['explanation']}\n")
            
            for item in analysis["lines_to_add"]:
                print(f"  ✅ Ligne {item['line_number']}: {item['content']}")
                print(f"     → {item['explanation']}\n")
        
        return {
            "success": True,
            "needs_fixing": analysis["is_code_bug"],
            "execution": execution,
            "analysis": analysis,
            "script_path": script
        }
    
    def apply_fixes(self, debug_result: Dict) -> Dict:
        """
        Applique les corrections proposées.
        
        Args:
            debug_result: Résultat de debug()
        
        Returns:
            Résultat de l'application
        """
        if not debug_result.get("needs_fixing"):
            return {
                "success": False,
                "message": "Aucune correction à appliquer"
            }
        
        analysis = debug_result["analysis"]
        script = debug_result["script_path"]
        
        corrections = []
        
        # D'abord les suppressions/modifications
        for delete in analysis.get("lines_to_delete", []):
            corrections.append({
                "line_number": delete["line_number"],
                "old_code": delete["content"],
                "new_code": "",  # Suppression = ligne vide
                "explanation": delete["explanation"]
            })
        
        # Puis les ajouts
        for add in analysis.get("lines_to_add", []):
            # Trouver la ligne actuelle pour la remplacer
            corrections.append({
                "line_number": add["line_number"],
                "old_code": "",  # Ajout = pas d'ancienne ligne
                "new_code": add["content"],
                "explanation": add["explanation"]
            })
        
        if not corrections:
            return {
                "success": False,
                "message": "Aucune correction à appliquer"
            }
        
        print(f"\n{'='*70}")
        print(f"APPLICATION DES CORRECTIONS")
        print(f"{'='*70}\n")
        
        result = self.patcher.apply_corrections(script, corrections)
        
        if result["success"]:
            print(f"\n✅ {result['applied_count']} correction(s) appliquée(s)")
            if result.get("backup_path"):
                print(f"💾 Sauvegarde: {result['backup_path']}")
        else:
            print(f"\n❌ Échec: {result['message']}")
        
        return result
    
    def auto_fix(self, script_path: str) -> Dict:
        """
        Débugge et corrige automatiquement un script.
        
        Args:
            script_path: Chemin du script
        
        Returns:
            Résultats complets
        """
        # Débugger
        result = self.debug(script_path)
        
        if not result["success"]:
            return result
        
        if not result.get("needs_fixing"):
            return result
        
        # Appliquer automatiquement
        fix_result = self.apply_fixes(result)
        result["fix_result"] = fix_result
        
        # Ré-exécuter pour vérifier
        if fix_result.get("success"):
            print(f"\n{'='*70}")
            print("VÉRIFICATION: Ré-exécution du script corrigé...")
            print(f"{'='*70}\n")
            
            verification = self.executor.execute(result["script_path"])
            result["verification"] = verification
            
            if verification["success"]:
                print("✅ Script corrigé fonctionne parfaitement!")
                if verification["stdout"]:
                    print("\nSortie:")
                    print(verification["stdout"])
            else:
                print("⚠️  Le script contient encore des erreurs:")
                print(verification["stderr"])
        
        return result


def main():
    """Point d'entrée principal."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m agent.main <script_path>")
        print("\nExemple:")
        print("  python -m agent.main examples/buggy_script.py")
        sys.exit(1)
    
    script_path = sys.argv[1]
    
    # Créer l'agent
    try:
        agent = DebugAgent()
    except ValueError as e:
        print(f"Erreur: {e}")
        print("\nDéfinissez votre clé API Groq:")
        print("  export GROQ_API_KEY='votre-clé'")
        sys.exit(1)
    
    # Débugger
    result = agent.debug(script_path)
    
    if result["success"] and result.get("needs_fixing"):
        response = input("\n❓ Appliquer les corrections? (o/n): ")
        if response.lower() in ['o', 'oui', 'y', 'yes']:
            agent.apply_fixes(result)


if __name__ == "__main__":
    main()
