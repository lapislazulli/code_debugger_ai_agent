"""
Script sans erreurs pour tester que l'agent détecte les scripts corrects.
"""

def fibonacci(n):
    """Génère les n premiers nombres de Fibonacci."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

def main():
    n = 10
    sequence = fibonacci(n)
    print(f"Les {n} premiers nombres de Fibonacci:")
    print(sequence)

if __name__ == "__main__":
    main()
