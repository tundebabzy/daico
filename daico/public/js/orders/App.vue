<script setup>
import { ref, shallowRef, onBeforeMount } from 'vue';
import { AgGridVue } from "ag-grid-vue3";
import Link from './renderers/OrderLink.vue';
import CustomerLink from './renderers/CustomerLink.vue';
import ItemLink from './renderers/ItemLink.vue';
import IsInvoiced from './renderers/IsInvoiced.vue';
import SalesInvoiceLink from './renderers/SalesInvoiceLink.vue';
import SalesOrderLink from './renderers/SalesOrderLink.vue';

const rowData = ref([]);

const currencyFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', currencySign: "accounting" });

// Column Definitions: Defines the columns to be displayed.
const colDefs = ref([
  {
    field: "is_invoiced", "headerName": "Invoiced", cellRenderer: IsInvoiced,
    filter: "agTextColumnFilter", filterParams: {
      filterOptions: ["", "blank", "notBlank"],
      maxNumConditions: 1,
    },
    sortable: false,
    pinned: "left",
    width: 15
  },
  {
    field: "po_name", "headerName": "DWM PO", filter: "agTextColumnFilter", cellRenderer: Link,
    filterParams: {
      filterOptions: ["equals", "contains", "startsWith", "endsWith"],
      maxNumConditions: 1,
    },
    pinned: "left",
    width: 110
  },
  {
    field: "client_po", headerName: "PO", filter: "agTextColumnFilter",
    filterParams: {
      filterOptions: ["equals", "contains", "startsWith", "endsWith", "blank", "notBlank"],
      maxNumConditions: 1,
    },
    cellRenderer: SalesOrderLink,
    width: 110
  },
  {
    field: "location", filter: "agTextColumnFilter",
    filterParams: {
      filterOptions: ["equals", "contains", "startsWith", "endsWith", "blank", "notBlank"],
      maxNumConditions: 1,
    },
    cellRenderer: CustomerLink
  },
  {
    field: "po_date", headerName: "Date", filter: 'agDateColumnFilter',
    filterParams: {
      filterOptions: ["equals", "inRange", "greaterThan", "lessThan"],
      maxNumConditions: 1,
    },
    width: 120
  },
  { field: "li_number", headerName: "LI #", sortable: false, width: 60 },
  { field: "part_name", headerName: "Part Name", sortable: false },
  {
    field: "part_number", headerName: "Part Number",
    sortable: false,
    cellRenderer: ItemLink,
    width: 160
  },
  { field: "qty_ordered", headerName: "Qty Ordered", sortable: false, width: 100 },
  { field: "qty_shipped", headerName: "Qty Shipped", sortable: false, width: 100 },
  {
    field: "sales_price", headerName: "Sales Price",
    sortable: false,
    valueFormatter: p => { if (p.value) return currencyFormatter.format(p.value || 0) },
    width: 100
  },
  {
    field: "buy_price", headerName: "Buy Price",
    valueFormatter: p => { if (p.value) return currencyFormatter.format(p.value || 0) },
    width: 100
  },
  {
    field: "grand_total", headerName: "Invoice Amount",
    width: 120,
    valueFormatter: p => { if (p.value) return currencyFormatter.format(p.value || 0) },
  },
  { field: "posting_date", "headerName": "Invoice Date", width: 120 },
  { field: "sales_invoice", "headerName": "Invoice #", cellRenderer: SalesInvoiceLink, width: 120 },
  { field: "notes", editable: true, sortable: false }
]);

const defaultColDef = ref({
  wrapHeaderText: true,
});

const autoSizeStrategy = {
  defaultMinWidth: 10,
}

const gridApi = shallowRef();

const rowBuffer = ref(null);
const rowModelType = ref(null);
const cacheBlockSize = ref(null);
const cacheOverflowSize = ref(null);
const maxConcurrentDatasourceRequests = ref(null);
const infiniteInitialRowCount = ref(null);
const maxBlocksInCache = ref(null);
const paginationPageSize = ref(null);

onBeforeMount(() => {
  rowBuffer.value = 0;
  rowModelType.value = "infinite";
  cacheBlockSize.value = 100;
  cacheOverflowSize.value = 2;
  maxConcurrentDatasourceRequests.value = 1;
  infiniteInitialRowCount.value = 20; //
  maxBlocksInCache.value = 10;
  paginationPageSize.value = 20;
});

const onGridReady = (params) => {
  gridApi.value = params.api;

  const updateData = () => {
    const dataSource = {
      rowCount: null, // behave as infinite scroll while pagination will handle things
      getRows: (params) => {
        frappe.call({
          method: "daico.query.orders.get_orders",
          args: {
            start: params.startRow,
            size: params.endRow - params.startRow,
            filter_model: params.filterModel,
            sort_model: params.sortModel
          }
        })
          .then((resp) => {
            const rowsThisPage = resp.message.result;
            const lastRow = resp.message.end;
            params.successCallback(rowsThisPage, lastRow);
          });
      },
    };
    params.api.setGridOption("datasource", dataSource);
  };

  updateData();
};

const onFilterChanged = (e) => {
  console.log("onFilterChanged", e);
  console.log("gridApi.value.getFilterModel() =>", e.api.getFilterModel());
};
const onFilterModified = (e) => {
  console.log("onFilterModified", e);
  console.log("filterInstance.getModel() =>", e.filterInstance.getModel());
  console.log(
    "filterInstance.getModelFromUi() =>",
    e.filterInstance.getModelFromUi(),
  );
};

</script>
<template>
  <div style="width: 100%; height: 100%;">
    <ag-grid-vue :rowData="rowData" :columnDefs="colDefs" style="height: 500px" class="ag-theme-quartz"
      :autoSizeStrategy="autoSizeStrategy" :pagination="true" @grid-ready="onGridReady" :rowBuffer="rowBuffer"
      :rowModelType="rowModelType" :cacheBlockSize="cacheBlockSize" :cacheOverflowSize="cacheOverflowSize"
      :maxConcurrentDatasourceRequests="maxConcurrentDatasourceRequests"
      :infiniteInitialRowCount="infiniteInitialRowCount" :maxBlocksInCache="maxBlocksInCache"
      :paginationPageSize="paginationPageSize" @filter-opened="onFilterOpened" @filter-changed="onFilterChanged"
      @filter-modified="onFilterModified" :defaultColDef="defaultColDef">
    </ag-grid-vue>
  </div>
</template>