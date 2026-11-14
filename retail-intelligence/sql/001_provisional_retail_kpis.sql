-- Project 003 Retail Intelligence | Case 018 SQL workbench
-- Requires a LOCAL candidate_lines table built from the unchanged Case 008
-- reversible view. All values are descriptive source records, not revenue.
-- Missing customer IDs remain NULL. No raw rows are exported.
CREATE TEMP VIEW retail_classified AS
SELECT
    invoice_no, stock_code, quantity, unit_price, invoice_date,
    customer_id, country,
    CASE
        WHEN SUBSTR(UPPER(TRIM(invoice_no)), 1, 1) = 'C'
            THEN 'cancellation_coded'
        WHEN quantity < 0 AND unit_price = 0 AND customer_id IS NULL
            THEN 'negative_quantity_zero_price_unknown_customer'
        WHEN quantity < 0
            THEN 'non_c_negative_quantity_other'
        WHEN quantity > 0 AND unit_price < 0
            THEN 'positive_quantity_negative_price'
        WHEN quantity > 0 AND unit_price = 0
            THEN 'positive_quantity_zero_price'
        WHEN quantity > 0 AND unit_price > 0
             AND UPPER(TRIM(stock_code)) IN
             ('POST', 'DOT', 'C2', 'BANK CHARGES', 'AMAZONFEE')
            THEN 'named_shipping_billing_code_candidate'
        WHEN quantity > 0 AND unit_price > 0
             AND UPPER(TRIM(stock_code)) IN ('M', 'D')
            THEN 'manual_discount_code_candidate'
        WHEN quantity > 0 AND unit_price > 0
            THEN 'other_positive_priced'
        ELSE 'unresolved_other'
    END AS provisional_line_cohort
FROM candidate_lines;
