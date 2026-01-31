import os
from pathlib import Path
import shutil
from datetime import datetime
from tinydb import TinyDB, Query, where
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from .logs import setup_logger

class doc_db_tiny:
    """
    TinyDB 封装类，提供更便捷的数据库操作接口
    支持自动备份、简化查询、事务模拟等功能
    """
    
    class tables:
        copywrite_structure = "copywrite_structure"
        avatar_metas = "avatar_metas"
    
    def __init__(self):
        """
        warn：init 时，连接已打开
        不在with作用域内使用时，必须手工close
        
        :param db_path: 数据库文件路径
        :param backup_dir: 备份文件目录
        :param auto_backup: 是否在初始化时自动备份
        """
        backup_dir='backups'
        auto_backup=False                                    
        db_path =  os.path.join( ".asset_space", ".dbs" , "doc_db" ,"database.json" )
        
        # 确保父级路劲存在
        root_dir = Path(db_path).parent
        root_dir.mkdir(exist_ok=True)
        # 确保备份路径存在
        backup_dir = os.path.join( root_dir,backup_dir)
        os.makedirs( backup_dir ,exist_ok= True)
        
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        self.logger = setup_logger(name= "tiny_db")
  
     
         # 使用缓存中间件提高性能
        self.db = TinyDB(
            self.db_path,
            storage=CachingMiddleware(JSONStorage),
            ensure_ascii=False  # 支持中文
        )      
      
        # 自动备份
        if auto_backup:
            self.backup()    
    

    def get_table(self, table_name='_default'):
        """
        获取数据表
        
        :param table_name: 表名，默认为默认表
        :return: 数据表对象
        """
        return self.db.table(table_name)
    
    def insert(self, data, table_name='_default'):
        """
        插入数据
        
        :param data: 要插入的数据，可以是字典或字典列表
        :param table_name: 表名
        :return: 插入的ID或ID列表
        """ 
        table = self.get_table(table_name)
        if isinstance(data, list):
            ids = table.insert_multiple(data) 
            return ids
        else:
            doc_id = table.insert(data) 
            return doc_id
    
    
    def query(self, conditions=None, table_name='_default', sort_by=None, reverse=False, limit=None):
        """
        查询数据
        
        :param conditions: 查询条件，如 where('age') > 18 或多个条件的组合
        :param table_name: 表名
        :param sort_by: 排序字段
        :param reverse: 是否倒序
        :param limit: 返回结果数量限制
        :return: 查询结果列表
        """
  
        table = self.get_table(table_name)
        query = table
        
        # 应用查询条件
        if conditions is not None:
            query = query.search(conditions)
        else:
            query = query.all()
        
        # 排序
        if sort_by is not None:
            query.sort(key=lambda x: x.get(sort_by), reverse=reverse)
        
        # 限制结果数量
        if limit is not None:
            query = query[:limit]
            

        return query
     
    
    def update(self, data, conditions, table_name='_default'):
        """
        更新数据
        
        :param data: 要更新的数据字典
        :param conditions: 更新条件
        :param table_name: 表名
        :return: 更新的记录数
        """
 
        table = self.get_table(table_name)
        count = table.update(data, conditions) 
        return count
       
    
    def delete(self, conditions, table_name='_default'):
        """
        删除数据
        
        :param conditions: 删除条件
        :param table_name: 表名
        :return: 删除的记录数
        """
  
        table = self.get_table(table_name)
        count = table.remove(conditions)
        return count 

    def get_by_id(self, doc_id, table_name='_default'):
        """
        通过ID获取单条记录
        
        :param doc_id: 记录ID
        :param table_name: 表名
        :return: 记录字典，如果不存在则返回None
        """
   
        table = self.get_table(table_name)
        result = table.get(doc_id=doc_id)
    
        return result
 
    
    def count(self, conditions=None, table_name='_default'):
        """
        统计记录数量
        
        :param conditions: 统计条件，None则统计所有
        :param table_name: 表名
        :return: 记录数量
        """
  
        table = self.get_table(table_name)
        if conditions:
            count = table.count(conditions)
        else:
            count = len(table)

        return count
 
    
    def backup(self, backup_name=None):
        """
        备份数据库
        
        :param backup_name: 备份文件名，None则使用当前时间戳
        :return: 备份文件路径
        """

        if not os.path.exists(self.db_path):   
            return None
            
        # 生成备份文件名
        if not backup_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(self.db_path)
            name, ext = os.path.splitext(filename)
            backup_name = f"{name}_{timestamp}{ext}"
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        # 执行备份
        shutil.copy2(self.db_path, backup_path)

        return backup_path
 
    
    def clear_table(self, table_name='_default', confirm=False):
        """
        清空表数据
        
        :param table_name: 表名
        :param confirm: 是否确认操作，为True才执行
        :return: 是否成功
        """
        if not confirm:
            return False
            
    
        table = self.get_table(table_name)
        table.truncate()
        return True
    
    
    def close(self):
        """关闭数据库连接"""
        if self.db:
            # 确保缓存数据写入磁盘
            self.db.storage.flush() 
            self.db = None
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出时关闭连接"""
        self.close()
        if exc_type: 
            pass


# 使用示例
if __name__ == "__main__":
    
    # 创建数据库实例，自动备份
    with doc_db_tiny() as db:
        # 插入数据
        user1 = {
            'name': '张三',
            'age': 25,
            'email': 'zhangsan@example.com',
            'hobbies': ['阅读', '运动']
        }
        
        user2 = {
            'name': '李四',
            'age': 30,
            'email': 'lisi@example.com',
            'hobbies': ['音乐', '旅行']
        }
        
        # 插入单条数据
        user1_id = db.insert(user1, 'users')
        print(f"插入用户ID: {user1_id}")
        
        # 插入多条数据
        user_ids = db.insert([user2], 'users')
        print(f"插入用户IDs: {user_ids}")
        
        # 查询所有用户
        all_users = db.query(table_name='users')
        print(f"所有用户: {all_users}")
        
        # 条件查询 - 年龄大于28的用户
        mature_users = db.query(
            conditions=where('age') > 28,
            table_name='users'
        )
        print(f"年龄大于28的用户: {mature_users}")
        
        # 更新数据 - 更新张三的年龄
        db.update(
            data={'age': 26},
            conditions=where('name') == '张三',
            table_name='users'
        )
        
        # 按ID查询
        updated_user = db.get_by_id(user1_id, 'users')
        print(f"更新后的用户: {updated_user}")
        
        # 统计用户数量
        user_count = db.count(table_name='users')
        print(f"用户总数: {user_count}")
        
        # 排序查询
        sorted_users = db.query(
            table_name='users',
            sort_by='age',
            reverse=True
        )
        print(f"按年龄排序的用户: {sorted_users}")
        
        # 删除数据
        # db.delete(conditions=where('name') == '李四', table_name='users')
