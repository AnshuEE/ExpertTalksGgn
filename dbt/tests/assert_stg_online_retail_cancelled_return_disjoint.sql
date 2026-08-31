-- is_cancelled and is_return are derived from overlapping signals (invoice_no
-- prefix, quantity sign) and must never both be true for the same row — a
-- cancellation and a stock write-off are distinct things. Returns rows only
-- on failure.
select *
from {{ ref('stg_online_retail') }}
where is_cancelled and is_return
