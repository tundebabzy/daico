# Copyright (c) 2025, tundebabzy@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    
    total_profit = sum(row.get('total_invoice_profit', 0) for row in data if row.get('is_total_row'))
    
    return columns, data

def get_columns():
    """Returns the column definitions for the report."""
    return [
        {
            "label": _("Sales Invoice"),
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 160
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 200
        },
        {
            "label": _("Quantity"),
            "fieldname": "quantity",
            "fieldtype": "Float",
            "width": 80
        },
        {
            "label": _("Sales Price (Rate)"),
            "fieldname": "sales_price",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Purchase Price (Cost)"),
            "fieldname": "purchase_price",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Profit Per Item"),
            "fieldname": "profit_per_item",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Profit for Line"),
            "fieldname": "profit_for_line",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Shipping Fee"),
            "fieldname": "shipping_fee",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Tariff"),
            "fieldname": "tariff",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Total Invoice Profit"),
            "fieldname": "total_invoice_profit",
            "fieldtype": "Currency",
            "width": 160
        }
    ]

def get_data(filters):
    """Fetches and processes the data for the report."""
    data = []
    
    conditions = ""
    filter_values = {}

    if filters.get("sales_invoice"):
        conditions += " AND si.name = %(sales_invoice)s"
        filter_values["sales_invoice"] = filters["sales_invoice"]
        
    if filters.get("po_no"):
        conditions += " AND si.po_no LIKE %(po_no)s"
        filter_values["po_no"] = f"%{filters['po_no']}%"

    invoice_list = frappe.db.sql(f"""
        SELECT name, posting_date
        FROM `tabSales Invoice` si
        WHERE docstatus = 1 {conditions}
        ORDER BY name DESC, posting_date DESC
    """, filter_values, as_dict=True)

    for inv in invoice_list:
        invoice_doc = frappe.get_doc("Sales Invoice", inv.name)
        invoice_total_profit = 0

        for item in invoice_doc.items:
            # Handle shipping charge item
            if item.item_code == "shippinghandling":
                data.append({
                    "sales_invoice": invoice_doc.name,
                    "posting_date": invoice_doc.posting_date,
                    "item_code": item.item_name,
                    "quantity": item.qty,
                    "shipping_fee": item.rate,
                })
            # Handle tariff charge item
            elif item.item_code == "tariffdelivery":
                 data.append({
                    "sales_invoice": invoice_doc.name,
                    "posting_date": invoice_doc.posting_date,
                    "item_code": item.item_name,
                    "quantity": item.qty,
                    "tariff": item.rate,
                })
            # Handle regular product items
            else:
                purchase_price = frappe.db.get_value("Item", item.item_code, "last_purchase_rate") or 0
                
                profit_per_item = item.rate - purchase_price
                profit_for_line = profit_per_item * item.qty
                invoice_total_profit += profit_for_line

                data.append({
                    "sales_invoice": invoice_doc.name,
                    "posting_date": invoice_doc.posting_date,
                    "item_code": item.item_name,
                    "quantity": item.qty,
                    "sales_price": item.rate,
                    "purchase_price": purchase_price,
                    "profit_per_item": profit_per_item,
                    "profit_for_line": profit_for_line,
                })

        data.append({
            "sales_invoice": invoice_doc.name,
            "item_code": _("Total Profit for this Invoice"),
            "total_invoice_profit": invoice_total_profit,
            "is_total_row": True 
        })

    return data
