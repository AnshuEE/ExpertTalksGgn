{{ config(materialized='table') }}

with stg as (

    select * from {{ ref('stg_online_retail') }}

),

merchandise as (

    select *
    from stg
    where is_merchandise

),

-- A stock_code's description isn't stable (typos, revisions across the
-- source). Resolved as the most-frequent non-null description; the 12
-- stock_codes that tie on frequency are broken alphabetically, and the 112
-- stock_codes with no non-null description anywhere get description = null.
description_counts as (

    select
          stock_code
        , description
        , count(*) as description_frequency
    from merchandise
    where description is not null
    group by 1, 2

),

ranked as (

    select
          stock_code
        , description
        , row_number() over (
              partition by stock_code
              order by description_frequency desc, description asc
          ) as frequency_rank
    from description_counts

),

final as (

    select
          m.stock_code
        , ranked.description
    from (select distinct stock_code from merchandise) m
    left join ranked
        on ranked.stock_code = m.stock_code
        and ranked.frequency_rank = 1

)

select * from final
