import sys
import json
from math import ceil


class Student():
    def __init__(self, name, age, grade):
        super().__init__(name, age)
        self.grade = grade

    def greet(self):
        print(f"I'm {self.name}, {self.age} years old, in grade {self.grade}.")
