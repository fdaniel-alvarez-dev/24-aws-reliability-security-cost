# 24-aws-reliability-security-cost

A portfolio-grade, runnable reliability + security toolkit focused on **cost-conscious database operations**:
repeatable drills, deterministic guardrails, and safe validation workflows.

This repository is intentionally generic (no employer branding). It demonstrates practical engineering habits:
clear runbooks, reliable automation, and honest validation.

## The 3 core problems this repo solves
1) **Cost control without surprises:** guardrails that catch obvious cost regressions early (before they ship).
2) **Recovery you can trust:** backup + restore drills that are verifiable and safe to rerun.
3) **Operational clarity:** runbooks and SLO templates that make expectations explicit.

## Quickstart (local lab)
Prereqs: Docker + Docker Compose.

```bash
make demo
```

You get:
- Postgres primary + replica
- PgBouncer for connection pooling
- scripts to seed data, verify replication, and run backup/restore drills

## Tests (two explicit modes)

This repo supports exactly two test modes via `TEST_MODE`:

- `TEST_MODE=demo` (default): **offline-only**, deterministic checks (no Docker, no cloud, no credentials)
- `TEST_MODE=production`: **real integrations**, guarded by an explicit opt-in

Run demo mode:

```bash
make test-demo
```

Run production mode (local integrations only):

```bash
make test-production
```

If production mode is missing tools, it will tell you exactly what to install and how to rerun.

## Cost guardrails

The file `tools/cost_guardrails.py` performs offline checks designed to catch common cost footguns:

- reproducibility risks (floating image tags)
- missing or weak cost-attribution signals in IaC examples
- missing repo documentation that supports operational ownership

Generate a JSON report:

```bash
python3 tools/cost_guardrails.py --format json --out artifacts/cost_guardrails.json
```

## Sponsorship and contact

Sponsored by:
CloudForgeLabs  
https://cloudforgelabs.ainextstudios.com/  
support@ainextstudios.com

Built by:
Freddy D. Alvarez  
https://www.linkedin.com/in/freddy-daniel-alvarez/

For job opportunities, contact:
it.freddy.alvarez@gmail.com

## License

Personal, educational, and non-commercial use is free. Commercial use requires paid permission.
See `LICENSE` and `COMMERCIAL_LICENSE.md`.
