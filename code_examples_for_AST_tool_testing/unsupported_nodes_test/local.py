import os
import sys
from math import sqrt


class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        print(f"Hello, I'm {self.name}, {self.age} years old.")
