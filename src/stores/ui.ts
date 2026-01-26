import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', {
  state: () => ({
    showNav: true
  }),
  actions: {
    toggleNav() {
      this.showNav = !this.showNav
    },
    setShowNav(value: boolean) {
      this.showNav = value
    }
  }
})
