frappe.pages["orders"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Orders"),
		single_column: true,
	});
};

frappe.pages["orders"].on_page_show = function (wrapper) {
	load_desk_page(wrapper);
};

function load_desk_page(wrapper) {
	let $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();

	frappe.require("orders.bundle.js").then(() => {
		frappe.orders = new frappe.ui.Orders({
			wrapper: $parent,
			page: wrapper.page,
		});
	});
}