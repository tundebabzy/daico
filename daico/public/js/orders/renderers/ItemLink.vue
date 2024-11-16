<template>
    <a v-if="params.value" :href="`/app/item/${params.value}`" target="_blank">{{ value }}</a>
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
