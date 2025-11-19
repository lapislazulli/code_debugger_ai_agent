"""
Script d'exemple avec des erreurs intentionnelles pour tester l'agent.
"""

def calculate_average(numbers):
    """Calcule la moyenne d'une liste de nombres."""
    total = sum(numbers)
    count = len(number)  # Erreur: 'number' n'existe pas, devrait être 'numbers'
    return total / count

def greet_user(name):
    """Salue l'utilisateur."""
    message = "Bonjour, " + name + "!"
    print(mesage)  # Erreur: 'mesage' mal orthographié, devrait être 'message'

def main():
    # Test de la fonction
    nums = [10, 20, 30, 40, 50]
    avg = calculate_average(nums)
    print(f"Moyenne: {avg}")
    
    greet_user("Alice")

if __name__ == "__main__":
    main()
