# 家具商城網站

這是一個使用Python Flask框架開發的家具產品購買網站。

## 功能特點

- 用戶註冊和登入系統
- 產品展示和詳情頁面
- 購物車功能
- 響應式設計
- 安全的用戶認證

## 技術棧

- 後端：Python Flask
- 前端：HTML, CSS, JavaScript, Bootstrap 5
- 數據庫：SQLite

## 安裝步驟

1. 克隆項目到本地：
```bash
git clone [項目URL]
cd furniture-store
```

2. 創建虛擬環境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安裝依賴：
```bash
pip install -r requirements.txt
```

4. 初始化數據庫：
```bash
flask db init
flask db migrate
flask db upgrade
```

5. 運行應用：
```bash
python app.py
```

## 項目結構

```
furniture-store/
├── app.py              # 主應用程序
├── requirements.txt    # 項目依賴
├── static/            # 靜態文件
│   ├── css/
│   └── js/
├── templates/         # HTML模板
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── product_detail.html
│   └── cart.html
└── README.md         # 項目說明
```

## 使用說明

1. 訪問首頁查看所有產品
2. 註冊新帳號或登入
3. 瀏覽產品並加入購物車
4. 在購物車中管理商品
5. 結帳完成購買

## 開發者

[您的名字]

## 許可證

MIT License 