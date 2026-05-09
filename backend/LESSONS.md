1. **Use a formatter**: Always format your code, it makes your work more professional.
2. **Don't sleep on UV**: 
3. Avoid imports at function level unless your preventing a cyclic dependency or the imported module is expensive
4. **Use the same database in dev as you would in production**
5. Try docker
6. Never commit __pycache__ to VCS
7. Never commit database file to VCS
8. You don't really need `requirements.txt` to manage your dependencies, they're a thing of the past, you 
the modern `pyproject.toml` if you use package managers like poetry or uv (my current favourite), you wont 
need to worry about creating the `pyproject.toml` file yourself, it's the new standard, and from it,
requirements.txt files can be generated for platforms that really require it.
