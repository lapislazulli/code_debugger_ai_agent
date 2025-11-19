"""
Exemple de script avec une erreur d'import.
"""
import numpy as np  # numpy n'est probablement pas installé dans le venv

def main():
    arr = np.array([1, 2, 3, 4, 5])
    print(f"Array: {arr}")
    print(f"Mean: {np.mean(arr)}")

if __name__ == "__main__":
    main()
