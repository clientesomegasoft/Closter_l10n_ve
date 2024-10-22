{
    "name": "Consignment Management System",
    "version": "16.0.0.0.0",
    "author": "Preciseways",  # pylint: disable=manifest-required-author
    "category": "Industries",
    "summary": """Retailer agrees to pay a seller or consignor for merchandise
    after the item sells or selling goods (clothing, furniture, etc.) through a
    third-party vendor such as a consignment store. the consignee is financially
    responsible (the buyer) for the receipt of a shipment also includes commission
    on consignment and multiple reports.""",
    "website": "https://apps.odoo.com/apps/modules/16.0/pways_so_po_consignment",  # pylint: disable=manifest-required-website
    "depends": ["purchase_stock", "sale_management", "sale_stock"],
    "data": [
        "security/purchase_security_inherit.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/purchase_order_view.xml",
        "views/res_partner_view.xml",
        "views/sale_order_view.xml",
        "views/analytic_account_view.xml",
        "report/report_action.xml",
        "report/consignments_template.xml",
        "wizard/consignment_report_wizard_view.xml",
        "views/menu_view.xml",
        "wizard/sale_order_create_wizard_view.xml",
        "views/sale_consignment_order_view.xml",
        "views/stock_warehouse_view.xml",
        "views/sale_order_consignment_view.xml",
        "report/sale_consignments_report_template.xml",
        "wizard/sale_consignment_report_wizard_view.xml",
    ],
    "Application": True,
    "installable": True,
    "price": 60.0,
    "currency": "EUR",
    "images": ["static/description/icon.png"],
    "license": "OPL-1",  # pylint: disable=license-allowed
}
