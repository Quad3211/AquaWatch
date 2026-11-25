# ADR 0001: Settings in TOML, loaded with the standard library

**Status:** accepted (build guide step A3)

## Context
Detector thresholds, dataset cutoffs and app behaviour were module constants in `config.py`. Nothing checked their types or ranges, they could not be changed without editing code, and results did not record which values produced them. The build guide suggested `pydantic-settings`, but `AGENTS.md` asks the team to agree on new dependencies first.

## Decision
- Keep the tunable values in `configs/default.toml`, which is commented and versioned.
- Load them into frozen dataclasses in `src/aquawatch/settings.py` using `tomllib`, part of the standard library since Python 3.11. This adds no new dependency.
- Precedence: the TOML file (or the file named by `AQUAWATCH_CONFIG`), then environment variables `AQUAWATCH__<SECTION>__<KEY>`.
- Validate on load. Unknown keys and out-of-range values raise a `SettingsError`.
- `Settings.fingerprint()` is a 12-character hash of every setting that can change results; the app section is excluded. It is printed by `aquawatch evaluate` and stored in the model metadata.
- `config.py` keeps only file locations and fixed product wording.

## Consequences
- A typo in a setting fails loudly instead of being silently ignored.
- A results table can be traced to its exact settings through the fingerprint.
- Switching to pydantic later would mean changing one module.
- Settings are read when a function runs (`get_settings()` is cached), so call `get_settings.cache_clear()` after changing environment variables in a long-running process.
