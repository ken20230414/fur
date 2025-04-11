from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import stripe
import qrcode
from io import BytesIO
import base64
import requests
import json
import time
import hashlib
import random
import string
import xmltodict
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import urllib.parse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///furniture.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Stripe支付配置
app.config['STRIPE_PUBLIC_KEY'] = 'your-stripe-public-key'
app.config['STRIPE_SECRET_KEY'] = 'your-stripe-secret-key'
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# 微信支付配置
WECHAT_APP_ID = 'your-wechat-app-id'
WECHAT_MCH_ID = 'your-wechat-merchant-id'
WECHAT_API_KEY = 'your-wechat-api-key'
WECHAT_NOTIFY_URL = 'https://your-domain.com/wechat/notify'

# 支付寶配置
ALIPAY_APP_ID = 'your-alipay-app-id'
ALIPAY_PRIVATE_KEY = 'your-alipay-private-key'
ALIPAY_PUBLIC_KEY = 'your-alipay-public-key'
ALIPAY_NOTIFY_URL = 'https://your-domain.com/alipay/notify'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 數據庫模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=0)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, cancelled
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product', backref='cart_items')

# 添加示例產品數據
def add_sample_products():
    sample_products = [
        {
            'name': '現代簡約沙發',
            'description': '採用高品質布料，舒適耐用，適合現代家居風格。',
            'price': 12999,
            'image_url': '/static/images/sofa.jpg',
            'category': '沙發',
            'stock': 10
        },
        {
            'name': '實木餐桌',
            'description': '精選實木製作，堅固耐用，可容納6-8人。',
            'price': 8999,
            'image_url': '/static/images/dining-table.jpg',
            'category': '餐桌',
            'stock': 15
        },
        {
            'name': '北歐風格床架',
            'description': '簡約設計，環保材質，提供舒適的睡眠體驗。',
            'price': 15999,
            'image_url': '/static/images/bed.jpg',
            'category': '床架',
            'stock': 8
        },
        {
            'name': '多功能書櫃',
            'description': '可調節層板，大容量儲物空間，適合各種書籍和裝飾品。',
            'price': 5999,
            'image_url': '/static/images/bookshelf.jpg',
            'category': '書櫃',
            'stock': 12
        },
        {
            'name': '人體工學辦公椅',
            'description': '可調節高度和靠背，提供良好的支撐，適合長時間工作。',
            'price': 3999,
            'image_url': '/static/images/chair.jpg',
            'category': '椅子',
            'stock': 20
        }
    ]
    
    try:
        for product_data in sample_products:
            if not Product.query.filter_by(name=product_data['name']).first():
                product = Product(**product_data)
                db.session.add(product)
        db.session.commit()
        print("示例產品數據添加成功！")
    except Exception as e:
        print(f"添加示例產品時出錯：{str(e)}")
        db.session.rollback()

def generate_order_number():
    """生成訂單號"""
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'ORDER{timestamp}{random_str}'

def generate_wechat_qrcode(order_id, total_amount):
    """生成微信支付二維碼"""
    # 生成隨機字符串
    nonce_str = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    # 構建簽名參數
    params = {
        'appid': WECHAT_APP_ID,
        'mch_id': WECHAT_MCH_ID,
        'nonce_str': nonce_str,
        'body': f'訂單支付 - {order_id}',
        'out_trade_no': order_id,
        'total_fee': int(total_amount * 100),  # 轉換為分
        'spbill_create_ip': request.remote_addr,
        'notify_url': WECHAT_NOTIFY_URL,
        'trade_type': 'NATIVE'
    }
    
    # 生成簽名
    sign = generate_wechat_sign(params)
    params['sign'] = sign
    
    # 調用微信支付統一下單接口
    response = requests.post(
        'https://api.mch.weixin.qq.com/pay/unifiedorder',
        data=params
    )
    
    if response.status_code == 200:
        # 解析返回的XML
        result = parse_xml(response.text)
        if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
            code_url = result.get('code_url')
            if code_url:
                # 生成二維碼圖片
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(code_url)
                qr.make(fit=True)
                
                # 創建圖片
                img = qr.make_image(fill_color="black", back_color="white")
                
                # 保存圖片到內存
                img_byte_arr = BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # 轉換為base64
                return f"data:image/png;base64,{base64.b64encode(img_byte_arr).decode()}"
    return None

def generate_alipay_qrcode(order_id, total_amount):
    """生成支付寶二維碼"""
    # 構建請求參數
    params = {
        'app_id': ALIPAY_APP_ID,
        'method': 'alipay.trade.precreate',
        'charset': 'utf-8',
        'sign_type': 'RSA2',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.0',
        'biz_content': json.dumps({
            'out_trade_no': order_id,
            'total_amount': str(total_amount),
            'subject': f'訂單支付 - {order_id}',
            'notify_url': ALIPAY_NOTIFY_URL
        })
    }
    
    # 生成簽名
    sign = generate_alipay_sign(params)
    params['sign'] = sign
    
    # 調用支付寶接口
    response = requests.post(
        'https://openapi.alipay.com/gateway.do',
        data=params
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('alipay_trade_precreate_response', {}).get('code') == '10000':
            qr_code = result['alipay_trade_precreate_response']['qr_code']
            if qr_code:
                # 生成二維碼圖片
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_code)
                qr.make(fit=True)
                
                # 創建圖片
                img = qr.make_image(fill_color="black", back_color="white")
                
                # 保存圖片到內存
                img_byte_arr = BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # 轉換為base64
                return f"data:image/png;base64,{base64.b64encode(img_byte_arr).decode()}"
    return None

def generate_wechat_sign(params):
    """生成微信支付簽名"""
    # 按字典序排序
    sorted_params = sorted(params.items())
    # 拼接參數
    stringA = '&'.join([f"{k}={v}" for k, v in sorted_params])
    # 拼接API密鑰
    stringSignTemp = f"{stringA}&key={WECHAT_API_KEY}"
    # MD5加密
    return hashlib.md5(stringSignTemp.encode('utf-8')).hexdigest().upper()

def generate_alipay_sign(params):
    """生成支付寶RSA2簽名"""
    try:
        # 按字典序排序參數
        sorted_params = sorted(params.items())
        
        # 構建待簽名字符串
        string_to_sign = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # 加載私鑰
        private_key = RSA.importKey(ALIPAY_PRIVATE_KEY)
        
        # 創建簽名對象
        signer = PKCS1_v1_5.new(private_key)
        
        # 計算SHA256哈希
        digest = SHA256.new()
        digest.update(string_to_sign.encode('utf-8'))
        
        # 生成簽名
        signature = signer.sign(digest)
        
        # Base64編碼
        return base64.b64encode(signature).decode('utf-8')
    except Exception as e:
        print(f"生成支付寶簽名錯誤: {str(e)}")
        return None

def parse_xml(xml_string):
    """解析XML字符串"""
    try:
        # 將XML字符串轉換為字典
        data = xmltodict.parse(xml_string)
        # 提取根節點下的數據
        return data.get('xml', {})
    except Exception as e:
        print(f"XML解析錯誤: {str(e)}")
        return {}

def verify_wechat_sign(data):
    """驗證微信支付簽名"""
    try:
        # 獲取簽名
        sign = data.pop('sign', None)
        if not sign:
            return False
            
        # 按字典序排序參數
        sorted_params = sorted(data.items())
        
        # 構建待驗證字符串
        string_to_verify = '&'.join([f"{k}={v}" for k, v in sorted_params])
        string_to_verify += f"&key={WECHAT_API_KEY}"
        
        # 計算MD5哈希
        calculated_sign = hashlib.md5(string_to_verify.encode('utf-8')).hexdigest().upper()
        
        # 比較簽名
        return calculated_sign == sign
    except Exception as e:
        print(f"驗證微信支付簽名錯誤: {str(e)}")
        return False

def verify_alipay_sign(data):
    """驗證支付寶RSA2簽名"""
    try:
        # 獲取簽名
        signature = data.pop('sign', None)
        if not signature:
            return False
            
        # 按字典序排序參數
        sorted_params = sorted(data.items())
        
        # 構建待驗證字符串
        string_to_verify = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # 加載公鑰
        public_key = RSA.importKey(ALIPAY_PUBLIC_KEY)
        
        # 創建驗證對象
        verifier = PKCS1_v1_5.new(public_key)
        
        # 計算SHA256哈希
        digest = SHA256.new()
        digest.update(string_to_verify.encode('utf-8'))
        
        # 驗證簽名
        return verifier.verify(digest, base64.b64decode(signature))
    except Exception as e:
        print(f"驗證支付寶簽名錯誤: {str(e)}")
        return False

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        # 获取购物车中的所有商品
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            flash('購物車為空', 'error')
            return redirect(url_for('cart'))
        
        # 计算总价
        total = sum(item.product.price * item.quantity for item in cart_items)
        
        try:
            # 创建订单
            order = Order(
                user_id=current_user.id,
                total_price=total,
                status='pending'
            )
            db.session.add(order)
            db.session.flush()  # 获取order.id
            
            # 创建订单项
            for cart_item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                db.session.add(order_item)
            
            # 清空购物车
            CartItem.query.filter_by(user_id=current_user.id).delete()
            
            db.session.commit()
            return redirect(url_for('payment', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            flash(f'創建訂單時出錯：{str(e)}', 'error')
            return redirect(url_for('cart'))
    
    return render_template('checkout.html')

@app.route('/payment/<int:order_id>', methods=['GET'])
@login_required
def payment(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('您無權訪問此訂單', 'danger')
        return redirect(url_for('index'))
    
    # 模擬生成支付二維碼
    wechat_qrcode_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAADICAYAAACtWK6eAAABhWlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw1AUhU9TpSIVBzuIOGSoThZERRy1CkWoEGqFVh1MXvoHTRqSFBdHwbXg4M9i1cHFWVcHV0EQ/AFxc3NSdJES70sKLWK88Hgf591zeO8+QKiXmWZ1jAOabpupRFzMZFdFrlf0YQ8w+QkQh8xYz9QkLcFjf7w4z0c+9OKwz0njxGZ1QyWeIJ4pGmX5nzjE8SmYVcJz4nGTLkj8yHXZ5TfOJYYFngk8q5kY8QxxWNo1Y1tyHmMq5hKzX+8S8j5xLNVZqjTqYEc5hCAQCCjQqKkGMjRqtJSo0G7bqGPB5C9+kqFyK+QqwuEGg5vrHMP9g/hVW3v4KjTg8R/4Yh0F6g9zYxgAY0D7Sx+3y9g4BLn+E+4PgtOcL6N1mQH6t0GL6z1tMYPgLtCo2/b3sWc0P0D/DNlq3QY8OoGLq7bmrwHXO4Ag0+6ZEiO5Kcp5PPA+xl9UwbovwV619zeWvs4fQDS1FXyBjg4BEYLlL3u8e7ezt7+PdPq7wd9dXH7j1QqQAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+gKDBQYJQvXQJQAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAAKElEQVR42u3BAQEAAACCIP+vbkhAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH4GJQAB9QZQ8QAAAABJRU5ErkJggg=="
    alipay_qrcode_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAADICAYAAACtWK6eAAABhWlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw1AUhU9TpSIVBzuIOGSoThZERRy1CkWoEGqFVh1MXvoHTRqSFBdHwbXg4M9i1cHFWVcHV0EQ/AFxc3NSdJES70sKLWK88Hgf591zeO8+QKiXmWZ1jAOabpupRFzMZFdFrlf0YQ8w+QkQh8xYz9QkLcFjf7w4z0c+9OKwz0njxGZ1QyWeIJ4pGmX5nzjE8SmYVcJz4nGTLkj8yHXZ5TfOJYYFngk8q5kY8QxxWNo1Y1tyHmMq5hKzX+8S8j5xLNVZqjTqYEc5hCAQCCjQqKkGMjRqtJSo0G7bqGPB5C9+kqFyK+QqwuEGg5vrHMP9g/hVW3v4KjTg8R/4Yh0F6g9zYxgAY0D7Sx+3y9g4BLn+E+4PgtOcL6N1mQH6t0GL6z1tMYPgLtCo2/b3sWc0P0D/DNlq3QY8OoGLq7bmrwHXO4Ag0+6ZEiO5Kcp5PPA+xl9UwbovwV619zeWvs4fQDS1FXyBjg4BEYLlL3u8e7ezt7+PdPq7wd9dXH7j1QqQAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+gKDBQYJQvXQJQAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAAKElEQVR42u3BAQEAAACCIP+vbkhAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH4GJQAB9QZQ8QAAAABJRU5ErkJggg=="
    
    return render_template('payment.html', 
                         order=order,
                         total=order.total_price,
                         wechat_qrcode_url=wechat_qrcode_url,
                         alipay_qrcode_url=alipay_qrcode_url)

@app.route('/wechat_pay/<int:order_id>')
@login_required
def wechat_pay(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('您無權訪問此訂單', 'danger')
        return redirect(url_for('index'))
    
    # 模擬生成微信支付二維碼
    # 實際應用中應該調用微信支付API
    try:
        # 更新訂單狀態
        order.status = 'paid'
        
        # 更新商品庫存
        product = order.items[0].product
        product.stock -= order.items[0].quantity
        
        db.session.commit()
        flash('微信支付成功！')
        return redirect(url_for('orders'))
    except Exception as e:
        db.session.rollback()
        flash(f'支付失敗：{str(e)}')
        return redirect(url_for('payment', order_id=order_id))

@app.route('/alipay/<int:order_id>')
@login_required
def alipay(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('您無權訪問此訂單', 'danger')
        return redirect(url_for('index'))
    
    # 模擬生成支付寶二維碼
    # 實際應用中應該調用支付寶API
    try:
        # 更新訂單狀態
        order.status = 'paid'
        
        # 更新商品庫存
        product = order.items[0].product
        product.stock -= order.items[0].quantity
        
        db.session.commit()
        flash('支付寶支付成功！')
        return redirect(url_for('orders'))
    except Exception as e:
        db.session.rollback()
        flash(f'支付失敗：{str(e)}')
        return redirect(url_for('payment', order_id=order_id))

@app.route('/payment_success')
@login_required
def payment_success():
    order_id = request.args.get('order_id')
    if not order_id:
        flash('訂單ID無效', 'error')
        return redirect(url_for('index'))
    
    order = Order.query.get(order_id)
    if not order or order.user_id != current_user.id:
        flash('訂單不存在或無權訪問', 'error')
        return redirect(url_for('index'))
    
    try:
        # 更新訂單狀態
        order.status = 'processing'
        
        # 更新商品庫存
        for item in order.items:
            product = item.product
            product.stock -= item.quantity
        
        db.session.commit()
        flash('支付成功！訂單正在處理中', 'success')
        return redirect(url_for('orders'))
    except Exception as e:
        db.session.rollback()
        flash(f'更新訂單狀態時出錯：{str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/payment_cancel')
@login_required
def payment_cancel():
    order_id = request.args.get('order_id')
    if not order_id:
        flash('訂單ID無效', 'error')
        return redirect(url_for('index'))
    
    order = Order.query.get(order_id)
    if not order or order.user_id != current_user.id:
        flash('訂單不存在或無權訪問', 'error')
        return redirect(url_for('index'))
    
    try:
        # 恢復庫存
        for item in order.items:
            product = item.product
            product.stock += item.quantity
        
        # 刪除訂單
        db.session.delete(order)
        db.session.commit()
        flash('訂單已取消', 'info')
        return redirect(url_for('cart'))
    except Exception as e:
        db.session.rollback()
        flash(f'取消訂單時出錯：{str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/orders')
@login_required
def orders():
    # 獲取當前用戶的所有訂單，按時間倒序排列
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('您無權查看此訂單')
        return redirect(url_for('orders'))
    return render_template('order_detail.html', order=order)

# 購物車相關路由
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > product.stock:
        flash('庫存不足')
        return redirect(url_for('product_detail', product_id=product_id))
    
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    flash('商品已加入購物車')
    return redirect(url_for('cart'))

@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('無權執行此操作')
        return redirect(url_for('cart'))
    
    quantity = int(request.form.get('quantity', 1))
    if quantity < 1:
        flash('數量必須大於0')
        return redirect(url_for('cart'))
    
    if quantity > cart_item.product.stock:
        flash('庫存不足')
        return redirect(url_for('cart'))
    
    cart_item.quantity = quantity
    db.session.commit()
    flash('購物車已更新')
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('無權執行此操作')
        return redirect(url_for('cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('商品已從購物車移除')
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('無效的用戶名或密碼')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if User.query.filter_by(username=username).first():
            flash('用戶名已存在')
            return redirect(url_for('register'))
        
        user = User(username=username, 
                   password_hash=generate_password_hash(password),
                   email=email)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/check_payment_status/<int:order_id>')
@login_required
def check_payment_status(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': '無權訪問'})
    
    if order.status == 'paid':
        return jsonify({'status': 'success'})
    return jsonify({'status': 'pending'})

@app.route('/wechat/notify', methods=['POST'])
def wechat_notify():
    """微信支付回調通知"""
    # 解析通知數據
    notify_data = parse_xml(request.data)
    
    # 驗證簽名
    if verify_wechat_sign(notify_data):
        # 更新訂單狀態
        order_id = notify_data.get('out_trade_no')
        order = Order.query.filter_by(id=order_id).first()
        if order and order.status == 'pending':
            order.status = 'paid'
            db.session.commit()
            return '<xml><return_code><![CDATA[SUCCESS]]></return_code></xml>'
    
    return '<xml><return_code><![CDATA[FAIL]]></return_code></xml>'

@app.route('/alipay/notify', methods=['POST'])
def alipay_notify():
    """支付寶回調通知"""
    # 解析通知數據
    notify_data = request.form.to_dict()
    
    # 驗證簽名
    if verify_alipay_sign(notify_data):
        # 更新訂單狀態
        order_id = notify_data.get('out_trade_no')
        order = Order.query.filter_by(id=order_id).first()
        if order and order.status == 'pending':
            order.status = 'paid'
            db.session.commit()
            return 'success'
    
    return 'fail'

def init_test_data():
    """初始化測試數據"""
    try:
        # 檢查是否已存在測試用戶
        test_user = User.query.filter_by(username='test').first()
        if not test_user:
            # 創建測試用戶
            test_user = User(
                username='test',
                password_hash=generate_password_hash('test123'),
                email='test@example.com'
            )
            db.session.add(test_user)
            db.session.commit()
            print("測試用戶創建成功！")
        
        # 檢查是否已存在測試產品
        test_product = Product.query.filter_by(name='測試產品').first()
        if not test_product:
            # 創建測試產品
            test_product = Product(
                name='測試產品',
                description='這是一個測試產品',
                price=100.0,
                image_url='/static/images/test.jpg',
                category='測試類別',
                stock=10
            )
            db.session.add(test_product)
            db.session.commit()
            print("測試產品創建成功！")
        
        # 創建測試訂單
        test_order = Order(
            user_id=test_user.id,
            total_price=100.0,
            status='pending'
        )
        db.session.add(test_order)
        db.session.commit()
        print("測試訂單創建成功！")
        
    except Exception as e:
        print(f"初始化測試數據時出錯：{str(e)}")
        db.session.rollback()

@app.route('/profile')
@login_required
def profile():
    # 獲取用戶的所有訂單，按時間倒序排列
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('profile.html', orders=orders)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # 檢查用戶名是否已被使用
        existing_user = User.query.filter(User.username == username, User.id != current_user.id).first()
        if existing_user:
            flash('該用戶名已被使用', 'danger')
            return redirect(url_for('edit_profile'))
        
        # 檢查郵箱是否已被使用
        existing_email = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_email:
            flash('該郵箱已被使用', 'danger')
            return redirect(url_for('edit_profile'))
        
        # 更新用戶資料
        current_user.username = username
        current_user.email = email
        db.session.commit()
        
        flash('個人資料更新成功', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html')

@app.route('/admin')
@login_required
def admin():
    # 檢查是否為管理員
    if not current_user.is_admin:
        flash('您沒有權限訪問此頁面')
        return redirect(url_for('index'))
    
    users = User.query.all()
    products = Product.query.all()
    orders = Order.query.all()
    return render_template('admin.html', users=users, products=products, orders=orders)

@app.route('/admin/user/<int:user_id>', methods=['GET', 'PUT'])
@login_required
def admin_user(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '沒有權限'})
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email
        })
    
    if request.method == 'PUT':
        data = request.get_json()
        
        # 檢查用戶名是否已被使用
        if data.get('username') and data['username'] != user.username:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                return jsonify({'success': False, 'message': '用戶名已被使用'})
            user.username = data['username']
        
        # 檢查電子郵件是否已被使用
        if data.get('email') and data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({'success': False, 'message': '電子郵件已被使用'})
            user.email = data['email']
        
        # 更新密碼（如果提供）
        if data.get('password'):
            user.password_hash = generate_password_hash(data['password'])
        
        try:
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/product/<int:product_id>', methods=['GET', 'PUT'])
@login_required
def admin_product(product_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '沒有權限'})
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'category': product.category
        })
    
    if request.method == 'PUT':
        data = request.get_json()
        
        # 更新產品信息
        if data.get('name'):
            product.name = data['name']
        if data.get('price'):
            product.price = float(data['price'])
        if data.get('stock'):
            product.stock = int(data['stock'])
        if data.get('category'):
            product.category = data['category']
        
        try:
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/order/<int:order_id>', methods=['GET', 'PUT'])
@login_required
def admin_order(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '沒有權限'})
    
    order = Order.query.get_or_404(order_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': order.id,
            'user': {'username': order.user.username},
            'total_price': order.total_price,
            'status': order.status,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items': [{
                'product': {'name': item.product.name},
                'quantity': item.quantity,
                'price': item.price
            } for item in order.items]
        })
    
    if request.method == 'PUT':
        data = request.get_json()
        
        # 更新訂單狀態
        if data.get('status') in ['pending', 'processing', 'completed', 'cancelled']:
            order.status = data['status']
        
        try:
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 检查是否已经有用户
        if not User.query.first():
            # 创建测试用户
            test_user = User(
                username='test_user',
                email='test@example.com'
            )
            test_user.password_hash = generate_password_hash('password123')
            db.session.add(test_user)
            db.session.commit()
            
            # 添加示例产品
            add_sample_products()
            
            print("數據庫初始化完成！")
    
    app.run(debug=True) 