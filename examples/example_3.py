# Example 3: TypeError
# This script will raise a TypeError
def add(a, b):
    return a + b

result = add("hello", 5)  # TypeError: can only concatenate str (not "int") to str
print(result)
