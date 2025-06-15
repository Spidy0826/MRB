# M-R-B 中途小巴     作者：Eight Lu

嗨！我是專案的作者，這邊是對於此專案的介紹，此專案目的是讓使用著可以查詢「台中市區公車抵達站點時間」的小網站。
而網站中所有公車的資訊都是透過由「運輸資料流通服務平臺（TDX）」的 Open API 所獲取，所以資訊都是正確、公開、合法的，請不用擔心
最後這個網站是透過 Render 所架設的。
# MRB 台中市區公車即時查詢系統

## 專案簡介
本專案是一個以 Django 開發的台中市區公車即時動態查詢網站，整合 TDX API，提供友善的公車到站查詢、去回程切換、日夜模式、響應式設計，並支援雲端自動部署。

## 主要功能
- 即時查詢台中市區公車到站資訊（整合 TDX API）
- 去程/回程滑動切換顯示
- 響應式 UI，手機/桌機自適應
- 日夜模式切換（支援自訂圖示）
- 查詢狀態提示、預估到站時間美化
- 靜態檔案與圖片正確載入
- 支援 Render 雲端自動部署

## 專案畫面
- ![首頁查詢畫面](static/images/demo-index.png)
- ![日夜模式切換](static/images/demo-darkmode.png)

## 安裝與本地開發
1. 下載原始碼
   ```bash
   git clone https://github.com/Spidy0826/MRB.git
   cd MRB
   ```
2. 安裝依賴
   ```bash
   pip install -r requirements.txt
   ```
3. 設定環境變數（可用 .env 檔）
   ```env
   SECRET_KEY=你的Django密鑰
   DEBUG=True
   TDX_APP_ID=你的TDX APP ID
   TDX_APP_KEY=你的TDX APP KEY
   ```
4. 資料庫遷移與靜態檔案收集
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
5. 啟動伺服器
   ```bash
   python manage.py runserver
   ```

## 雲端部署（Render）
1. 將專案推送到 GitHub
2. Render 建立新 Web Service，連接 GitHub 倉庫
3. Build Command：
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
   ```
4. Start Command：
   ```bash
   gunicorn bus_project.wsgi:application
   ```
5. 設定環境變數（與本地一致）
6. 完成自動部署

## 主要環境變數
| 變數名稱      | 說明                |
| ------------- | ------------------- |
| SECRET_KEY    | Django 安全密鑰     |
| DEBUG         | 是否開啟除錯模式    |
| TDX_APP_ID    | TDX API 應用程式ID  |
| TDX_APP_KEY   | TDX API 應用程式金鑰|

## 技術棧
- Python 3.11+
- Django 5+
- Gunicorn
- Whitenoise
- TDX API
- Render 雲端平台

## 專案結構
```
MRB/
├── bus_project/         # Django 主設定
├── businfo/             # 公車查詢 app
├── static/              # 靜態檔案與圖示
├── templates/           # 前端模板
├── requirements.txt     # 依賴套件
├── runtime.txt          # Python 版本
└── README.md
```

## 授權
本專案採用 MIT License。

---

如有問題或建議，歡迎開 issue 或 PR！
