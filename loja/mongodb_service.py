from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

class ProdutoService:
    def __init__(self):
        self.client = MongoClient('mongodb://AdministradorSite:pass@localhost:27017/BD2_TP')
        self.db = self.client['BD2_TP']
        self.produtos_collection = self.db['produto']
        self.promocoes_collection = self.db['promocao']
        self.avaliacoes_collection = self.db['avaliacao']

    def list_produtos(self, search=None, categoria=None, avaliacao=None):
        query = {}

        if search:
            query["nome"] = {"$regex": search, "$options": "i"}

        if categoria:
            query["categoria"] = categoria

        produtos = []
        for p in self.produtos_collection.find(query):
            p["id"] = str(p["_id"])

            avals = list(self.avaliacoes_collection.find({"produto_id": p["_id"]}))
            if avals:
                media = sum(a["nota"] for a in avals) / len(avals)
                p["media_avaliacao"] = media
            else:
                p["media_avaliacao"] = None

            if avaliacao:
                try:
                    min_avaliacao = float(avaliacao)
                    if not p["media_avaliacao"] or p["media_avaliacao"] < min_avaliacao:
                        continue 
                except ValueError:
                    pass

            produtos.append(p)

        return produtos

    def get_categorias(self):
        
        return self.produtos_collection.distinct("categoria")

    def get_produto(self, produto_id):
        produto = self.produtos_collection.find_one({"_id": produto_id})
        if produto:
            produto["id"] = str(produto["_id"])
            avals = list(self.avaliacoes_collection.find({"produto_id": produto["_id"]}))
            if avals:
                media = sum(a["nota"] for a in avals) / len(avals)
                produto["media_avaliacao"] = round(media, 2)
                produto["total_avaliacoes"] = len(avals)
            else:
                produto["media_avaliacao"] = None
                produto["total_avaliacoes"] = 0
            promocao_ativa = self.get_promocao_ativa(produto["_id"])
            if promocao_ativa:
                produto["promocao"] = promocao_ativa
                produto["preco_promocional"] = self.calcular_preco_promocional(produto["preco"], promocao_ativa)
        return produto

    def create_produto(self, produto_data):
        return self.produtos_collection.insert_one(produto_data)

    def update_produto(self, produto_id, update_data):
        return self.produtos_collection.update_one(
            {"_id": produto_id}, 
            {"$set": update_data}
        )

    def delete_produto(self, produto_id):
        return self.produtos_collection.delete_one({"_id": produto_id})
    
    def list_promocoes(self, ativas_apenas=False):
        """List all promotions, optionally filter for active ones only"""
        query = {}
        if ativas_apenas:
            agora = datetime.now()
            query = {
                "data_inicio": {"$lte": agora},
                "data_fim": {"$gte": agora}
            }
        
        promocoes = []
        for p in self.promocoes_collection.find(query):
            p["id"] = str(p["_id"])
            # Add product name for reference
            produto = self.produtos_collection.find_one({"_id": p["produto_id"]})
            if produto:
                p["produto_nome"] = produto["nome"]
            promocoes.append(p)
        
        return promocoes

    def get_promocao(self, promocao_id):
        promocao = self.promocoes_collection.find_one({"_id": ObjectId(promocao_id)})
        if promocao:
            promocao["id"] = str(promocao["_id"])
            produto = self.produtos_collection.find_one({"_id": promocao["produto_id"]})
            if produto:
                promocao["produto"] = produto
        return promocao

    def get_promocao_ativa(self, produto_id):
        """Get active promotion for a specific product"""
        agora = datetime.now()
        promocao = self.promocoes_collection.find_one({
            "produto_id": produto_id,
            "data_inicio": {"$lte": agora},
            "data_fim": {"$gte": agora}
        })
        if promocao:
            promocao["id"] = str(promocao["_id"])
        return promocao

    def create_promocao(self, promocao_data):
        if promocao_data["data_inicio"] >= promocao_data["data_fim"]:
            raise ValueError("Data de início deve ser anterior à data de fim")
        
        return self.promocoes_collection.insert_one(promocao_data)

    def update_promocao(self, promocao_id, update_data):
        return self.promocoes_collection.update_one(
            {"_id": ObjectId(promocao_id)}, 
            {"$set": update_data}
        )

    def delete_promocao(self, promocao_id):
        return self.promocoes_collection.delete_one({"_id": ObjectId(promocao_id)})

    def calcular_preco_promocional(self, preco_original, promocao):
        tipo = promocao["tipo"].lower()
        
        if tipo in ["desconto_percentual", "desconto percentual"]:
            desconto = preco_original * (promocao["valor"] / 100)
            return round(preco_original - desconto, 2)
        elif tipo in ["desconto_fixo", "desconto fixo"]:
            return round(max(0, preco_original - promocao["valor"]), 2)
        else:
            return preco_original
        
    def list_avaliacoes(self, produto_id=None, usuario_id=None):
        query = {}
        if produto_id:
            if isinstance(produto_id, str) and produto_id.isdigit():
                query["produto_id"] = int(produto_id)
            else:
                query["produto_id"] = produto_id
                    
        if usuario_id:
            query["usuario_id"] = usuario_id

        avaliacoes = []
        for a in self.avaliacoes_collection.find(query).sort("data", -1):
            a["id"] = str(a["_id"])
            
            # Add product name
            produto = self.produtos_collection.find_one({"_id": a["produto_id"]})
            if produto:
                a["produto_nome"] = produto["nome"]
                    
            avaliacoes.append(a)
        
        return avaliacoes

    def get_avaliacao(self, avaliacao_id):
        avaliacao = self.avaliacoes_collection.find_one({"_id": ObjectId(avaliacao_id)})
        if avaliacao:
            avaliacao["id"] = str(avaliacao["_id"])
            
            produto = self.produtos_collection.find_one({"_id": avaliacao["produto_id"]})
            if produto:
                avaliacao["produto"] = produto
                
        return avaliacao

    def create_avaliacao(self, avaliacao_data):
        if not 0 <= avaliacao_data["nota"] <= 5:
            raise ValueError("Nota deve estar entre 0 e 5")
            
        existing = self.avaliacoes_collection.find_one({
            "usuario_id": avaliacao_data["usuario_id"],
            "produto_id": avaliacao_data["produto_id"]  # No conversion needed
        })
        
        if existing:
            raise ValueError("Usuário já avaliou este produto")
            
        if "data" not in avaliacao_data:
            avaliacao_data["data"] = datetime.now()
            
        return self.avaliacoes_collection.insert_one(avaliacao_data)

    def update_avaliacao(self, avaliacao_id, update_data):
        if "nota" in update_data and not 0 <= update_data["nota"] <= 5:
            raise ValueError("Nota deve estar entre 0 e 5")
            
        return self.avaliacoes_collection.update_one(
            {"_id": ObjectId(avaliacao_id)}, 
            {"$set": update_data}
        )

    def delete_avaliacao(self, avaliacao_id):
        return self.avaliacoes_collection.delete_one({"_id": ObjectId(avaliacao_id)})