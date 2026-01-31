from datetime import datetime
from web.extensions import sql_db

class User(sql_db.Model):
    __tablename__ = 'users'
    
    id = sql_db.Column(sql_db.Integer, primary_key=True)
    username = sql_db.Column(sql_db.String(80), nullable=False)
    password = sql_db.Column(sql_db.String(80), nullable=False)
    email = sql_db.Column(sql_db.String(120), unique=True, nullable=False)
    created_at = sql_db.Column(sql_db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典，用于JSON序列化"""
        return {
            'id': self.id,
            'username': self.username,  # 修复属性名错误
            'password':self.password,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }


class UserFile(sql_db.Model):
    __tablename__ = 'user_files'
    
    id = sql_db.Column(sql_db.Integer, primary_key=True)
    file_path = sql_db.Column(sql_db.String(255), nullable=False)
    userid = sql_db.Column(sql_db.Integer, sql_db.ForeignKey('users.id'), nullable=False)
    file_count = sql_db.Column(sql_db.Integer, default=0)
    batch_number = sql_db.Column(sql_db.String(50), nullable=True)
    folder_name = sql_db.Column(sql_db.String(100), nullable=True)  # 新增文件夹名称字段
    upload_time = sql_db.Column(sql_db.Float, nullable=False)
