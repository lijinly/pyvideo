from datetime import datetime
from werkzeug.security import generate_password_hash
from web.extensions import sql_db
from web.models.users import User

def init_data():
    """初始化数据库，确保在首次访问前执行"""
    # 检查是否已有用户数据
    if User.query.count() == 0:
        print("数据库中没有用户数据，开始初始化...")
        
        # 创建初始用户
        users = [
            {
                'username': 'admin',
                'password': 'admin123',  # 会被哈希处理
                'email': 'admin@example.com'
            },
            {
                'username': 'user1',
                'password': 'user123',
                'email': 'user1@example.com'
            } 
        ]
        
        # 添加用户到数据库
        for user_data in users:
            user = User(
                username=user_data['username'],
                # 哈希处理密码，提高安全性
                password=generate_password_hash(user_data['password'], method='pbkdf2:sha256'),
                email=user_data['email'],
                created_at=datetime.utcnow()
            )
            sql_db.session.add(user)
        
        try:
            sql_db.session.commit()
            print(f"成功初始化 {len(users)} 个用户数据")
        except Exception as e:
            sql_db.session.rollback()
            print(f"初始化数据失败: {str(e)}")
    else:
        print("数据库中已有用户数据，跳过初始化")

 
    
 
    