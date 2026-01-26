// src/stores/toast.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

type ToastType = 'success' | 'error' | 'info'

interface ToastItem {
  id: number
  message: string
  type: ToastType
}

let idSeed = 1

export const useToastStore = defineStore('toast', () => {
  const toasts = ref<ToastItem[]>([])

  const show = (message: string, type: ToastType = 'info', duration = 3000) => {
    const id = idSeed++
    const item: ToastItem = { id, message, type }
    toasts.value.push(item)

    if (duration > 0) {
      setTimeout(() => {
        remove(id)
      }, duration)
    }
  }

  const remove = (id: number) => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const success = (msg: string, duration = 3000) => show(msg, 'success', duration)
  const error = (msg: string, duration = 4000) => show(msg, 'error', duration)
  const info = (msg: string, duration = 3000) => show(msg, 'info', duration)

  return {
    toasts,
    show,
    remove,
    success,
    error,
    info,
  }
})
