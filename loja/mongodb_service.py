# services/mongodb_service.py
from pymongo import MongoClient

class ProdutoService:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['techmart']
        self.collection = self.db['produtos']
    
    def get_produto(self, produto_id):
        return self.collection.find_one({"_id": produto_id})
    
    def create_produto(self, produto_data):
        return self.collection.insert_one(produto_data)
    
    def update_produto(self, produto_id, update_data):
        return self.collection.update_one(
            {"_id": produto_id}, 
            {"$set": update_data}
        )