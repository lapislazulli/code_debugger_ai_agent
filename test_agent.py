"""
Script de test pour démontrer le fonctionnement de l'agent.
"""
import os
from pathlib import Path
from agent.main import DebugAgent


def test_agent():
    """Teste l'agent de debugging sur les exemples."""
    print("="*70)
    print("TEST DE L'AGENT DE DEBUGGING AUTOMATIQUE")
    print("="*70)
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("\n⚠️  GROQ_API_KEY non définie")
        print("Pour tester avec l'IA, définissez votre clé:")
        print("  export GROQ_API_KEY='votre-clé'")
        print("\nObtenez une clé gratuite sur: https://console.groq.com/")
        return
    
    try:
        agent = DebugAgent(api_key)
    except ValueError as e:
        print(f"\n❌ Erreur: {e}")
        return
    
    # Tests sur différents scripts
    test_scripts = [
        ("examples/buggy_script.py", "Script avec erreurs NameError"),
        ("examples/syntax_error.py", "Script avec erreur de syntaxe"),
        ("examples/correct_script.py", "Script correct sans erreurs")
    ]
    
    results = []
    
    for script_path, description in test_scripts:
        print(f"\n{'='*70}")
        print(f"TEST: {description}")
        print(f"{'='*70}")
        
        result = agent.debug(script_path)
        results.append((script_path, result))
        
        if result.get("needs_fixing"):
            print("\n>>> Des corrections sont proposées.")
            print(">>> En mode test automatique, les corrections ne sont pas appliquées.")
            print(">>> Utilisez agent.apply_fixes(result) pour appliquer.")
    
    # Résumé
    print(f"\n{'='*70}")
    print("RÉSUMÉ DES TESTS")
    print(f"{'='*70}")
    
    for script_path, result in results:
        script_name = Path(script_path).name
        status = "✅ OK" if result["success"] else "❌ ERREUR"
        needs_fix = "Corrections proposées" if result.get("needs_fixing") else "Aucune correction"
        print(f"{status} | {script_name:25} | {needs_fix}")
    
    print("\n✅ Tests terminés avec succès!")


def demo_auto_fix():
    """Démo avec application automatique des corrections."""
    print("\n" + "="*70)
    print("DÉMONSTRATION: Correction Automatique")
    print("="*70 + "\n")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY non définie")
        return
    
    agent = DebugAgent(api_key)
    
    # Tester sur un script avec erreurs
    result = agent.auto_fix("examples/buggy_script.py")
    
    if result.get("fix_result", {}).get("success"):
        print("\n🎉 Script corrigé avec succès!")
    elif not result.get("needs_fixing"):
        print("\n✅ Aucune correction nécessaire!")
    else:
        print("\n⚠️  Corrections proposées mais non appliquées")


if __name__ == "__main__":
    test_agent()
    
    # Décommenter pour tester la correction automatique
    # demo_auto_fix()
