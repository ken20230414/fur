from app import app, db, User, Product, Order, OrderItem, CartItem
from datetime import datetime

def view_database():
    with app.app_context():
        print("\n=== 用戶數據 ===")
        users = User.query.all()
        for user in users:
            print(f"ID: {user.id}")
            print(f"用戶名: {user.username}")
            print(f"電子郵件: {user.email}")
            print(f"註冊時間: {user.created_at}")
            print("---")

        print("\n=== 產品數據 ===")
        products = Product.query.all()
        for product in products:
            print(f"ID: {product.id}")
            print(f"名稱: {product.name}")
            print(f"描述: {product.description}")
            print(f"價格: NT$ {product.price}")
            print(f"類別: {product.category}")
            print(f"庫存: {product.stock}")
            print(f"圖片URL: {product.image_url}")
            print("---")

        print("\n=== 訂單數據 ===")
        orders = Order.query.all()
        for order in orders:
            print(f"ID: {order.id}")
            print(f"用戶ID: {order.user_id}")
            print(f"總價: NT$ {order.total_price}")
            print(f"創建時間: {order.created_at}")
            print(f"狀態: {order.status}")
            print("訂單項目:")
            for item in order.items:
                print(f"  - 產品ID: {item.product_id}")
                print(f"    數量: {item.quantity}")
                print(f"    單價: NT$ {item.price}")
            print("---")

        print("\n=== 購物車項目 ===")
        cart_items = CartItem.query.all()
        for item in cart_items:
            print(f"ID: {item.id}")
            print(f"用戶ID: {item.user_id}")
            print(f"產品ID: {item.product_id}")
            print(f"數量: {item.quantity}")
            print("---")

if __name__ == '__main__':
    print("開始查看數據庫內容...")
    view_database()
    print("\n數據庫查看完成！") 