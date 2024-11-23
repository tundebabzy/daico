<template>
    <p v-if="params.value" :href="`/app/customer/${params.value}`" target="_blank">{{ value ? "&#10004;" : "" }}</p>
</template>

<script setup>
import { onBeforeMount, ref } from 'vue';

const value = ref("");
const props = defineProps(["params"]);
const { params } = props;

onBeforeMount(() => {
    value.value = params.value;
});
</script>
