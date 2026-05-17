import React from "react";
import ReactDOM from "react-dom/client";
import { App as AntApp, ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: "#111111",
          colorText: "#2F3437",
          colorTextSecondary: "#787774",
          colorBgLayout: "#F7F6F3",
          borderRadius: 8,
          fontFamily: "'SF Pro Display', 'Geist Sans', 'Helvetica Neue', 'Switzer', sans-serif"
        }
      }}
    >
      <AntApp>
        <App />
      </AntApp>
    </ConfigProvider>
  </React.StrictMode>
);
