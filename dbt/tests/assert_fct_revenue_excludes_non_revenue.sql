-- fct_revenue claims to exclude cancellations, stock write-offs, and
-- non-merchandise lines, using stg_online_retail's flags. Returns rows only
-- on failure.
select fct.line_item_key
from {{ ref('fct_revenue') }} fct
join {{ ref('stg_online_retail') }} stg
    on stg.line_item_key = fct.line_item_key
where stg.is_cancelled
   or stg.is_return
   or not stg.is_merchandise
   or fct.extended_revenue < 0
