# Native Helpers Module (`native_helpers/`)

This directory is reserved for native platform extensions (C/C++ DLLs, Rust binaries, or assembly routines) that handle low-level forensic tasks:

- Memory dump parsing & acquisition
- Direct raw physical block device read wrappers
- Hardware write-blocker drivers

## Security Model

1. **Isolation**: All native helpers must compile with strict compiler flags (`-fSTACK-PROTECTOR`, `ASLR`, `DEP`).
2. **Access Control**: Native binaries require administrative or elevated security contexts and are strictly gated by `REAL_DEVICE_OPERATIONS=true`.
3. **No Direct Storage Mutations**: In `SAFE_MODE=true`, native helpers must run in read-only/simulation mode.
