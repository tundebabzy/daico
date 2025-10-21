// Copyright (c) 2025, tundebabzy@gmail.com and contributors
// For license information, please see license.txt

frappe.query_reports["Invoice Profit"] = {
    "filters": [
        {
            "fieldname": "date_range",
            "label": __("Date Range"),
            "fieldtype": "DateRange",
            "reqd": 1,
            "default": [frappe.datetime.add_months(frappe.datetime.get_today(), -1), frappe.datetime.get_today()]
        },
        {
            "fieldname": "buying_price_list",
            "label": __("Buying Price List"),
            "fieldtype": "Link",
            "options": "Price List",
            "default": "Standard Buying",
            "description": "Select the price list to use for calculating costs.",
            "reqd": 1
        },
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

		// Handle the grand total row first because it's the most specific
		if (data && data.is_grand_total_row) {
			if (column.fieldname === 'sales_invoice' || column.fieldname === 'total_invoice_profit') {
				// Special styling for the grand total text and value
				return `<strong style='font-size: 1.1em;'>${value}</strong>`;
			}
			// Return an empty string for other cells in this row to keep it clean
			return "";
		}

		// Handle regular parent rows
		if (data && data.indent === 0) {
			// If it's a parent row, make all its text bold
			return `<strong>${value}</strong>`;
		}

		// Otherwise, return the default value for child rows
		return value;
	}
};

