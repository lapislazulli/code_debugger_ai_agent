# Example 5: AttributeError
# This script will raise an AttributeError
class Person:
    def __init__(self, name):
        self.name = name

person = Person("Alice")
print(person.age)  # AttributeError: 'Person' object has no attribute 'age'
