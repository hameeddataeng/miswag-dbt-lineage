# Publishing to PyPI Guide

This guide walks through publishing `miswag-dbt-lineage` to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - Test PyPI: https://test.pypi.org/account/register/
   - Production PyPI: https://pypi.org/account/register/

2. **API Tokens**: Generate API tokens:
   - Test PyPI: https://test.pypi.org/manage/account/token/
   - Production PyPI: https://pypi.org/manage/account/token/

3. **Install build tools**:
```bash
pip install build twine
```

## Step 1: Verify Package Quality

### Check pyproject.toml
- Verify version number is correct
- Update author email if needed
- Ensure all dependencies are listed

### Run tests (if virtual env is set up)
```bash
pytest
black --check .
ruff check .
```

### Verify README renders correctly
```bash
pip install readme-renderer
python -m readme_renderer README.md -o /tmp/readme.html
open /tmp/readme.html
```

## Step 2: Build the Package

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build

# Verify build outputs
ls -lh dist/
# Should see:
# - miswag_dbt_lineage-0.1.0.tar.gz
# - miswag_dbt_lineage-0.1.0-py3-none-any.whl
```

## Step 3: Test on Test PyPI (Recommended)

```bash
# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*
# Enter your Test PyPI username and password/token

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ miswag-dbt-lineage

# Verify it works
miswag-dbt-lineage --version
```

## Step 4: Publish to Production PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*
# Enter your PyPI username and password/token

# Verify on PyPI
# Visit: https://pypi.org/project/miswag-dbt-lineage/
```

## Step 5: Test Installation

```bash
# Create fresh virtual environment
python -m venv test-env
source test-env/bin/activate

# Install from PyPI
pip install miswag-dbt-lineage

# Test it works
miswag-dbt-lineage --version
miswag-dbt-lineage --help
```

## Step 6: Tag the Release on GitHub

```bash
# Tag the version
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0

# Create GitHub release
# Go to: https://github.com/miswag/miswag-dbt-lineage/releases/new
# - Select tag: v0.1.0
# - Title: "v0.1.0 - Initial Release"
# - Copy release notes from CHANGELOG.md
```

## Using GitHub Actions for Auto-Publishing

The `.github/workflows/publish.yml` workflow will automatically publish to PyPI when you create a GitHub release.

### Setup:
1. Add PyPI API token to GitHub secrets:
   - Go to: https://github.com/miswag/miswag-dbt-lineage/settings/secrets/actions
   - Add secret: `PYPI_API_TOKEN`
   - Value: Your PyPI API token

2. Create a release on GitHub
3. The workflow will automatically build and publish

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- `0.1.0` → Initial release
- `0.1.1` → Bug fix
- `0.2.0` → New feature (backward compatible)
- `1.0.0` → Stable release

## Pre-release Versions

For beta/alpha releases:
```toml
# In pyproject.toml
version = "0.2.0a1"  # Alpha
version = "0.2.0b1"  # Beta
version = "0.2.0rc1" # Release candidate
```

## Troubleshooting

### "File already exists" error
- You cannot re-upload the same version
- Bump the version in `pyproject.toml` and rebuild

### Import errors after install
- Check `MANIFEST.in` includes all necessary files
- Verify `pyproject.toml` has correct package configuration

### Missing dependencies
- Ensure all dependencies are in `pyproject.toml`
- Test in clean virtual environment

## Checklist Before Publishing

- [ ] All tests pass
- [ ] Version number updated in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] README.md is accurate and renders correctly
- [ ] LICENSE file is present
- [ ] `.gitignore` excludes build artifacts
- [ ] All files committed to git
- [ ] Tested build locally
- [ ] Tested on Test PyPI
- [ ] GitHub repository is public
- [ ] GitHub secrets configured (for auto-publish)

## Post-Publishing

1. Announce on social media/communities
2. Update documentation
3. Monitor issues and feedback
4. Plan next version improvements
