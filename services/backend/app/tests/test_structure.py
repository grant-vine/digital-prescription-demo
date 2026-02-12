"""Test suite for backend directory structure validation."""

import pytest
from pathlib import Path


def test_backend_directory_structure():
    """Verify all required backend directories exist."""
    backend_root = Path(".")
    required_dirs = [
        backend_root / "app",
        backend_root / "app" / "models",
        backend_root / "app" / "services",
        backend_root / "app" / "api",
        backend_root / "app" / "tests",
    ]
    
    for dir_path in required_dirs:
        assert dir_path.is_dir(), f"Required directory missing: {dir_path}"


def test_requirements_file():
    """Verify requirements.txt exists and is parseable."""
    req_path = Path("requirements.txt")
    
    assert req_path.is_file(), "requirements.txt not found"
    
    with open(req_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) > 0, "requirements.txt is empty"
    
    # Validate format: each line should be empty, comment, or valid package spec
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            # Basic package spec validation (name or name==version)
            assert '=' in stripped or stripped.isidentifier(), \
                f"Invalid package spec: {stripped}"


def test_pytest_config():
    """Verify pytest.ini exists and is valid."""
    pytest_path = Path("pytest.ini")
    
    assert pytest_path.is_file(), "pytest.ini not found"
    
    # Verify it's valid INI format
    import configparser
    config = configparser.ConfigParser()
    config.read(pytest_path)
    
    # Should have at least pytest section
    assert len(config.sections()) > 0, "pytest.ini has no valid sections"
