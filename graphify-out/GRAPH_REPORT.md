# Graph Report - .  (2026-08-31)

## Corpus Check
- Corpus is ~18,726 words - fits in a single context window. You may not need a graph.

## Summary
- 79 nodes · 139 edges · 12 communities (9 shown, 3 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.89)
- Token cost: 199,603 input · 6,500 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Bronze Loader & Tests|Bronze Loader & Tests]]
- [[_COMMUNITY_Commit Message Governance|Commit Message Governance]]
- [[_COMMUNITY_Layered Architecture Docs|Layered Architecture Docs]]
- [[_COMMUNITY_Silver Staging Model|Silver Staging Model]]
- [[_COMMUNITY_Gold Revenue Rules|Gold Revenue Rules]]
- [[_COMMUNITY_Streamlit Deployment|Streamlit Deployment]]
- [[_COMMUNITY_dbt Schema Naming|dbt Schema Naming]]
- [[_COMMUNITY_dbt Package Dependencies|dbt Package Dependencies]]
- [[_COMMUNITY_Customer Dimension|Customer Dimension]]
- [[_COMMUNITY_Product Dimension|Product Dimension]]

## God Nodes (most connected - your core abstractions)
1. `stg_online_retail Model` - 15 edges
2. `read_source()` - 11 edges
3. `fct_revenue Model` - 9 edges
4. `Facilitator Runbook` - 9 edges
5. `is_valid()` - 8 edges
6. `load()` - 7 edges
7. `assert_fct_revenue_excludes_non_revenue Test` - 6 edges
8. `CI workflow (ci.yml)` - 6 edges
9. `AI Review Checklist` - 6 edges
10. `main()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `create-dbt-model Skill` --conceptually_related_to--> `fct_revenue Model`  [INFERRED]
  .claude/skills/create-dbt-model/SKILL.md → dbt/models/marts/fct_revenue.sql
- `create-dbt-model Skill` --conceptually_related_to--> `assert_fct_revenue_excludes_non_revenue Test`  [INFERRED]
  .claude/skills/create-dbt-model/SKILL.md → dbt/tests/assert_fct_revenue_excludes_non_revenue.sql
- `create-dbt-model Skill` --conceptually_related_to--> `stg_online_retail Model`  [INFERRED]
  .claude/skills/create-dbt-model/SKILL.md → dbt/models/staging/stg_online_retail.sql
- `pre-commit config` --references--> `main()`  [EXTRACTED]
  .pre-commit-config.yaml → scripts/check_commit_msg.py
- `main()` --calls--> `Path`  [INFERRED]
  scripts/check_commit_msg.py → src/bronze/load_online_retail.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Silver Business-Rule Flags** — staging_stg_online_retail_stg_online_retail, staging_stg_online_retail_is_cancelled, staging_stg_online_retail_is_return, staging_stg_online_retail_is_merchandise, staging_stg_online_retail_has_customer [EXTRACTED 1.00]
- **Gold Layer Marts Group** — marts_dim_customer_dim_customer, marts_dim_product_dim_product, marts_fct_revenue_fct_revenue, deploy_02_create_streamlit_create_streamlit [INFERRED 0.85]
- **dbt Build Configuration Chain** — dbt_dbt_project_dbt_project, dbt_packages_packages, dbt_package_lock_package_lock, macros_generate_schema_name_generate_schema_name [INFERRED 0.85]
- **Bronze Loader Test Suite** — bronze_load_online_retail_read_source, tests_test_load_online_retail_source_xlsx, tests_test_load_online_retail_test_forces_every_source_column_to_string, tests_test_load_online_retail_test_preserves_row_count_and_blank_customer_id, tests_test_load_online_retail_test_adds_sequential_source_row_starting_at_one, tests_test_load_online_retail_test_adds_source_file_and_loaded_at_metadata [EXTRACTED 1.00]
- **Commit Message Governance Gate** — scripts_check_commit_msg_is_valid, pre_commit_config, workflows_ci, concept_conventional_commits_etg [EXTRACTED 1.00]
- **Bronze/Silver/Gold Documented Across the Harness** — concept_bronze_layer, concept_silver_layer, concept_gold_layer, agents, claude, readme [EXTRACTED 1.00]

## Communities (12 total, 3 thin omitted)

### Community 0 - "Bronze Loader & Tests"
Cohesion: 0.18
Nodes (17): connect(), CREATE_TABLE_SQL, load(), main(), Idempotent Bronze loader — data/raw/Online_Retail.xlsx -> BRONZE.ONLINE_RETAIL_R, Read the source file with every column forced to string, no other changes., Full idempotent reload of BRONZE.ONLINE_RETAIL_RAW. Returns rows loaded., read_source() (+9 more)

### Community 1 - "Commit Message Governance"
Cohesion: 0.18
Nodes (14): Conventional Commits + mandatory ETG ticket, Guardrails as cost control, No-hardcoded-credentials gate, pre-commit config, EXEMPT (git-generated commit regex), is_valid(), main(), PATTERN (commit regex) (+6 more)

### Community 2 - "Layered Architecture Docs"
Cohesion: 0.40
Nodes (11): A-prefix 'Adjust bad debt' rows, Bronze layer, Force dtype=str on Bronze read, Four-beat demo structure, Gold layer, The harness, Silver layer, create-dbt-model skill (+3 more)

### Community 3 - "Silver Staging Model"
Cohesion: 0.33
Nodes (6): create-dbt-model Skill, CustomerID Float Artifact Bug, online_retail_raw Source, Byte-Identical Dedup Rule, has_customer Rule, stg_online_retail Model

### Community 4 - "Gold Revenue Rules"
Cohesion: 0.60
Nodes (6): fct_revenue Model, is_cancelled Rule, is_merchandise Rule, is_return Rule, assert_fct_revenue_excludes_non_revenue Test, assert_stg_online_retail_cancelled_return_disjoint Test

### Community 5 - "Streamlit Deployment"
Cohesion: 0.67
Nodes (3): Git Repository Setup Script, Create Streamlit Deploy Script, Streamlit Reads Gold Only Rule

### Community 7 - "dbt Package Dependencies"
Cohesion: 0.67
Nodes (3): package-lock.yml Lockfile, dbt_utils Package, packages.yml Dependency Manifest

## Knowledge Gaps
- **10 isolated node(s):** `DataFrame`, `SnowflakeConnection`, `dbt_project.yml Config`, `packages.yml Dependency Manifest`, `package-lock.yml Lockfile` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `read_source()` connect `Bronze Loader & Tests` to `Layered Architecture Docs`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Why does `main()` connect `Commit Message Governance` to `Bronze Loader & Tests`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `Path` connect `Bronze Loader & Tests` to `Commit Message Governance`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **What connects `True if the first non-comment line satisfies the convention.`, `DataFrame`, `SnowflakeConnection` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._