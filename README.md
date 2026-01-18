# 倉庫管理系統 (WMS)

這是一個現代化的倉庫管理系統 (Warehouse Management System)，旨在提供直觀的倉庫佈局編輯與日常作業管理功能。

## 🚀 技術棧 (Tech Stack)

本專案採用以下前端技術構建：

-   **[Vue 3](https://vuejs.org/)**: 漸進式 JavaScript 框架
-   **[TypeScript](https://www.typescriptlang.org/)**: 強型別的 JavaScript 超集
-   **[Vite](https://vitejs.dev/)**: 下一代前端構建工具，提供極速的開發體驗
-   **[Pinia](https://pinia.vuejs.org/)**: Vue 的專屬狀態管理庫
-   **[Vue Router](https://router.vuejs.org/)**: Vue.js 的官方路由管理器
-   **[VueUse](https://vueuse.org/)**: 必要的 Vue Composition Utilities 集合

## ✨ 功能特色 (Features)

-   **身份驗證 (Authentication)**: 
    -   完整的登入系統
    -   路由守衛 (Router Guards) 保護需要權限的頁面
-   **儀表板 (Dashboard)**: 
    -   系統概覽與導航
-   **倉庫編輯器 (Warehouse Editor)**:
    -   可視化編輯倉庫佈局
    -   拖放式操作 (預計功能)
-   **作業視圖 (Operation View)**:
    -   日常倉庫作業的操作介面
    -   庫位與庫存管理

## 🛠️ 安裝與執行 (Setup)

請確保您的電腦已安裝 [Node.js](https://nodejs.org/) (建議使用 LTS 版本)。

1.  **複製專案 (Clone Repository)**

    ```bash
    git clone https://github.com/Eddiexian/AI_Pr.git
    cd AI_Pr
    ```

2.  **安裝依賴 (Install Dependencies)**

    ```bash
    npm install
    ```

3.  **啟動開發伺服器 (Start Dev Server)**

    ```bash
    npm run dev
    ```

4.  **建置生產版本 (Build for Production)**

    ```bash
    npm run build
    ```

## 📂 專案結構 (Project Structure)

```
src/
├── assets/          # 靜態資源
├── components/      # 共用元件
├── router/          # 路由設定
├── stores/          # Pinia 狀態管理 (Auth, Warehouse)
├── views/           # 頁面組件 (Login, Dashboard, Editor, Operation)
├── App.vue          # 根組件
└── main.ts          # 程式入口點
```
