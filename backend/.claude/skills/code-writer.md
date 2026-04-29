---
name: python-code-writer
description: Generate codes for project
---

Generate code fits logic of the project

1. **Install environment**: Install uv if not already exists, search for requirements.txt in root directory, install with `uv pip install -r requirements.txt`
2. **Codebase inspect**: Inspect structure of full code base, identify which function module need code writing according to instruction
3. **Instruction breakdown**: Verify human instruction, if scope is too large to handle at once, break down to smaller generation or modification sections
4. **Requirement breakdown**: Break down development goal, execute order as below, skip if not required
   1. Create database
   2. modify database
   3. Create/update CRUD logic
   4. Generate API schemas
   5. Assemble API schema and CRUD logic to make a fully functional API
   6. Evaluate API
   7. Others
5. **Restrictions**: Only use libraries in project environment, ask for human for additional package if required
6. **Code generation**: 
   - Minium variable re-assign to another variable
   - Keep variable readable
   - Log out critical point of code execution by logger in @app/logger_utils/ 
7. **Docstring**: In every generated functions, add docstring with google-style