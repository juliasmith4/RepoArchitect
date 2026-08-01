import ast

from app.analyzer.parsing.visitor import PythonAstVisitor


source = """
import os
import pandas as pd
from pathlib import Path
from typing import Any as Anything


class Analyzer:
    \"""Analyze a repository.\"""

    def run(self, path: Path, *, strict: bool = False) -> bool:
        \"""Run the analyzer.\"""
        return True


async def main(name: str = "RepoArchitect") -> None:
    pass
"""


tree = ast.parse(source)

visitor = PythonAstVisitor()
visitor.visit(tree)

print("Imports:")
for imported in visitor.imports:
    print(imported)

print("\nFunctions:")
for function in visitor.functions:
    print(function)

print("\nClasses:")
for parsed_class in visitor.classes:
    print(parsed_class)

    