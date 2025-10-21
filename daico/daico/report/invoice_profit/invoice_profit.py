# Copyright (c) 2025, tundebabzy@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": _("Sales Invoice"),
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 200,
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": _("Total Invoice Profit"),
            "fieldname": "total_invoice_profit",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 200,
            "indent": 1,
        },
        {
            "label": _("Quantity"),
            "fieldname": "quantity",
            "fieldtype": "Float",
            "width": 80,
        },
        {
            "label": _("Sales Price (Rate)"),
            "fieldname": "sales_price",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Purchase Price (Cost)"),
            "fieldname": "purchase_price",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Profit Per Item"),
            "fieldname": "profit_per_item",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Profit for Line"),
            "fieldname": "profit_for_line",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Shipping Fee"),
            "fieldname": "shipping_fee",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Tariff"),
            "fieldname": "tariff",
            "fieldtype": "Currency",
            "width": 140,
        },
    ]


def get_data(filters):
    data = []
    buying_price_list = filters.get("buying_price_list")
    from_date, to_date = filters.date_range
    if not buying_price_list:
        frappe.throw(
            _(
                "Please select a <strong>Buying Price List</strong> filter to calculate costs."
            )
        )

    if not from_date or not to_date:
        frappe.throw(_("<strong>Date Range</strong> is a mandatory filter."))

    conditions = ""
    filter_values = {
        "price_list": buying_price_list,
        "from_date": from_date,
        "to_date": to_date,
    }

    conditions += " AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s"

    if filters.get("sales_invoice"):
        conditions += " AND si.name = %(sales_invoice)s"
        filter_values["sales_invoice"] = filters["sales_invoice"]

    if filters.get("po_no"):
        conditions += " AND si.po_no LIKE %(po_no)s"
        filter_values["po_no"] = f"%{filters['po_no']}%"

    invoice_list = frappe.db.sql(
        f"""
        SELECT name, posting_date FROM `tabSales Invoice` si
        WHERE docstatus = 1 {conditions}
        ORDER BY name DESC, posting_date DESC
    """,
        filter_values,
        as_dict=True,
    )

    if not invoice_list:
        return []

    all_invoice_names = [inv.name for inv in invoice_list]
    all_item_codes = frappe.db.sql_list(
        """
        SELECT DISTINCT item_code FROM `tabSales Invoice Item`
        WHERE parent IN %(invoices)s
    """,
        {"invoices": all_invoice_names},
    )

    price_cache = build_price_cache(all_item_codes, buying_price_list)

    grand_total_profit = 0

    for inv in invoice_list:
        invoice_doc = frappe.get_doc("Sales Invoice", inv.name)

        invoice_total_profit = 0
        total_shipping = 0
        total_tariff = 0
        child_item_rows = []

        for item in invoice_doc.items:
            if item.item_code == "shippinghandling":
                total_shipping += item.rate
            elif item.item_code == "tariffdelivery":
                total_tariff += item.rate
            else:
                purchase_price = get_item_price_from_cache(
                    price_cache, item.item_code, invoice_doc.posting_date
                )

                profit_per_item = item.rate - purchase_price
                profit_for_line = profit_per_item * item.qty
                invoice_total_profit += profit_for_line

                child_item_rows.append(
                    {
                        "item_code": item.item_name,
                        "quantity": item.qty,
                        "sales_price": item.rate,
                        "purchase_price": purchase_price,
                        "profit_per_item": profit_per_item,
                        "profit_for_line": profit_for_line,
                        "indent": 1,
                    }
                )

        grand_total_profit += invoice_total_profit

        parent_row = {
            "sales_invoice": invoice_doc.name,
            "posting_date": invoice_doc.posting_date,
            "shipping_fee": total_shipping,
            "tariff": total_tariff,
            "total_invoice_profit": invoice_total_profit,
            "indent": 0,
        }
        data.append(parent_row)

        data.extend(child_item_rows)

    if data:
        data.append({})  # Add a separator line
        grand_total_row = {
            "sales_invoice": _("Invoice Profit for Period"),
            "total_invoice_profit": grand_total_profit,
            "is_grand_total_row": True,  # Flag for special formatting in JS
        }
        data.append(grand_total_row)

    return data


def build_price_cache(item_codes, price_list):
    """
    Builds a cache of item prices for a given list of items and a price list.
    Returns a dict: {item_code: [(valid_from_date, price), ...]}
    """
    cache = {}
    if not item_codes:
        return cache

    price_data = frappe.db.sql(
        """
        SELECT item_code, valid_from, price_list_rate
        FROM `tabItem Price`
        WHERE item_code IN %(item_codes)s AND price_list = %(price_list)s
        ORDER BY item_code, valid_from DESC
    """,
        {"item_codes": item_codes, "price_list": price_list},
        as_dict=True,
    )

    for row in price_data:
        if row.item_code not in cache:
            cache[row.item_code] = []
        cache[row.item_code].append((row.valid_from, row.price_list_rate))

    return cache


def get_item_price_from_cache(cache, item_code, transaction_date):
    """
    Looks up the item price from the pre-built cache for a specific date.
    """
    price_list_for_item = cache.get(item_code)
    if not price_list_for_item:
        return 0

    transaction_date_obj = getdate(transaction_date)

    for valid_from, price in price_list_for_item:
        if getdate(valid_from) <= transaction_date_obj:
            return price

    return 0
