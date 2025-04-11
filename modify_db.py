from app import app, db, User, Product, Order, OrderItem, CartItem
from datetime import datetime
from werkzeug.security import generate_password_hash
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

class DatabaseModifier:
    def __init__(self, root):
        self.root = root
        self.root.title("數據庫修改工具")
        self.root.geometry("800x600")
        
        # 創建應用程序上下文
        self.ctx = app.app_context()
        self.ctx.push()
        
        # 創建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 創建標籤頁
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 創建用戶標籤頁
        self.user_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.user_frame, text="用戶管理")
        
        # 創建產品標籤頁
        self.product_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.product_frame, text="產品管理")
        
        # 創建訂單標籤頁
        self.order_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.order_frame, text="訂單管理")
        
        # 初始化各個標籤頁
        self.init_user_tab()
        self.init_product_tab()
        self.init_order_tab()
        
        # 添加保存按鈕
        self.save_button = ttk.Button(self.main_frame, text="保存所有修改", command=self.save_changes)
        self.save_button.grid(row=1, column=0, pady=10)
        
        # 加載數據
        self.load_data()
        
        # 設置窗口關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        # 關閉應用程序上下文
        self.ctx.pop()
        self.root.destroy()
    
    def init_user_tab(self):
        # 創建用戶表格
        columns = ('id', 'username', 'email', 'password', 'is_admin')
        self.user_tree = ttk.Treeview(self.user_frame, columns=columns, show='headings')
        
        # 設置列標題
        self.user_tree.heading('id', text='ID')
        self.user_tree.heading('username', text='用戶名')
        self.user_tree.heading('email', text='電子郵件')
        self.user_tree.heading('password', text='密碼')
        self.user_tree.heading('is_admin', text='管理員')
        
        # 設置列寬
        self.user_tree.column('id', width=50)
        self.user_tree.column('username', width=150)
        self.user_tree.column('email', width=200)
        self.user_tree.column('password', width=150)
        self.user_tree.column('is_admin', width=80)
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(self.user_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滾動條
        self.user_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 使表格可編輯
        self.user_tree.bind('<Double-1>', self.edit_user_item)
    
    def init_product_tab(self):
        # 創建產品表格
        columns = ('id', 'name', 'description', 'price', 'stock', 'category')
        self.product_tree = ttk.Treeview(self.product_frame, columns=columns, show='headings')
        
        # 設置列標題
        self.product_tree.heading('id', text='ID')
        self.product_tree.heading('name', text='名稱')
        self.product_tree.heading('description', text='描述')
        self.product_tree.heading('price', text='價格')
        self.product_tree.heading('stock', text='庫存')
        self.product_tree.heading('category', text='類別')
        
        # 設置列寬
        self.product_tree.column('id', width=50)
        self.product_tree.column('name', width=150)
        self.product_tree.column('description', width=200)
        self.product_tree.column('price', width=80)
        self.product_tree.column('stock', width=80)
        self.product_tree.column('category', width=100)
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(self.product_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滾動條
        self.product_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 使表格可編輯
        self.product_tree.bind('<Double-1>', self.edit_product_item)
    
    def init_order_tab(self):
        # 創建訂單表格
        columns = ('id', 'user_id', 'total_price', 'status', 'created_at')
        self.order_tree = ttk.Treeview(self.order_frame, columns=columns, show='headings')
        
        # 設置列標題
        self.order_tree.heading('id', text='ID')
        self.order_tree.heading('user_id', text='用戶ID')
        self.order_tree.heading('total_price', text='總價')
        self.order_tree.heading('status', text='狀態')
        self.order_tree.heading('created_at', text='創建時間')
        
        # 設置列寬
        self.order_tree.column('id', width=50)
        self.order_tree.column('user_id', width=80)
        self.order_tree.column('total_price', width=100)
        self.order_tree.column('status', width=100)
        self.order_tree.column('created_at', width=150)
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(self.order_frame, orient=tk.VERTICAL, command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滾動條
        self.order_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 使表格可編輯
        self.order_tree.bind('<Double-1>', self.edit_order_item)
    
    def load_data(self):
        # 加載用戶數據
        users = User.query.all()
        for user in users:
            self.user_tree.insert('', 'end', values=(
                user.id,
                user.username,
                user.email,
                '********',
                '是' if hasattr(user, 'is_admin') and user.is_admin else '否'
            ))
        
        # 加載產品數據
        products = Product.query.all()
        for product in products:
            self.product_tree.insert('', 'end', values=(
                product.id,
                product.name,
                product.description or '',
                product.price,
                product.stock,
                product.category or ''
            ))
        
        # 加載訂單數據
        orders = Order.query.all()
        for order in orders:
            self.order_tree.insert('', 'end', values=(
                order.id,
                order.user_id,
                order.total_price,
                order.status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ))
    
    def edit_user_item(self, event):
        item = self.user_tree.selection()[0]
        values = self.user_tree.item(item, 'values')
        
        # 創建編輯窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title("編輯用戶")
        
        # 創建表單
        ttk.Label(edit_window, text="用戶名:").grid(row=0, column=0, padx=5, pady=5)
        username_entry = ttk.Entry(edit_window)
        username_entry.grid(row=0, column=1, padx=5, pady=5)
        username_entry.insert(0, values[1])
        
        ttk.Label(edit_window, text="電子郵件:").grid(row=1, column=0, padx=5, pady=5)
        email_entry = ttk.Entry(edit_window)
        email_entry.grid(row=1, column=1, padx=5, pady=5)
        email_entry.insert(0, values[2])
        
        ttk.Label(edit_window, text="密碼:").grid(row=2, column=0, padx=5, pady=5)
        password_entry = ttk.Entry(edit_window, show="*")
        password_entry.grid(row=2, column=1, padx=5, pady=5)
        
        is_admin_var = tk.BooleanVar(value=values[4] == '是')
        ttk.Checkbutton(edit_window, text="管理員", variable=is_admin_var).grid(row=3, column=0, columnspan=2, pady=5)
        
        def save():
            user = User.query.get(int(values[0]))
            if user:
                user.username = username_entry.get()
                user.email = email_entry.get()
                if password_entry.get():
                    user.set_password(password_entry.get())
                user.is_admin = is_admin_var.get()
                db.session.commit()
                self.user_tree.item(item, values=(
                    user.id,
                    user.username,
                    user.email,
                    '********',
                    '是' if user.is_admin else '否'
                ))
                edit_window.destroy()
                messagebox.showinfo("成功", "用戶信息已更新")
        
        ttk.Button(edit_window, text="保存", command=save).grid(row=4, column=0, columnspan=2, pady=10)
    
    def edit_product_item(self, event):
        item = self.product_tree.selection()[0]
        values = self.product_tree.item(item, 'values')
        
        # 創建編輯窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title("編輯產品")
        
        # 創建表單
        ttk.Label(edit_window, text="名稱:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(edit_window)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.insert(0, values[1])
        
        ttk.Label(edit_window, text="描述:").grid(row=1, column=0, padx=5, pady=5)
        description_entry = ScrolledText(edit_window, width=30, height=5)
        description_entry.grid(row=1, column=1, padx=5, pady=5)
        description_entry.insert('1.0', values[2])
        
        ttk.Label(edit_window, text="價格:").grid(row=2, column=0, padx=5, pady=5)
        price_entry = ttk.Entry(edit_window)
        price_entry.grid(row=2, column=1, padx=5, pady=5)
        price_entry.insert(0, values[3])
        
        ttk.Label(edit_window, text="庫存:").grid(row=3, column=0, padx=5, pady=5)
        stock_entry = ttk.Entry(edit_window)
        stock_entry.grid(row=3, column=1, padx=5, pady=5)
        stock_entry.insert(0, values[4])
        
        ttk.Label(edit_window, text="類別:").grid(row=4, column=0, padx=5, pady=5)
        category_entry = ttk.Entry(edit_window)
        category_entry.grid(row=4, column=1, padx=5, pady=5)
        category_entry.insert(0, values[5])
        
        def save():
            product = Product.query.get(int(values[0]))
            if product:
                product.name = name_entry.get()
                product.description = description_entry.get('1.0', tk.END).strip()
                product.price = float(price_entry.get())
                product.stock = int(stock_entry.get())
                product.category = category_entry.get()
                db.session.commit()
                self.product_tree.item(item, values=(
                    product.id,
                    product.name,
                    product.description,
                    product.price,
                    product.stock,
                    product.category
                ))
                edit_window.destroy()
                messagebox.showinfo("成功", "產品信息已更新")
        
        ttk.Button(edit_window, text="保存", command=save).grid(row=5, column=0, columnspan=2, pady=10)
    
    def edit_order_item(self, event):
        item = self.order_tree.selection()[0]
        values = self.order_tree.item(item, 'values')
        
        # 創建編輯窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title("編輯訂單")
        
        # 創建表單
        ttk.Label(edit_window, text="總價:").grid(row=0, column=0, padx=5, pady=5)
        total_price_entry = ttk.Entry(edit_window)
        total_price_entry.grid(row=0, column=1, padx=5, pady=5)
        total_price_entry.insert(0, values[2])
        
        ttk.Label(edit_window, text="狀態:").grid(row=1, column=0, padx=5, pady=5)
        status_var = tk.StringVar(value=values[3])
        status_combo = ttk.Combobox(edit_window, textvariable=status_var)
        status_combo['values'] = ('pending', 'processing', 'completed', 'cancelled')
        status_combo.grid(row=1, column=1, padx=5, pady=5)
        
        def save():
            order = Order.query.get(int(values[0]))
            if order:
                order.total_price = float(total_price_entry.get())
                order.status = status_var.get()
                db.session.commit()
                self.order_tree.item(item, values=(
                    order.id,
                    order.user_id,
                    order.total_price,
                    order.status,
                    order.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ))
                edit_window.destroy()
                messagebox.showinfo("成功", "訂單信息已更新")
        
        ttk.Button(edit_window, text="保存", command=save).grid(row=2, column=0, columnspan=2, pady=10)
    
    def save_changes(self):
        messagebox.showinfo("成功", "所有修改已保存")

if __name__ == '__main__':
    root = tk.Tk()
    app = DatabaseModifier(root)
    root.mainloop() 