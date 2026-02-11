#!/usr/bin/env python3
"""
Infrastructure Validation Script

Validates that the project structure, Docker Compose configuration, and
package configurations are correctly set up before development begins.

Exit codes:
  0 = All validations passed
  1 = One or more validations failed
"""

import sys
import yaml
from pathlib import Path


def check_directories():
    """Verify all required directories exist."""
    required_dirs = [
        "apps",
        "services",
        "infrastructure",
        "packages",
        "scripts",
    ]
    
    results = []
    for dir_name in required_dirs:
        path = Path(dir_name)
        exists = path.is_dir()
        results.append((f"Directory: {dir_name}", exists))
        if exists:
            print(f"✓ Directory exists: {dir_name}")
        else:
            print(f"✗ Directory missing: {dir_name}")
    
    return all(result[1] for result in results)


def check_files():
    """Verify all required files exist at root level."""
    required_files = [
        "docker-compose.yml",
        "README.md",
        ".gitignore",
    ]
    
    results = []
    for file_name in required_files:
        path = Path(file_name)
        exists = path.is_file()
        results.append((f"File: {file_name}", exists))
        if exists:
            print(f"✓ File exists: {file_name}")
        else:
            print(f"✗ File missing: {file_name}")
    
    return all(result[1] for result in results)


def check_docker_compose():
    """Verify docker-compose.yml is valid YAML."""
    docker_path = Path("docker-compose.yml")
    
    if not docker_path.is_file():
        print("✗ docker-compose.yml not found")
        return False
    
    try:
        with open(docker_path, 'r') as f:
            yaml.safe_load(f)
        print("✓ docker-compose.yml is valid YAML")
        return True
    except yaml.YAMLError as e:
        print(f"✗ docker-compose.yml is invalid: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading docker-compose.yml: {e}")
        return False


def check_backend_requirements():
    """Verify backend requirements.txt exists and is parseable."""
    req_path = Path("services/backend/requirements.txt")
    
    if not req_path.is_file():
        print("✗ services/backend/requirements.txt not found")
        return False
    
    try:
        with open(req_path, 'r') as f:
            lines = f.readlines()
        # Basic validation: count non-comment, non-empty lines
        valid_lines = [
            l.strip() for l in lines
            if l.strip() and not l.strip().startswith('#')
        ]
        print(f"✓ services/backend/requirements.txt is valid ({len(valid_lines)} packages)")
        return True
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")
        return False


def check_mobile_package_json():
    """Verify mobile package.json exists and has required scripts."""
    pkg_path = Path("apps/mobile/package.json")
    
    if not pkg_path.is_file():
        print("✗ apps/mobile/package.json not found")
        return False
    
    try:
        import json
        with open(pkg_path, 'r') as f:
            package = json.load(f)
        
        required_scripts = ["start", "test", "lint", "type-check"]
        scripts = package.get("scripts", {})
        
        missing = [s for s in required_scripts if s not in scripts]
        
        if missing:
            print(f"✗ apps/mobile/package.json missing scripts: {missing}")
            return False
        
        print("✓ apps/mobile/package.json has all required scripts")
        return True
    except Exception as e:
        print(f"✗ Error reading package.json: {e}")
        return False


def check_pytest_config():
    """Verify pytest.ini exists and is valid INI format."""
    pytest_path = Path("services/backend/pytest.ini")
    
    if not pytest_path.is_file():
        print("✗ services/backend/pytest.ini not found")
        return False
    
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(pytest_path)
        print("✓ services/backend/pytest.ini is valid")
        return True
    except Exception as e:
        print(f"✗ Error reading pytest.ini: {e}")
        return False


def check_jest_config():
    """Verify jest.config.js exists."""
    jest_path = Path("apps/mobile/jest.config.js")
    
    if not jest_path.is_file():
        print("✗ apps/mobile/jest.config.js not found")
        return False
    
    print("✓ apps/mobile/jest.config.js exists")
    return True


def main():
    """Run all validation checks."""
    print("\n" + "="*60)
    print("Infrastructure Validation")
    print("="*60 + "\n")
    
    checks = [
        ("Directories", check_directories),
        ("Root Files", check_files),
        ("Docker Compose", check_docker_compose),
        ("Backend Requirements", check_backend_requirements),
        ("Mobile Package.json", check_mobile_package_json),
        ("Pytest Config", check_pytest_config),
        ("Jest Config", check_jest_config),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n→ Checking {check_name}...")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"✗ Unexpected error in {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {check_name}")
    
    print("\n" + "="*60 + "\n")
    
    # Exit code
    if all(result for _, result in results):
        print("✓ All validations passed!")
        return 0
    else:
        print("✗ Some validations failed. Please check the structure.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
