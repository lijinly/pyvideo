import uuid
from tinydb import Query
from utils.doc_db import doc_db_tiny,setup_logger

class cpy_store:
    
    """
    ""
    {
    "doc_id":sdsafa
    "user_id":"default",
    "body": {
      "Rhythm": "总时长 20 秒以内；3 秒钩子、15 秒爽点、5 秒互动",
      "style_tone": "亲切共鸣、社群化、口语化、短句、情绪词、无镜头描述",
      "structure": [
        {
          "description": "钩子",
          "method": "search:租车+主播"
        },
        {
          "description": "爽点",
          "method": "search:租车"
        },
        {
          "description": "互动",
          "method": "search:租车"
        }
      ]
    }
    }
    """
    def __init__(self): 
        self.table_name = doc_db_tiny.tables.copywrite_structure # "copy_write"   
        self.logger = setup_logger(name="copyright_structure")   
        pass
    
    def load_copywrites(self, user_id: str):
        # 创建数据库实例
        with doc_db_tiny() as db:
    
            # 获取指定表
            cpys = db.get_table(self.table_name)
            # 创建查询对象
            item = Query()
            # 执行查询 - 使用正确的TinyDB查询语法
            results = cpys.search(item.user_id == user_id)
            # 返回查询结果
            return results
        
    
    def save_copywrite(self,user_id:str,cws:dict):
        jsonObj = {**cws,**{"user_id":user_id}}
       
        doc_id = None
        if  "doc_id" in jsonObj:
            doc_id = jsonObj["doc_id"]
          
        with doc_db_tiny() as db:
            cpys = db.get_table(self.table_name)  
            
            if doc_id :
                item = Query()            
                cpys.update({**jsonObj},item.doc_id == doc_id)  
            else:               
                doc_id = str(uuid.uuid4())
                jsonObj = {**jsonObj,**{"doc_id": doc_id}}               
                cpys.insert(jsonObj)  

            db.db.storage.flush()
            
        return doc_id
    
    def delete_copywrite(self,doc_id:str):
        with doc_db_tiny() as db:
      
            # 获取指定表
            cpys = db.get_table(self.table_name) 
            item = Query()
            cpys.remove(item.doc_id == doc_id)
            db.db.storage.flush()