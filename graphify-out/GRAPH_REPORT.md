# Graph Report - ExpertTalksGgn  (2026-09-16)

## Corpus Check
- 48 files · ~26,522 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .example 1)

## Summary
- 109 nodes · 145 edges · 12 communities (8 shown, 4 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8441b815`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Bronze Loader & Tests
- Commit Message Governance
- Layered Architecture Docs
- Silver Staging Model
- Gold Revenue Rules
- Streamlit Deployment
- dbt Schema Naming
- dbt Package Dependencies
- Product Dimension

## God Nodes (most connected - your core abstractions)
1. `stg_online_retail Model` - 15 edges
2. `read_source()` - 10 edges
3. `fct_revenue Model` - 9 edges
4. `scan()` - 7 edges
5. `is_valid()` - 6 edges
6. `load()` - 6 edges
7. `assert_fct_revenue_excludes_non_revenue Test` - 6 edges
8. `Phase 1 — does graphify save tokens? (A/B result)` - 5 edges
9. `Phase 2 — round 2, same graph as round 1 (A/B result)` - 5 edges
10. `create-dbt-model Skill` - 5 edges

## Surprising Connections (you probably didn't know these)
- `create-dbt-model Skill` --conceptually_related_to--> `fct_revenue Model`  [INFERRED]
  .claude/skills/create-dbt-model/SKILL.md → dbt/models/marts/fct_revenue.sql
- `create-dbt-model Skill` --conceptually_related_to--> `stg_online_retail Model`  [INFERRED]
  .claude/skills/create-dbt-model/SKILL.md → dbt/models/staging/stg_online_retail.sql
- `create-dbt-model Skill` --conceptually_related_to--> `assert_fct_revenue_excludes_non_revenue Test`  [INFERRED]
  .claude/skills/create-dbt-model/SKILL.md → dbt/tests/assert_fct_revenue_excludes_non_revenue.sql
- `CI workflow (ci.yml)` --references--> `main()`  [EXTRACTED]
  .github/workflows/ci.yml → scripts/check_commit_msg.py
- `pre-commit config` --references--> `main()`  [EXTRACTED]
  .pre-commit-config.yaml → scripts/check_commit_msg.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Silver Business-Rule Flags** — dbt_models_staging_stg_online_retail_stg_online_retail, dbt_models_staging_stg_online_retail_is_cancelled, dbt_models_staging_stg_online_retail_is_return, dbt_models_staging_stg_online_retail_is_merchandise, dbt_models_staging_stg_online_retail_has_customer [EXTRACTED 1.00]
- **Gold Layer Marts Group** — dbt_models_marts_dim_customer_dim_customer, dbt_models_marts_dim_product_dim_product, dbt_models_marts_fct_revenue_fct_revenue, sql_deploy_02_create_streamlit_create_streamlit [INFERRED 0.85]
- **dbt Build Configuration Chain** — dbt_dbt_project_dbt_project, dbt_packages_packages, dbt_package_lock_package_lock, dbt_macros_generate_schema_name_generate_schema_name [INFERRED 0.85]
- **Commit Message Governance Gate** — scripts_check_commit_msg_is_valid, pre_commit_config, github_workflows_ci, concept_conventional_commits_etg [EXTRACTED 1.00]
- **Bronze/Silver/Gold Documented Across the Harness** — concept_bronze_layer, concept_silver_layer, concept_gold_layer, agents, claude, readme [EXTRACTED 1.00]

## Communities (12 total, 4 thin omitted)

### Community 0 - "Bronze Loader & Tests"
Cohesion: 0.16
Nodes (17): DataFrame, fixture, Path, SnowflakeConnection, connect(), load(), main(), Idempotent Bronze loader — data/raw/Online_Retail.xlsx ->… (+9 more)

### Community 1 - "Commit Message Governance"
Cohesion: 0.19
Nodes (13): Conventional Commits + mandatory ETG ticket, Guardrails as cost control, No-hardcoded-credentials gate, CI workflow (ci.yml), pre-commit config, is_valid(), main(), Enforce Conventional Commits with a mandatory ticket reference. Format:… (+5 more)

### Community 2 - "Layered Architecture Docs"
Cohesion: 0.24
Nodes (11): create-dbt-model skill, A-prefix 'Adjust bad debt' rows, Bronze layer, Force dtype=str on Bronze read, Four-beat demo structure, Gold layer, The harness, Silver layer (+3 more)

### Community 3 - "Silver Staging Model"
Cohesion: 0.15
Nodes (21): create-dbt-model Skill, dbt_project.yml Config, generate_schema_name Macro, Customer Country Tiebreak Rule, dim_customer Model, Product Description Tiebreak Rule, dim_product Model, fct_revenue Model (+13 more)

### Community 4 - "Gold Revenue Rules"
Cohesion: 0.29
Nodes (9): main(), Block hardcoded connection details and credentials in tracked files. CLAUDE.md:…, Return one message per offending line., scan(), parametrize, Tests for the hardcoded-credential gate. AAA pattern per CLAUDE.md., test_allows_placeholders_and_env_lookups(), test_flags_hardcoded_values() (+1 more)

### Community 5 - "Streamlit Deployment"
Cohesion: 0.67
Nodes (3): Git Repository Setup Script, Create Streamlit Deploy Script, Streamlit Reads Gold Only Rule

### Community 6 - "dbt Schema Naming"
Cohesion: 0.20
Nodes (9): Conclusion, Paired cost delta per round (`without − with`; positive = graphify cheaper that round), Phase 1 — does graphify save tokens? (A/B result), Recommendation for the demo, Results, Setup, Steps followed, per round, The AGENTS.md hint (+1 more)

### Community 7 - "dbt Package Dependencies"
Cohesion: 0.22
Nodes (8): Conclusion, Paired cost delta per round (`without − with`; positive = graphify cheaper that round), Phase 2 — round 2, same graph as round 1 (A/B result), Recommendation for the demo, Results, Setup, Steps followed, per round, The prompt tested (identical, byte-for-byte, on both branches, same as phase 1)

## Knowledge Gaps
- **19 isolated node(s):** `expert-talk-ggn`, `The AGENTS.md hint`, `The prompt tested (identical, byte-for-byte, on both branches)`, `Steps followed, per round`, `Paired cost delta per round (`without − with`; positive = graphify cheaper that round)` (+14 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 46 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Conventional Commits + mandatory ETG ticket` connect `Commit Message Governance` to `Layered Architecture Docs`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **What connects `expert-talk-ggn`, `The AGENTS.md hint`, `The prompt tested (identical, byte-for-byte, on both branches)` to the rest of the system?**
  _19 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Silver Staging Model` be split into smaller, more focused modules?**
  _Cohesion score 0.14624505928853754 - nodes in this community are weakly interconnected._
