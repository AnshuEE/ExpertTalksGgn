-- Deploy the Streamlit-in-Snowflake app from the Git repository object.
-- Run AFTER pushing the branch. See FACILITATOR_RUNBOOK §6 and Appendix C.10.
--
-- The app itself (streamlit/app.py) is built live during the demo — this file is
-- only the deploy step, and it reads Gold via the app, never directly.

use role <SNOWFLAKE_ROLE>;
use database EXPERT_TALK;

-- Always fetch first. Ninety percent of "the dashboard didn't update" is a
-- missing FETCH: Snowflake serves the fetched snapshot, not the live remote.
alter git repository EXPERT_TALK.PUBLIC.expert_talk_repo fetch;

-- Confirm the branch path exists before creating against it.
ls @EXPERT_TALK.PUBLIC.expert_talk_repo/branches/<BRANCH>/streamlit/;

create or replace streamlit EXPERT_TALK.GOLD.expert_talk_dashboard
    root_location   = '@EXPERT_TALK.PUBLIC.expert_talk_repo/branches/<BRANCH>/streamlit'
    main_file       = 'app.py'
    query_warehouse = <SNOWFLAKE_WAREHOUSE>
    comment         = 'Expert Talks GGN — revenue dashboard. Reads EXPERT_TALK.GOLD only.';

-- The app URL is in this output.
show streamlits in schema EXPERT_TALK.GOLD;
