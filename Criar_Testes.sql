CREATE OR REPLACE FUNCTION TEST_vw_utilizadores_completos()
RETURNS TEXT AS $$
DECLARE
    contador INTEGER;
    resultado TEXT;
BEGIN
    SELECT COUNT(*) INTO contador
    FROM vw_utilizadores_completos;

    IF contador >= 0 THEN
        resultado := 'OK';
    ELSE
        resultado := 'NOK';
    END IF;

    RETURN resultado;
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION TEST_vw_produto_fornecedor()
RETURNS TEXT AS $$
DECLARE
    fornecedor_id INT;
    produto_id INT := 3;
    contador INTEGER;
    resultado TEXT;
BEGIN
    SELECT id_fornecedor INTO fornecedor_id FROM fornecedor LIMIT 1;
    
    IF fornecedor_id IS NULL THEN
        INSERT INTO usuario (nome, email, password, tipo_usuario)
        VALUES ('Test View Supplier', 'view.supplier@email.com', 'password', 'fornecedor')
        RETURNING id_usuario INTO fornecedor_id;
        
        INSERT INTO fornecedor (id_fornecedor, nif)
        VALUES (fornecedor_id, '555666777');
    END IF;

    INSERT INTO stock (id_produto, id_fornecedor, quantidade)
    VALUES (produto_id, fornecedor_id, 25);

    SELECT COUNT(*) INTO contador
    FROM vw_produto_fornecedor
    WHERE id_produto = produto_id;

    IF contador > 0 THEN
        resultado := 'OK';
    ELSE
        resultado := 'NOK';
    END IF;

    RETURN resultado;
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION TEST_pedidos_por_fornecedor()
RETURNS TEXT AS $$
DECLARE
    cliente_id INT;
    fornecedor_id INT;
    pedido_id INT;
    produto_id INT := 4;
    contador INTEGER;
    resultado TEXT;
BEGIN
    INSERT INTO usuario (nome, email, password, tipo_usuario)
    VALUES ('Test Function Client', 'func.client@email.com', 'password', 'cliente')
    RETURNING id_usuario INTO cliente_id;
    
    INSERT INTO cliente (id_cliente, genero, data_nascimento, morada)
    VALUES (cliente_id, 'Masculino', '1988-03-10', 'Function Test Address');

    INSERT INTO usuario (nome, email, password, tipo_usuario)
    VALUES ('Test Function Supplier', 'func.supplier@email.com', 'password', 'fornecedor')
    RETURNING id_usuario INTO fornecedor_id;
    
    INSERT INTO fornecedor (id_fornecedor, nif)
    VALUES (fornecedor_id, '888999000');

    INSERT INTO stock (id_produto, id_fornecedor, quantidade)
    VALUES (produto_id, fornecedor_id, 75);

    INSERT INTO pedido (id_cliente, status)
    VALUES (cliente_id, 'Pendente')
    RETURNING id_pedido INTO pedido_id;

    INSERT INTO tem2 (id_pedido, id_produto, quantidade)
    VALUES (pedido_id, produto_id, 3);

    SELECT COUNT(*) INTO contador
    FROM pedidos_por_fornecedor(fornecedor_id)
    WHERE id_pedido = pedido_id;

    IF contador > 0 THEN
        resultado := 'OK';
    ELSE
        resultado := 'NOK';
    END IF;

    RETURN resultado;
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION TEST_pedidos_todos_fornecedores()
RETURNS TEXT AS $$
DECLARE
    contador INTEGER;
    resultado TEXT;
BEGIN
    SELECT COUNT(*) INTO contador
    FROM pedidos_todos_fornecedores();

    IF contador >= 0 THEN
        resultado := 'OK';
    ELSE
        resultado := 'NOK';
    END IF;

    RETURN resultado;
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION TEST_criar_pedido()
RETURNS TEXT AS $$
DECLARE
    cliente_id INT;
    fornecedor_id INT;
    pedido_id INT;
    produtos INT[] := ARRAY[5, 6];
    quantidades INT[] := ARRAY[2, 1];
    contador INTEGER;
    resultado TEXT;
BEGIN
    INSERT INTO usuario (nome, email, password, tipo_usuario)
    VALUES ('Test Pedido Client', 'pedido.client@email.com', 'password', 'cliente')
    RETURNING id_usuario INTO cliente_id;
    
    INSERT INTO cliente (id_cliente, genero, data_nascimento, morada)
    VALUES (cliente_id, 'Feminino', '1992-07-22', 'Pedido Test Address');

    INSERT INTO usuario (nome, email, password, tipo_usuario)
    VALUES ('Test Pedido Supplier', 'pedido.supplier@email.com', 'password', 'fornecedor')
    RETURNING id_usuario INTO fornecedor_id;
    
    INSERT INTO fornecedor (id_fornecedor, nif)
    VALUES (fornecedor_id, '111222333');

    INSERT INTO stock (id_produto, id_fornecedor, quantidade)
    VALUES (5, fornecedor_id, 10), (6, fornecedor_id, 5);

    SELECT criar_pedido(cliente_id, produtos, quantidades) INTO pedido_id;

    SELECT COUNT(*) INTO contador
    FROM pedido
    WHERE id_pedido = pedido_id AND id_cliente = cliente_id;

    IF contador > 0 THEN
        resultado := 'OK';
    ELSE
        resultado := 'NOK';
    END IF;

    RETURN resultado;
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION TEST_processar_pedido()
RETURNS TEXT AS $$
DECLARE
    cliente_id INT;
    fornecedor_id INT;
    pedido_id INT;
    produto_id INT := 7;
    stock_inicial INT := 20;
    quantidade_pedida INT := 5;
    stock_final INT;
    resultado TEXT;
BEGIN
    INSERT INTO usuario (nome, email, password, tipo_usuario)
    VALUES ('Test Process Client', 'process.client@email.com', 'password', 'cliente')
    RETURNING id_usuario INTO cliente_id;
    
    INSERT INTO cliente (id_cliente, genero, data_nascimento, morada)
    VALUES (cliente_id, 'Masculino', '1987-11-15', 'Process Test Address');

    INSERT INTO usuario (nome, email, password, tipo_usuario)
    VALUES ('Test Process Supplier', 'process.supplier@email.com', 'password', 'fornecedor')
    RETURNING id_usuario INTO fornecedor_id;
    
    INSERT INTO fornecedor (id_fornecedor, nif)
    VALUES (fornecedor_id, '444555666');

    INSERT INTO stock (id_produto, id_fornecedor, quantidade)
    VALUES (produto_id, fornecedor_id, stock_inicial);

    INSERT INTO pedido (id_cliente, status)
    VALUES (cliente_id, 'Pendente')
    RETURNING id_pedido INTO pedido_id;

    INSERT INTO tem2 (id_pedido, id_produto, quantidade)
    VALUES (pedido_id, produto_id, quantidade_pedida);

    CALL processar_pedido(pedido_id);

    SELECT quantidade INTO stock_final
    FROM stock
    WHERE id_produto = produto_id AND id_fornecedor = fornecedor_id;

    IF stock_final = (stock_inicial - quantidade_pedida) THEN
        IF (SELECT status FROM pedido WHERE id_pedido = pedido_id) = 'Concluido' THEN
            resultado := 'OK';
        ELSE
            resultado := 'NOK';
        END IF;
    ELSE
        resultado := 'NOK';
    END IF;

    RETURN resultado;
END $$ LANGUAGE plpgsql;