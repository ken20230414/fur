from app import app, db, User, Product, Order, OrderItem, CartItem
from datetime import datetime
from werkzeug.security import generate_password_hash

def modify_database():
    with app.app_context():
        print("\n=== 修改數據庫 ===")
        
        # 1. 修改用戶數據
        users = User.query.all()
        for user in users:
            print(f"\n修改用戶 {user.username} 的數據：")
            # 修改用戶名
            new_username = input(f"新的用戶名 (當前: {user.username}, 直接回車保持不變): ")
            if new_username:
                user.username = new_username
            
            # 修改電子郵件
            new_email = input(f"新的電子郵件 (當前: {user.email}, 直接回車保持不變): ")
            if new_email:
                user.email = new_email
            
            # 修改密碼
            new_password = input("新的密碼 (直接回車保持不變): ")
            if new_password:
                user.password_hash = generate_password_hash(new_password)
        
        # 2. 修改產品數據
        products = Product.query.all()
        for product in products:
            print(f"\n修改產品 {product.name} 的數據：")
            # 修改名稱
            new_name = input(f"新的產品名稱 (當前: {product.name}, 直接回車保持不變): ")
            if new_name:
                product.name = new_name
            
            # 修改價格
            new_price = input(f"新的價格 (當前: {product.price}, 直接回車保持不變): ")
            if new_price:
                product.price = float(new_price)
            
            # 修改庫存
            new_stock = input(f"新的庫存數量 (當前: {product.stock}, 直接回車保持不變): ")
            if new_stock:
                product.stock = int(new_stock)
        
        # 3. 修改訂單狀態
        orders = Order.query.all()
        for order in orders:
            print(f"\n修改訂單 #{order.id} 的狀態：")
            print(f"當前狀態: {order.status}")
            print("可選狀態: pending, processing, completed, cancelled")
            new_status = input("新的狀態 (直接回車保持不變): ")
            if new_status in ['pending', 'processing', 'completed', 'cancelled']:
                order.status = new_status
        
        # 確認修改
        confirm = input("\n確認要保存這些修改嗎？(y/n): ")
        if confirm.lower() == 'y':
            try:
                db.session.commit()
                print("數據修改成功！")
            except Exception as e:
                db.session.rollback()
                print(f"保存修改時出錯：{str(e)}")
        else:
            db.session.rollback()
            print("已取消修改。")

if __name__ == '__main__':
    print("開始修改數據庫...")
    modify_database()
    print("\n數據庫修改完成！") 