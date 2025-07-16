# Contributor Guidelines

This repository contains a Blender add-on. Please adhere to the following guidelines when making changes.

## Coding Practices
- Use Python 3 syntax throughout.
- Follow PEP8 style conventions with a focus on readability.
- Keep modules small and focused on a single responsibility to encourage a modular code base.
- Reuse helper logic via functions or classes in `utils.py` whenever possible.
- Use or create utils.py for helper functions related only to particular workflow, and cant be reused as pure-python functions. 

## Naming Conventions
- File names use `snake_case` (e.g. `example_module.py`).
- Class names use `CamelCase` and functions use `snake_case`.



## Project Overview
- The `Structure` file in the repository root provides a high-level overview of the directories contained in this project.

