import frappe
from frappe.utils import cint
import json

field_name_map = {
    "po_name": "po.name",
    "client_po": "po.custom_customer_po_number",
    "location": "po.customer",
    "po_date": "po.transaction_date",
    "li_number": "poi.idx",
    "buy_price": "poi.rate",
    "is_invoiced": "poi.sales_order",
}


@frappe.whitelist()
def get_orders(start=0, size=20, filter_model={}, sort_model={}):
    if isinstance(filter_model, str):
        filter_model = json.loads(filter_model)
    print(filter_model)
    if isinstance(sort_model, str):
        sort_model = json.loads(sort_model)

    orders = frappe.db.sql(
        f"""
        select poi.idx as li_number, po.custom_customer_po_number as client_po, po.customer as location, 
        poi.item_name as part_name, poi.item_code as part_number, poi.qty as qty_ordered, 
        po.transaction_date as po_date, poi.sales_order_item, poi.sales_order,
        poi.qty as qty_shipped, poi.rate as buy_price, po.name as po_name  from `tabPurchase Order Item` poi
        join `tabPurchase Order` po on poi.parent = po.name
        {transform_filter_model(filter_model)}
        {transform_sort_model(sort_model)}
        limit {cint(size) + 1} offset {cint(start)}""",
        as_dict=1,
        debug=1,
    )

    count = frappe.db.sql(
        f"""
        select count(*) as count from `tabPurchase Order Item` poi
        join `tabPurchase Order` po on poi.parent = po.name
        {transform_filter_model(filter_model)}
        {transform_sort_model(sort_model)}""",
        as_dict=1,
    )

    sales_items = [doc.sales_order_item for doc in orders]
    sales_data = frappe.get_all(
        "Sales Order Item",
        fields=["rate", "name", "parent"],
        filters={"name": ["in", sales_items]},
    )

    # push sales_data into a hash table
    sales_data_dict = {}
    for item in sales_data:
        sales_data_dict[item.name] = item.rate

    invoice_data = {}
    sales_order_names = [d.parent for d in sales_data]
    invoices = frappe.get_all(
        "Sales Invoice",
        fields=[
            "name",
            "`tabSales Invoice Item`.sales_order",
            "posting_date",
            "grand_total",
        ],
        filters={"sales_order": ["in", sales_order_names]},
    )

    for invoice in invoices:
        invoice_data[invoice.sales_order] = {
            "name": invoice.name,
            "posting_date": invoice.posting_date,
            "grand_total": invoice.grand_total,
        }

    # update `orders`
    for order in orders:
        if order.sales_order_item and sales_data_dict.get(order.sales_order_item):
            order["sales_price"] = sales_data_dict.get(order.sales_order_item)
        if order.sales_order and invoice_data.get(order.sales_order):
            order["is_invoiced"] = order.sales_order
            order["sales_invoice"] = (
                invoice_data.get(order.sales_order)["name"]
                if invoice_data.get(order.sales_order)
                else None
            )
            order["posting_date"] = (
                invoice_data.get(order.sales_order)["posting_date"]
                if invoice_data.get(order.sales_order)
                else None
            )
            order["grand_total"] = (
                invoice_data.get(order.sales_order)["grand_total"]
                if invoice_data.get(order.sales_order)
                else None
            )

    if filter_model.get("is_invoiced"):
        if filter_model["is_invoiced"].get("type") == "notBlank":
            orders = [order for order in orders if order.get("is_invoiced")]
        elif filter_model["is_invoiced"].get("type") == "blank":
            orders = [order for order in orders if not order.get("is_invoiced")]

    return {"result": orders[: cint(size)], "end": count[0].count if count else None}


def transform_filter_model(filter_model):
    fields = filter_model.keys() if filter_model else []
    tokens = _transform_filter(fields, filter_model)
    result = " and ".join(tokens)
    if result:
        result = f"where {result}"
    return result


def transform_sort_model(sort_model):
    order = [
        f"""order by {field_name_map.get(model.get("colId")) or model.get("colId")} {model.get("sort")}"""
        for model in sort_model
    ]
    if not order:
        order = ["order by po.modified desc"]
    return ", ".join(order)


def _transform_filter(keys, filter_model):
    result = []
    for key in keys:
        model = filter_model.get(key)
        _key = field_name_map.get(key) or key
        if model.get("filterType") == "text":
            if model.get("type") == "contains":
                result.append(f'{_key} LIKE "%%{model.get("filter")}%%"')
            if model.get("type") == "notContains":
                result.append(f'{_key} NOT LIKE "%%{model.get("filter")}%%"')
            if model.get("type") == "equals":
                result.append(f'{_key} = "{model.get("filter")}"')
            if model.get("type") == "notEqual":
                result.append(f'{_key} <> "{model.get("filter")}"')
            if model.get("type") == "startsWith":
                result.append(f'{_key} LIKE "{model.get("filter")}%%"')
            if model.get("type") == "endsWith":
                result.append(f'{_key} LIKE "%%{model.get("filter")}"')
            if model.get("type") == "blank":
                result.append(f"{_key} IS NULL")
            if model.get("type") == "notBlank":
                result.append(f"{_key} IS NOT NULL")

        if model.get("filterType") == "date":
            if model.get("type") == "lessThan":
                result.append(f'{_key} < CAST("{model.get("dateFrom")}" AS DATE)')
            if model.get("type") == "greaterThan":
                result.append(f'{_key} > CAST("{model.get("dateFrom")}" AS DATE)')
            if model.get("type") == "inRange":
                result.append(
                    f'{_key} BETWEEN CAST("{model.get("dateFrom")}" AS DATE) AND CAST("{model.get("dateTo")}" AS DATE)'
                )
            if model.get("type") == "equals":
                result.append(f'{_key} = CAST("{model.get("dateFrom")}" AS DATE)')
    return result
