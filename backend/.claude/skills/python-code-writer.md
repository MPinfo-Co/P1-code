---
name: python-code-writer
description: Generate codes for project
---

Generate code fits logic of the project

1. **Install environment**: Install uv if not already exists, search for requirements.txt in root directory, install with `uv pip install -r requirements.txt`
2. **Codebase inspect**: Inspect structure of full code base, identify which function module need code writing according to instruction
3. **Instruction breakdown**: Verify human instruction, if scope is too large to handle at once, break down to smaller generation or modification sections
4. **Requirement breakdown**: Break down development goal, execute order as below, skip if not required
   1. Modification in database
   2. Modification in FastAPI server middleware
   3. Modification in logic behind API
   4. Modification in FastAPI startup/teardown(lifespan)
   5. Modification in tasks(@app/tasks)
5. **Restrictions**: 
   1. Only use libraries in project environment, ask for human for additional package if required
   2. Don't restructure server/database
6. **Code generation**: 
   - Minium variable re-assign to another variable
   - Keep variable readable
   - Log out critical point of code execution by logger in @app/logger_utils/ 
   - Use existed files for newly generate code, report to human if required to modify existed code
7. **Docstring**: In every generated functions, add docstring with google-style is a must