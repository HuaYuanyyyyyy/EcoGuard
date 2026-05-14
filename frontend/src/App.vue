<template>
  <router-view v-slot="{ Component }">
    <transition name="slide-up" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', sans-serif; }

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.6s ease;
}
.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}
.slide-up-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>