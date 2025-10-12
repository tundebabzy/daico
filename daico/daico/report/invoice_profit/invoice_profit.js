// Copyright (c) 2025, tundebabzy@gmail.com and contributors
// For license information, please see license.txt

frappe.query_reports["Invoice Profit"] = {
    "filters": [
        {
            "fieldname": "sales_invoice",
            "label": __("Invoice Number"),
            "fieldtype": "Link",
            "options": "Sales Invoice"
        },
        {
            "fieldname": "po_no",
            "label": __("PO Number"),
            "fieldtype": "Data"
        }
    ],
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // Check for the custom flag 'is_total_row' to apply special formatting
        if (data && data.is_total_row) {
            // Make the 'Item' column text bold
            if (column.fieldname === 'item_code') {
                return `<strong style='color: var(--text-color);'>${value}</strong>`;
            } 
            // Make the total value in the 'Total Invoice Profit' column bold
            else if (column.fieldname === 'total_invoice_profit') {
                 return `<strong style='color: var(--text-color);'>${value}</strong>`;
            }
        }
        return value;
    }
};