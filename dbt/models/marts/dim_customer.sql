{{ config(materialized='table') }}

with stg as (

    select * from {{ ref('stg_online_retail') }}

),

customers as (

    select *
    from stg
    where customer_id is not null

),

-- A handful of customers (8 of 4,372) have order rows recorded under more than
-- one country. Resolved deterministically as "country as of the customer's
-- most recent invoice" — verified no customer ties for the single latest
-- invoiced_at, so this always picks exactly one row.
most_recent as (

    select
          customer_id
        , country
        , row_number() over (
              partition by customer_id order by invoiced_at desc
          ) as recency_rank
    from customers

),

final as (

    select
          customer_id
        , country
    from most_recent
    where recency_rank = 1

)

select * from final
