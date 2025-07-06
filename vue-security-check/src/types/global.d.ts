// 全局类型声明
declare global {
  interface Window {
    showNotification: (message: string, type?: string) => void
  }
}

export {}