# Vendored Python dependencies

Place offline Python dependencies in this directory so packaged/compiled builds can run without network access.

Current expected dependency:

- `Pillow` (for `.tga` -> `.png` conversion)

## How to vendor locally

```bash
python3 -m pip install --target ./vendor pillow
```

`convert_mcpack.py` automatically prepends `./vendor` to `sys.path` at runtime.
