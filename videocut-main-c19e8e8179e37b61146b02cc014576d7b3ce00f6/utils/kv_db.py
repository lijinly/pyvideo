import os
from pathlib import Path
import lmdb
import pickle
from typing import Any, Optional, Iterator, Tuple

class kv_db_lmdb:
    """
    warn：init 时，连接已打开
    不在with作用域内使用时，必须手工close
    """
    class sub_dbs:
        cache_db = "cache_db"
        
    def __init__(
        self,
        map_size: int = 1024**3,  # 默认 1GB
        max_dbs: int = 10,
        readonly: bool = False
    ):
        """
        初始化 LMDB 数据库环境
        :param path: 数据库路径
        :param map_size: 最大存储空间（字节）
        :param max_dbs: 子数据库数量（0表示不启用）
        :param readonly: 只读模式
        """
                                  
        db_dir =  os.path.join( ".asset_space" , ".dbs" ,"kv_db" )
        
         
        os.makedirs(db_dir,exist_ok=True)
        
        self.env = lmdb.open(
            db_dir,
            map_size=map_size,
            max_dbs=max_dbs,
            readonly=readonly,
            lock=True,  # 启用多进程锁
            metasync=False  # 提升写入性能
        )
        self.subdbs = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_subdb(self, name: str) -> lmdb._Database:
        """获取或创建子数据库（表）"""
        if name not in self.subdbs:
            self.subdbs[name] = self.env.open_db(name.encode())
        return self.subdbs[name]

    def put(
        self,
        key: bytes,
        value: Any,
        subdb: Optional[str] = None,
        serialize: bool = True
    ) -> bool:
        """
        写入键值对
        :param key: 字节类型键
        :param value: 任意类型值（可序列化）
        :param subdb: 子数据库名称
        :param serialize: 是否自动序列化
        :return: 操作是否成功
        """
        db = self.get_subdb(subdb) if subdb else None
        with self.env.begin(write=True, db=db) as txn:
            try:
                txn.put(key, pickle.dumps(value) if serialize else value)
                return True
            except lmdb.Error:
                return False

    def get(
        self,
        key: bytes,
        subdb: Optional[str] = None,
        deserialize: bool = True
    ) -> Optional[Any]:
        """
        读取键值
        :param key: 字节类型键
        :param subdb: 子数据库名称
        :param deserialize: 是否自动反序列化
        :return: 值（失败返回None）
        """
        db = self.get_subdb(subdb) if subdb else None
        with self.env.begin(db=db) as txn:
            data = txn.get(key)
            if data is None:
                return None
            return pickle.loads(data) if deserialize else data

    def delete(self, key: bytes, subdb: Optional[str] = None) -> bool:
        """删除键值"""
        db = self.get_subdb(subdb) if subdb else None
        with self.env.begin(write=True, db=db) as txn:
            return txn.delete(key)

    def batch_write(
        self,
        items: list,
        subdb: Optional[str] = None,
        serialize: bool = True
    ) -> int:
        """
        批量写入键值对
        :param items: [(key1, value1), (key2, value2)...]
        :param subdb: 子数据库名称
        :param serialize: 是否序列化
        :return: 成功写入数量
        """
        db = self.get_subdb(subdb) if subdb else None
        with self.env.begin(write=True, db=db) as txn:
            count = 0
            for key, value in items:
                if txn.put(key, pickle.dumps(value) if serialize else value):
                    count += 1
            return count

    def items(
        self,
        subdb: Optional[str] = None,
        deserialize: bool = True
    ) -> Iterator[Tuple[bytes, Any]]:
        """
        遍历数据库返回键值生成器
        :param subdb: 子数据库名称
        :param deserialize: 是否反序列化值
        """
        db = self.get_subdb(subdb) if subdb else None
        with self.env.begin(db=db) as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                yield key, pickle.loads(value) if deserialize else value

    def close(self):
        """关闭数据库释放资源"""
        if self.env:
            self.env.close()
            self.env = None

# 示例用法
if __name__ == "__main__":
    # 初始化数据库（自动创建）
    with kv_db_lmdb( map_size=10**8) as db:
    
        # 写入数据（自动序列化）
        db.put(b"user:1", {"name": "Alice", "age": 30})
        db.put(b"config:debug_mode", True, subdb="settings")
        
        # 读取数据
        user = db.get(b"user:1")  # 返回字典
        debug_mode = db.get(b"config:debug_mode", subdb="settings")  # 返回布尔值
        
        # 批量写入
        items = [(f"key_{i}".encode(), i * 100) for i in range(100)]
        db.batch_write(items, subdb="batch_data")
        
        # 遍历子数据库
        for key, value in db.items(subdb="batch_data"):
            print(f"{key.decode()}: {value}")
        
        # 删除数据
        db.delete(b"user:1")
        
        # 自动关闭（通过上下文管理器）