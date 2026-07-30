# Specification Compliance Map

This map links specification sections to implementation locations.

## Core Generation and Hard Constraints

- Sections 4, 5, 6, 7, 8, 9, 10.1, 10.2, 12.2, 12.3, 12.4, 15.2, 17.2, 25.1
  - Implemented in [src/noc_roster/solver.py](src/noc_roster/solver.py)
  - Validated in [src/noc_roster/validator.py](src/noc_roster/validator.py)

## Soft Objectives, RQS, and Fairness

- Sections 10.3, 10.4, 10.5, 11, 11.1, 11.2, 12.5, 12.7, 13.1, 13.2, 13.3, 13.4, 18, 19, 20, 21, 22, 23, 25.2, 25.3, 26, 27
  - Optimized in [src/noc_roster/solver.py](src/noc_roster/solver.py)
  - Scored and reported in [src/noc_roster/validator.py](src/noc_roster/validator.py)

## Cover Model

- Sections 14, 16, 16.1, 16.2
  - Implemented in [src/noc_roster/cover.py](src/noc_roster/cover.py)

## Workbook Outputs

- Section 24.1 to 24.10
  - Implemented in [src/noc_roster/workbook.py](src/noc_roster/workbook.py)

## CLI and Project Boilerplate

- GitHub-friendly Python packaging, entrypoints, usage docs:
  - [pyproject.toml](pyproject.toml)
  - [requirements.txt](requirements.txt)
  - [.gitignore](.gitignore)
  - [README.md](README.md)
  - [src/noc_roster/cli.py](src/noc_roster/cli.py)
