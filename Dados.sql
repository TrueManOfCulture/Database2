/* =============================
   USUARIOS (um admin, um cliente, um fornecedor)
   ============================= */
INSERT INTO USUARIO (NOME, EMAIL, PASSWORD, TIPO_USUARIO) VALUES
('Alice Admin', 'alice@techmart.com', 'admin123', 'admin'),
('Carlos Cliente', 'carlos@gmail.com', 'cliente123', 'cliente'),
('Fernanda Fornecedor', 'fernanda@fornecedores.com', 'fornecedor123', 'fornecedor');


/* =============================
   CLIENTE (ligado ao Carlos)
   ============================= */
INSERT INTO CLIENTE (ID_CLIENTE, GENERO, DATA_NASCIMENTO, MORADA) VALUES
(2, 'M', '1995-06-15', 'Rua das Flores, 123');


/* =============================
   FORNECEDOR (ligado à Fernanda)
   ============================= */
INSERT INTO FORNECEDOR (ID_FORNECEDOR, NIF) VALUES
(3, '509876321');


/* =============================
   PEDIDOS (feito pelo cliente)
   ============================= */
INSERT INTO PEDIDO (ID_CLIENTE, DATA_EFETUADO, STATUS) VALUES
(2, '2025-08-10', 'Pendente'),
(2, '2025-08-12', 'Concluido');


/* =============================
   STOCK (referencia produtos no Mongo)
   Aqui vou criar stock para produtos com IDs 101 e 102
   ============================= */
INSERT INTO STOCK (ID_FORNECEDOR, ID_PRODUTO, QUANTIDADE) VALUES
(3, 101, 50),   -- Produto 101 no Mongo
(3, 102, 30);   -- Produto 102 no Mongo


/* =============================
   TEM2 (associa pedido a produtos no Mongo)
   ============================= */
-- Pedido 1 (pendente) com 2 produtos 101
INSERT INTO TEM2 (ID_PEDIDO, ID_PRODUTO, QUANTIDADE) VALUES
(1, 101, 2);

-- Pedido 2 (concluido) com 1 produto 102
INSERT INTO TEM2 (ID_PEDIDO, ID_PRODUTO, QUANTIDADE) VALUES
(2, 102, 1);
