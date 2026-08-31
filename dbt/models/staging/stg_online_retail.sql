{{ config(materialized='view') }}

with source as (

    select * from {{ source('online_retail', 'online_retail_raw') }}

),

renamed as (

    select
          invoiceno    as invoice_no
        , stockcode    as stock_code
        , description  as description
        , quantity     as quantity
        , invoicedate  as invoiced_at
        , unitprice    as unit_price
        , customerid   as customer_id
        , country      as country
    from source

),

deduped as (

    -- The source contains 4,879 groups of byte-identical repeat rows (same
    -- invoice, stock code, description, quantity, date, price, customer, and
    -- country), totaling 10,147 rows out of 541,909; this keeps one row per
    -- group, removing 5,268 excess rows.
    select *
    from renamed
    qualify row_number() over (
        partition by
              invoice_no, stock_code, description, quantity
            , invoiced_at, unit_price, customer_id, country
        order by invoice_no
    ) = 1

),

typed as (

    -- TRY_CAST, never CAST — failures become null and get surfaced by a test,
    -- rather than aborting the build or silently vanishing. Verified against
    -- this source: 0 cast failures on quantity, unit_price, or invoiced_at.
    select
          {{ dbt_utils.generate_surrogate_key([
              'invoice_no', 'stock_code', 'description', 'quantity',
              'invoiced_at', 'unit_price', 'customer_id', 'country'
          ]) }}                                   as line_item_key
        , invoice_no
        , stock_code
        , description
        , try_cast(quantity as number)            as quantity
        , try_cast(unit_price as float)            as unit_price
        , try_to_timestamp_ntz(invoiced_at)        as invoiced_at
        , customer_id
        , country
    from deduped

),

flagged as (

    select
          typed.*

        -- A whole-invoice cancellation, by this dataset's InvoiceNo convention.
        -- Verified: every 'C'-prefixed invoice carries negative quantity, and no
        -- other prefix behaves the same way (a stray 'A'-prefixed "Adjust bad
        -- debt" entry is a distinct case, excluded from revenue via
        -- is_merchandise instead — see schema.yml).
        , invoice_no like 'C%'                                    as is_cancelled

        -- A negative-quantity row that is NOT a paired cancellation invoice.
        -- These are internal stock write-offs (no customer, zero price, notes
        -- like "damages"/"check"/"wet rusty"), not customer-initiated returns
        -- paired to an original sale.
        , quantity < 0 and not (invoice_no like 'C%')             as is_return

        -- False for known non-product stock codes: postage, carriage, manual
        -- entries, discounts, samples, bank charges, Amazon fees, charity
        -- commission, bad-debt write-offs, and gift vouchers. Deliberately an
        -- explicit list, not a code-shape regex — a shape rule would wrongly
        -- exclude real products such as the DCGS* codes and PADS, which carry
        -- genuine descriptions and (for PADS) real customers.
        , not (
              upper(trim(stock_code)) in (
                  'POST', 'DOT', 'M', 'C2', 'D', 'S',
                  'BANK CHARGES', 'AMAZONFEE', 'CRUK', 'B'
              )
              or left(upper(trim(stock_code)), 5) = 'GIFT_'
          )                                                        as is_merchandise

        -- ~25% of rows are guest checkouts with no CustomerID — that is
        -- expected, not missing data. See AGENTS.md.
        , customer_id is not null                                 as has_customer
    from typed

)

select * from flagged
