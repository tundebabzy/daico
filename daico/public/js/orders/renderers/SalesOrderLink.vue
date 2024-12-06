<template>
    <a v-if="sales_order" :href="`/app/sales-order/${sales_order}`" target="_blank">{{ value }}</a>
    <span v-else>{{ value }}</span>
</template>

<script setup>
import { onBeforeMount, ref } from 'vue';

const value = ref("");
const sales_order = ref("");
const props = defineProps(["params"]);
const { params } = props;

onBeforeMount(() => {
    value.value = params.value;
    sales_order.value = params.data && params.data.sales_order ? params.data.sales_order : "";
});
</script>
