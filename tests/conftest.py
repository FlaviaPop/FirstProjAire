"""Global pytest fixtures shared by every test package.

Role-specific users and logged-in clients are added here by the stories that introduce
login and RBAC (1.2, 1.3), so every context's tests use the same fixtures. Markers are
declared in pyproject.toml ([tool.pytest.ini_options] markers, enforced by --strict-markers).
"""
