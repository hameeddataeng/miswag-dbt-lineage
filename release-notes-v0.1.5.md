# Release Notes: v0.1.5

## Overview
This is a critical bug fix release that resolves an AttributeError in the `build` command.

## What's Fixed

### Bug Fixes
- **Fixed AttributeError in build command** (#issue)
  - The `build` command was failing with `AttributeError: 'function' object has no attribute 'allow_extra_args'`
  - Root cause: Incorrect invocation of the `generate` command using `typer.Context`
  - Solution: Changed to direct function call instead of context-based invocation
  - Location: `miswag_dbt_lineage/cli/main.py:260`

## Impact
Users can now successfully use the `build` command without errors:

```bash
miswag-dbt-lineage build \
  --project-dir . \
  --output target/lineage_website \
  --dialect clickhouse
```

The command now properly:
1. Runs `dbt docs generate` (unless `--skip-dbt-docs` is specified)
2. Invokes the `generate` command internally without errors
3. Generates the lineage website successfully

## Upgrade Notes
No breaking changes. Simply upgrade to v0.1.5:

```bash
pip install --upgrade miswag-dbt-lineage==0.1.5
```

## Technical Details
**Before (broken):**
```python
ctx = typer.Context(generate)  # ❌ Fails
ctx.invoke(generate, ...)
```

**After (fixed):**
```python
generate(  # ✅ Works
    manifest=manifest,
    catalog=catalog,
    output=output,
    dialect=dialect,
    verbose=False,
)
```

## Credits
- Bug reported and fixed by the community
- Thanks to all users who provided feedback on this issue

---

**Full Changelog**: v0.1.4...v0.1.5
