{{ config(materialized='table') }}

with stg as (

    select * from {{ ref('stg_online_retail') }}

),

-- Excludes non-revenue rows using stg_online_retail's named flags — never by
-- re-deriving the rule with an inline LIKE 'C%' or similar. 536,641 Silver
-- rows in, 523,697 kept (12,944 excluded: cancellations, stock write-offs,
-- and non-merchandise lines, with some overlap between the three).
revenue_rows as (

    select *
    from stg
    where not is_cancelled
      and not is_return
      and is_merchandise

),

final as (

    select
          line_item_key
        , invoice_no
        , stock_code
        , customer_id
        , country
        , invoiced_at
        , quantity
        , unit_price
        , quantity * unit_price as extended_revenue
    from revenue_rows

)

select * from final
