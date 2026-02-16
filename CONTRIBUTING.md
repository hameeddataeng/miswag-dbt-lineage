# Contributing to miswag-dbt-lineage

Thank you for your interest in contributing! Here's how you can help:

## Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/miswag-dbt-lineage.git
cd miswag-dbt-lineage
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=miswag_dbt_lineage --cov-report=html

# Run specific test file
pytest tests/test_extractor.py -v
```

## Code Style

We use:
- **black** for code formatting
- **ruff** for linting
- **mypy** for type checking

Run these before submitting:
```bash
black .
ruff check .
mypy miswag_dbt_lineage --ignore-missing-imports
```

## Submitting Changes

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and add tests

3. Run tests and linting:
```bash
pytest
black .
ruff check .
```

4. Commit your changes:
```bash
git commit -m "Add feature: your feature description"
```

5. Push and create a pull request:
```bash
git push origin feature/your-feature-name
```

## Pull Request Guidelines

- Write clear, descriptive commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass
- Keep PRs focused on a single feature/fix

## Questions?

Open an issue or start a discussion on GitHub!
