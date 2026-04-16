# compliance-control-mapper

[![CI](https://github.com/intruderfr/compliance-control-mapper/actions/workflows/ci.yml/badge.svg)](https://github.com/intruderfr/compliance-control-mapper/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A zero-dependency command-line crosswalk that maps security controls across the four frameworks most IT and GRC teams have to speak fluently at once:

- **ISO/IEC 27001:2022** (Annex A, 93-control edition)
- **NIST Cybersecurity Framework 2.0** (Feb 2024)
- **CIS Controls v8**
- **SOC 2 Trust Services Criteria** (2017 TSC with 2022 points of focus)

Given a control from any one framework, `compliance-mapper` tells you which controls in the others cover the same ground - so you can scope a new certification against existing work instead of running a blank-sheet audit.

## Why this exists

Most organizations end up with overlapping compliance obligations: the auditors pursuing SOC 2 want one language, the legal team procuring on ISO 27001 want another, and the sysadmins trying to implement it all want CIS benchmarks. Rebuilding crosswalks by hand (spreadsheets, chased across Slack threads) wastes hours per audit cycle.

This tool ships with 16 curated topical crosswalks that cover **100% of the bundled ISO 27001 and CIS controls** and ~90% of the SOC 2 common criteria. It runs entirely offline on stock Python 3.9+ - no SaaS, no API keys, no telemetry.

## Installation

```bash
git clone https://github.com/intruderfr/compliance-control-mapper.git
cd compliance-control-mapper
pip install .
```

Or run it in place with no install:

```bash
git clone https://github.com/intruderfr/compliance-control-mapper.git
cd compliance-control-mapper
python -m compliance_mapper.cli stats
```

No runtime dependencies. Python 3.9+ is the only requirement.

## Usage

### Look up a control and find its equivalents

```bash
compliance-mapper map A.8.13
```

```
======================================================================
ISO/IEC 27001:2022  A.8.13 - Information backup
======================================================================

Summary: Maintain backup copies of information, software, and systems and test restoration regularly.

Crosswalk topic: Backup & Recovery (backup_recovery)
----------------------------------------------------------------------
  ISO/IEC 27001:2022:
    - A.5.29: Information security during disruption
    - A.5.30: ICT readiness for business continuity
  NIST CSF 2.0:
    - RC.RP: Incident Recovery Plan Execution
    - RC.CO: Incident Recovery Communication
  CIS Controls v8:
    - CIS-11: Data Recovery
  SOC 2 TSC:
    - A1.3: Recovery Plan Testing
    - CC7.5: Recovery from Incidents
    - CC9.1: Risk Mitigation Activities
```

The tool automatically figures out which framework the control belongs to. Use `-f` to disambiguate if a control ID appears in more than one framework.

### Search by keyword

```bash
compliance-mapper search "malware"
compliance-mapper search "incident" -f nist -f soc2
```

### List every control in a framework

```bash
compliance-mapper list iso27001
compliance-mapper list cis
```

Valid framework keys: `iso27001`, `nist_csf`, `cis`, `soc2`. Aliases `iso`, `nist`, `cis_v8`, `soc` all work too.

### Browse by topic

```bash
compliance-mapper topics               # list all 16 crosswalk topics
compliance-mapper topic backup_recovery
```

### Show coverage statistics

```bash
compliance-mapper stats
```

```
Crosswalk topics defined: 16

+-------------------------------------+-------+--------------+----------+
| Framework                           | Total | In crosswalk | Coverage |
+-------------------------------------+-------+--------------+----------+
| ISO/IEC 27001:2022                  | 31    | 31           | 100.0%   |
| NIST Cybersecurity Framework 2.0    | 21    | 20           | 95.2%    |
| CIS Controls v8                     | 18    | 18           | 100.0%   |
| SOC 2 Trust Services Criteria (TSC) | 28    | 25           | 89.3%    |
+-------------------------------------+-------+--------------+----------+
```

### Export for auditors or a wiki

```bash
compliance-mapper export markdown > crosswalk.md
compliance-mapper export csv      > crosswalk.csv
compliance-mapper export json     > crosswalk.json
```

The Markdown export is ready to paste into Confluence, Notion, or a GitHub wiki. The CSV is designed to drop straight into an audit work paper.

### Machine-readable output

Every read command takes `--json` for piping into another tool:

```bash
compliance-mapper map A.8.13 --json | jq '.topics[].resolved.nist_csf'
```

## The 16 crosswalk topics

| Topic key | Covers |
|---|---|
| `access_control` | Identity, authentication, authorization |
| `asset_management` | Hardware / software / data inventory |
| `vulnerability_management` | Vulnerability scanning, patching |
| `logging_monitoring` | Audit logs, SIEM, anomaly detection |
| `incident_response` | IR plans, reporting, mitigation |
| `malware_defense` | Endpoint protection, email/web filtering |
| `backup_recovery` | Backup, restoration, DR |
| `data_protection` | Classification, encryption, DLP |
| `governance` | Policies, roles, board oversight |
| `risk_management` | Risk assessment, risk treatment |
| `training_awareness` | Security awareness programs |
| `network_security` | Segmentation, perimeter, monitoring |
| `physical_security` | Facility, environmental controls |
| `supply_chain` | Third-party / vendor risk |
| `change_management` | Change, configuration management |
| `secure_development` | Secure SDLC, application security |

## How the mappings were built

The crosswalk topics are curated from publicly available cross-references:

- **NIST Online Informative References (OLIR)** - the official NIST crosswalks to CSF
- **CIS Community Defense Model** - CIS's own mapping of v8 to NIST, ISO, and PCI
- **AICPA SOC 2 mapping guides** - the Trust Services Criteria mapping to NIST 800-53
- Hand review against ISO/IEC 27001:2022 Annex A

### A word on accuracy

> **These mappings are general guidance, not audit conclusions.**
> Controls that are "equivalent in spirit" can differ materially in scope. A.8.13 and CIS-11 both talk about data recovery, but their specific testing requirements are not identical. Always validate the exact scope against your organization's control implementation with a qualified auditor before using a crosswalk to reduce audit work.

## Adding your own frameworks

The data is plain JSON in `data/`. Drop in a new framework by:

1. Adding `data/your_framework.json` with the same shape as the bundled files.
2. Registering it in `compliance_mapper/data.py` under `FRAMEWORKS`.
3. Adding its ID list to the relevant topics in `data/mappings.json`.
4. Running `pytest` - the `test_mappings_file_integrity` test verifies every ID resolves.

## Development

```bash
git clone https://github.com/intruderfr/compliance-control-mapper.git
cd compliance-control-mapper
pip install -e '.[dev]'
pytest
```

The test suite (`tests/`) covers data integrity, search, mapping, and every CLI command. It runs in under a second.

## Roadmap

- [ ] PCI DSS v4.0 mapping
- [ ] HIPAA Security Rule mapping
- [ ] GDPR Article 32 technical measures
- [ ] HTML dashboard export
- [ ] Gap-analysis command (given "we have controls X, Y, Z" - what's missing for SOC 2?)

Pull requests welcome, especially curated crosswalks for additional frameworks.

## License

MIT - see [LICENSE](LICENSE).

## Author

**Aslam Ahamed** - Head of IT @ Prestige One Developments, Dubai  
LinkedIn: [aslam-ahamed](https://www.linkedin.com/in/aslam-ahamed/)
