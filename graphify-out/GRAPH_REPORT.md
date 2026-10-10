# Graph Report - ExpertTalksGgn  (2026-10-10)

## Corpus Check
- 31 files · ~22,093 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: .example 3, (none) 3, .stm 3)

## Summary
- 188 nodes · 284 edges · 26 communities (13 shown, 13 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cebc390a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_load_online_retail.py
- CI workflow (ci.yml)
- README.md
- stg_online_retail Model
- check_commit_msg.py
- Create Streamlit Deploy Script
- token_usage.py
- Token Tracking: Measuring API Spend Per Request
- load
- expert-talk-ggn
- load_online_retail.py
- _StubConnection
- SnowflakeConnectionConfig
- package.json
- test_load_raises_when_the_warehouse_load_fails

## God Nodes (most connected - your core abstractions)
1. `stg_online_retail Model` - 15 edges
2. `Request` - 13 edges
3. `load()` - 12 edges
4. `read_source()` - 10 edges
5. `price()` - 9 edges
6. `iter_requests()` - 9 edges
7. `Token Tracking: Measuring API Spend Per Request` - 9 edges
8. `fct_revenue Model` - 9 edges
9. `SnowflakeConnectionConfig` - 8 edges
10. `scan()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `2. too-many-parameters — line 58 (`connect`)` --references--> `SnowflakeConnectionConfig`  [INFERRED]
  habit-hooks-plan.md → src/bronze/load_online_retail.py
- `Out of scope — flagged, not fixed here` --references--> `connect()`  [INFERRED]
  habit-hooks-plan.md → src/bronze/load_online_retail.py
- `1. swallowed-exception — line 96` --references--> `load()`  [INFERRED]
  habit-hooks-plan.md → src/bronze/load_online_retail.py
- `Order of operations` --references--> `load()`  [INFERRED]
  habit-hooks-plan.md → src/bronze/load_online_retail.py
- `2. too-many-parameters — line 58 (`connect`)` --references--> `connect()`  [INFERRED]
  habit-hooks-plan.md → src/bronze/load_online_retail.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Silver Business-Rule Flags** — dbt_models_staging_stg_online_retail_stg_online_retail, dbt_models_staging_stg_online_retail_is_cancelled, dbt_models_staging_stg_online_retail_is_return, dbt_models_staging_stg_online_retail_is_merchandise, dbt_models_staging_stg_online_retail_has_customer [EXTRACTED 1.00]
- **Bronze/Silver/Gold Documented Across the Harness** — concept_bronze_layer, concept_silver_layer, concept_gold_layer, agents, claude, readme [EXTRACTED 1.00]
- **dbt Build Configuration Chain** — dbt_dbt_project_dbt_project, dbt_packages_packages, dbt_package_lock_package_lock, dbt_macros_generate_schema_name_generate_schema_name [INFERRED 0.85]
- **Gold Layer Marts Group** — dbt_models_marts_dim_customer_dim_customer, dbt_models_marts_dim_product_dim_product, dbt_models_marts_fct_revenue_fct_revenue, sql_deploy_02_create_streamlit_create_streamlit [INFERRED 0.85]

## Communities (26 total, 13 thin omitted)

### Community 0 - "test_load_online_retail.py"
Cohesion: 0.22
Nodes (12): DataFrame, fixture, src_bronze, Read the source file with every column forced to string, no other changes., read_source(), Tests for the Bronze loader. AAA pattern per CLAUDE.md. `read_source` is pure…, snowflake_env(), source_xlsx() (+4 more)

### Community 1 - "CI workflow (ci.yml)"
Cohesion: 0.47
Nodes (5): Conventional Commits + mandatory ETG ticket, Guardrails as cost control, No-hardcoded-credentials gate, CI workflow (ci.yml), pre-commit config

### Community 2 - "README.md"
Cohesion: 0.24
Nodes (11): create-dbt-model skill, A-prefix 'Adjust bad debt' rows, Bronze layer, Force dtype=str on Bronze read, Four-beat demo structure, Gold layer, The harness, Silver layer (+3 more)

### Community 3 - "stg_online_retail Model"
Cohesion: 0.15
Nodes (21): create-dbt-model Skill, dbt_project.yml Config, generate_schema_name Macro, Customer Country Tiebreak Rule, dim_customer Model, Product Description Tiebreak Rule, dim_product Model, fct_revenue Model (+13 more)

### Community 4 - "check_commit_msg.py"
Cohesion: 0.13
Nodes (21): pathlib, pytest, re, is_valid(), main(), Enforce Conventional Commits with a mandatory ticket reference. Format:…, True if the first non-comment line satisfies the convention., main() (+13 more)

### Community 5 - "Create Streamlit Deploy Script"
Cohesion: 0.67
Nodes (3): Git Repository Setup Script, Create Streamlit Deploy Script, Streamlit Reads Gold Only Rule

### Community 6 - "token_usage.py"
Cohesion: 0.12
Nodes (33): argparse, collections, json, _fmt_usd(), iter_requests(), main(), price(), project_dir() (+25 more)

### Community 7 - "Token Tracking: Measuring API Spend Per Request"
Cohesion: 0.12
Nodes (15): By model (`--by-model`), Deduplication, For Next Steps, Implementation Notes, Key Numbers to Know, List-Price Estimates, Measuring Cost Savings (Before/After Habit-Hooks), Output Explained (+7 more)

### Community 8 - "load"
Cohesion: 0.21
Nodes (12): 1. swallowed-exception — line 96, 2. too-many-parameters — line 58 (`connect`), 3. unused-import — line 11, habit-hooks fix plan — src/bronze/load_online_retail.py, Order of operations, Out of scope — flagged, not fixed here, SnowflakeConnection, connect() (+4 more)

### Community 12 - "load_online_retail.py"
Cohesion: 0.25
Nodes (7): dataclasses, datetime, os, pandas, snowflake_connector, snowflake_connector_pandas_tools, Idempotent Bronze loader — data/raw/Online_Retail.xlsx ->…

### Community 13 - "_StubConnection"
Cohesion: 0.29
Nodes (3): Minimal stand-in for SnowflakeConnection: context manager + cursor()., _StubConnection, test_load_returns_row_count_when_the_write_succeeds()

### Community 14 - "SnowflakeConnectionConfig"
Cohesion: 0.47
Nodes (5): The six connection fields that always travel together. Same field set the dbt…, Read the profile from the environment. A missing variable raises KeyError., SnowflakeConnectionConfig, test_connection_config_raises_when_an_environment_variable_is_missing(), test_connection_config_reads_every_field_from_the_environment()

### Community 15 - "package.json"
Cohesion: 0.50
Nodes (3): devDependencies, jscpd, jscpd

## Knowledge Gaps
- **23 isolated node(s):** `jscpd`, `jscpd`, `expert-talk-ggn`, `TL;DR`, `Where Data Comes From` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 80 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load()` connect `load` to `test_load_online_retail.py`, `load_online_retail.py`, `_StubConnection`, `SnowflakeConnectionConfig`, `test_load_raises_when_the_warehouse_load_fails`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `_StubConnection` connect `_StubConnection` to `test_load_online_retail.py`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `SnowflakeConnectionConfig` connect `SnowflakeConnectionConfig` to `load`, `test_load_online_retail.py`, `load_online_retail.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `load()` (e.g. with `1. swallowed-exception — line 96` and `2. too-many-parameters — line 58 (`connect`)`) actually correct?**
  _`load()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `jscpd`, `jscpd`, `expert-talk-ggn` to the rest of the system?**
  _23 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `stg_online_retail Model` be split into smaller, more focused modules?**
  _Cohesion score 0.14624505928853754 - nodes in this community are weakly interconnected._
- **Should `check_commit_msg.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12666666666666668 - nodes in this community are weakly interconnected._
