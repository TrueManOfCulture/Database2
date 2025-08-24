from pymongo import MongoClient
from bson.objectid import ObjectId

class ProdutoService:
    def __init__(self):
        self.client = MongoClient('mongodb://AdministradorSite:pass@localhost:27017/BD2_TP')
        self.db = self.client['BD2_TP']
        self.collection = self.db['produto']
        self.avaliacoes_collection = self.db['avaliacoes']

    def list_produtos(self, search=None, categoria=None, avaliacao=None):
        """List produtos with optional filtering by search, category, and average rating"""
        query = {}

        # Filter by search text
        if search:
            query["nome"] = {"$regex": search, "$options": "i"}

        # Filter by category
        if categoria:
            query["categoria"] = categoria

        produtos = []
        for p in self.collection.find(query):
            p["id"] = str(p["_id"])

            # Compute average avaliação
            avals = list(self.avaliacoes_collection.find({"produto_id": p["_id"]}))
            if avals:
                media = sum(a["nota"] for a in avals) / len(avals)
                p["media_avaliacao"] = media
            else:
                p["media_avaliacao"] = None

            # Filter by minimum average rating if provided
            if avaliacao:
                try:
                    min_avaliacao = float(avaliacao)
                    if not p["media_avaliacao"] or p["media_avaliacao"] < min_avaliacao:
                        continue  # skip this product
                except ValueError:
                    pass  # ignore invalid rating filter

            produtos.append(p)

        return produtos

    def get_categorias(self):
        """Get list of unique categories"""
        return self.collection.distinct("categoria")

    def get_produto(self, produto_id):
        produto = self.collection.find_one({"_id": ObjectId(produto_id)})
        if produto:
            produto["id"] = str(produto["_id"])
        return produto

    def create_produto(self, produto_data):
        return self.collection.insert_one(produto_data)

    def update_produto(self, produto_id, update_data):
        return self.collection.update_one(
            {"_id": ObjectId(produto_id)}, 
            {"$set": update_data}
        )

    def delete_produto(self, produto_id):
        return self.collection.delete_one({"_id": ObjectId(produto_id)})