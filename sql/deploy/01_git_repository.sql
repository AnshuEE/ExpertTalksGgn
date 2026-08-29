-- Snowflake native Git integration.
-- Run once, before the session. See FACILITATOR_RUNBOOK §1.4.
--
-- Placeholders in <angle brackets> are filled from the runbook's §0 table.
-- Do not commit real values into this file — a pre-commit hook will reject it.

-- ---------------------------------------------------------------------------
-- Step 1: database and layer schemas
-- ---------------------------------------------------------------------------
use role <SNOWFLAKE_ROLE>;

create database if not exists EXPERT_TALK;
create schema   if not exists EXPERT_TALK.BRONZE;
create schema   if not exists EXPERT_TALK.SILVER;
create schema   if not exists EXPERT_TALK.GOLD;

-- Long enough to survive the deck sections between beats.
alter warehouse <SNOWFLAKE_WAREHOUSE> set auto_suspend = 300;

-- ---------------------------------------------------------------------------
-- Step 2: credentials and API integration
-- CREATE API INTEGRATION needs ACCOUNTADMIN or an explicit CREATE INTEGRATION
-- grant. Sort this the day before, not five minutes before.
-- ---------------------------------------------------------------------------
use role accountadmin;

create or replace secret EXPERT_TALK.PUBLIC.git_pat
    type     = password
    username = '<git username>'
    password = '<personal access token, repo:read scope>';

create or replace api integration expert_talk_git_api
    api_provider                   = git_https_api
    api_allowed_prefixes           = ('https://github.com/AnshuEE')
    allowed_authentication_secrets = (EXPERT_TALK.PUBLIC.git_pat)
    enabled                        = true;

-- ---------------------------------------------------------------------------
-- Step 3: the repository object
-- ---------------------------------------------------------------------------
use role <SNOWFLAKE_ROLE>;

create or replace git repository EXPERT_TALK.PUBLIC.expert_talk_repo
    api_integration = expert_talk_git_api
    git_credentials = EXPERT_TALK.PUBLIC.git_pat
    origin          = 'https://github.com/AnshuEE/ExpertTalksGgn.git';

-- ---------------------------------------------------------------------------
-- Step 4: fetch, and prove it landed
-- Snowflake serves the FETCHED snapshot, not the live remote. Re-run this
-- ALTER after every push, or the dashboard silently serves stale code.
-- ---------------------------------------------------------------------------
alter git repository EXPERT_TALK.PUBLIC.expert_talk_repo fetch;

-- Must list your files. Empty output means the fetch did not land, and
-- CREATE STREAMLIT will fail later with a confusing path error.
ls @EXPERT_TALK.PUBLIC.expert_talk_repo/branches/main/;
