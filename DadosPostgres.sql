DELETE FROM TEM2;
DELETE FROM STOCK;
DELETE FROM PEDIDO;
DELETE FROM CLIENTE;
DELETE FROM FORNECEDOR;
DELETE FROM USUARIO;

ALTER SEQUENCE usuario_id_usuario_seq RESTART WITH 1;
ALTER SEQUENCE pedido_id_pedido_seq RESTART WITH 1;
ALTER SEQUENCE stock_id_stock_seq RESTART WITH 1;

SELECT create_usuario('João Silva', 'joao.silva@email.com', 'pass123', 'cliente', 'M', '1990-05-15', 'Rua das Flores, 123, Lisboa', NULL);
SELECT create_usuario('Maria Santos', 'maria.santos@email.com', 'pass456', 'cliente', 'F', '1985-08-22', 'Av. da Liberdade, 456, Porto', NULL);
SELECT create_usuario('Carlos Mendes', 'carlos.mendes@email.com', 'pass789', 'cliente', 'M', '1992-12-10', 'Rua Central, 789, Coimbra', NULL);
SELECT create_usuario('Ana Costa', 'ana.costa@email.com', 'pass321', 'cliente', 'F', '1988-03-18', 'Praça da República, 12, Braga', NULL);
SELECT create_usuario('Pedro Oliveira', 'pedro.oliveira@email.com', 'pass654', 'cliente', 'M', '1995-07-25', 'Rua Nova, 34, Aveiro', NULL);

SELECT create_usuario('TechSupply Lda', 'vendas@techsupply.pt', 'supplier123', 'fornecedor', NULL, NULL, NULL, '123456789');
SELECT create_usuario('ElectroDistrib SA', 'comercial@electrodistrib.pt', 'supplier456', 'fornecedor', NULL, NULL, NULL, '987654321');
SELECT create_usuario('GadgetWorld', 'info@gadgetworld.pt', 'supplier789', 'fornecedor', NULL, NULL, NULL, '456789123');
SELECT create_usuario('ComponentesPro', 'vendas@componentespro.pt', 'supplier321', 'fornecedor', NULL, NULL, NULL, '789123456');

INSERT INTO usuario (nome, email, password, tipo_usuario) 
VALUES ('Admin', 'admin@techmart.com', 'admin123', 'admin');

INSERT INTO STOCK (id_fornecedor, id_produto, quantidade) VALUES
(6, 1, 50),
(6, 2, 30),
(6, 3, 45),
(6, 4, 25),
(6, 5, 15);

INSERT INTO STOCK (id_fornecedor, id_produto, quantidade) VALUES
(7, 6, 20),
(7, 7, 35),
(7, 8, 40),
(7, 9, 12), 
(7, 10, 25);

INSERT INTO STOCK (id_fornecedor, id_produto, quantidade) VALUES
(8, 11, 18),
(8, 12, 22),
(8, 13, 30),
(8, 14, 15),
(8, 15, 28);

INSERT INTO STOCK (id_fornecedor, id_produto, quantidade) VALUES
(9, 16, 25),
(9, 17, 35),
(9, 18, 40),
(9, 19, 45),
(9, 20, 50);

SELECT criar_pedido(1, ARRAY[1, 3], ARRAY[1, 1]);
SELECT criar_pedido(2, ARRAY[6, 8, 10], ARRAY[1, 1, 2]);
SELECT criar_pedido(3, ARRAY[11, 13], ARRAY[1, 1]);
SELECT criar_pedido(4, ARRAY[16, 18, 19], ARRAY[1, 1, 1]);
SELECT criar_pedido(5, ARRAY[4, 5], ARRAY[1, 1]);

CALL processar_pedido(1);
CALL processar_pedido(3);
CALL processar_pedido(5);

CALL adicionar_produto_pedido(2, 7, 1);
CALL adicionar_produto_pedido(4, 20, 2);