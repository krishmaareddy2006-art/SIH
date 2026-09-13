# Forensic Test Data Module (`test_data/`)

This directory contains automated tooling for generating synthetic digital forensic evidence datasets for testing ingestion, indexing, hashing, duplication detection, and corruption recovery pipelines.

## Contents

- **`generator.py`**: Python script that builds deterministic forensic test trees.
- **`generated_evidence/`**: Default output directory containing generated test evidence and `manifest.json`.

## Generating Test Data

Run the generator from the project root or `test_data/` folder:

```bash
python test_data/generator.py
```

Or specify a custom output directory:

```bash
python test_data/generator.py ./custom_evidence_dir
```

## Evidence Manifest Schema (`manifest.json`)

The output directory will contain a `manifest.json` file detailing:
- File paths (relative to target directory)
- Exact calculated SHA-256 hashes
- Size in bytes
- Corruption status & structural flaw descriptions
- Duplication markers
