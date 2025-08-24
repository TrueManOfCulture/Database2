/* ========================================
   TRIGGER: Atualizar DATA_CONCLUIDO quando pedido for concluído
   ======================================== */
CREATE OR REPLACE FUNCTION set_data_concluido()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'Concluido' AND OLD.status IS DISTINCT FROM 'Concluido' THEN
        NEW.data_concluido := CURRENT_DATE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_data_concluido ON pedido;
CREATE TRIGGER trg_set_data_concluido
BEFORE UPDATE ON pedido
FOR EACH ROW
EXECUTE FUNCTION set_data_concluido();


/* ========================================
   Função: Criar Pedido
   ======================================== */
CREATE OR REPLACE FUNCTION criar_pedido(
    p_id_cliente INT,
    p_produtos INT[],
    p_quantidades INT[]
) RETURNS INT AS $$
DECLARE
    v_pedido_id INT;
    i INT;
    stock_atual INT;
BEGIN
    -- Validar cliente
    IF NOT EXISTS (SELECT 1 FROM cliente WHERE id_cliente = p_id_cliente) THEN
        RAISE EXCEPTION 'Cliente % não existe', p_id_cliente;
    END IF;

    -- Validar arrays
    IF array_length(p_produtos, 1) IS NULL OR array_length(p_quantidades, 1) IS NULL THEN
        RAISE EXCEPTION 'Listas de produtos e quantidades não podem ser vazias';
    END IF;

    IF array_length(p_produtos, 1) <> array_length(p_quantidades, 1) THEN
        RAISE EXCEPTION 'Número de produtos e quantidades não correspondem';
    END IF;

    -- Verificar stock de todos os produtos antes de criar pedido
    FOR i IN 1..array_length(p_produtos, 1) LOOP
        SELECT quantidade INTO stock_atual
        FROM stock
        WHERE id_produto = p_produtos[i];

        IF stock_atual IS NULL THEN
            RAISE EXCEPTION 'Produto % não existe em stock', p_produtos[i];
        ELSIF stock_atual < p_quantidades[i] THEN
            RAISE EXCEPTION 'Stock insuficiente para produto % (disponível %, solicitado %)',
                p_produtos[i], stock_atual, p_quantidades[i];
        END IF;
    END LOOP;

    -- Criar pedido
    INSERT INTO pedido (id_cliente, status)
    VALUES (p_id_cliente, 'Pendente')
    RETURNING id_pedido INTO v_pedido_id;

    -- Inserir os produtos associados
    FOR i IN 1..array_length(p_produtos, 1) LOOP
        INSERT INTO tem2 (id_pedido, id_produto, quantidade)
        VALUES (v_pedido_id, p_produtos[i], p_quantidades[i]);
    END LOOP;

    RETURN v_pedido_id;
END;
$$ LANGUAGE plpgsql;


/* ========================================
   TRIGGER: Validar cliente ao criar pedido
   ======================================== */
CREATE OR REPLACE FUNCTION check_cliente_exist()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM cliente WHERE id_cliente = NEW.id_cliente) THEN
        RAISE EXCEPTION 'Cliente % não existe', NEW.id_cliente;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_cliente ON pedido;
CREATE TRIGGER trg_check_cliente
BEFORE INSERT ON pedido
FOR EACH ROW
EXECUTE FUNCTION check_cliente_exist();


/* ========================================
   TRIGGER: Validar stock antes de adicionar produto ao pedido
   ======================================== */
CREATE OR REPLACE FUNCTION check_stock()
RETURNS TRIGGER AS $$
DECLARE
    quantidade_disponivel INT;
BEGIN
    SELECT quantidade INTO quantidade_disponivel
    FROM stock
    WHERE id_produto = NEW.id_produto;

    IF quantidade_disponivel IS NULL THEN
        RAISE EXCEPTION 'Produto % não tem stock registado', NEW.id_produto;
    END IF;

    IF quantidade_disponivel < NEW.quantidade THEN
        RAISE EXCEPTION 'Stock insuficiente para produto %: disponível %, solicitado %',
            NEW.id_produto, quantidade_disponivel, NEW.quantidade;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_stock ON tem2;
CREATE TRIGGER trg_check_stock
BEFORE INSERT ON tem2
FOR EACH ROW
EXECUTE FUNCTION check_stock();


/* ========================================
   PROCEDURE: Processar Pedido
   ======================================== */
CREATE OR REPLACE PROCEDURE processar_pedido(p_pedido_id INT)
LANGUAGE plpgsql
AS $$
DECLARE
    r RECORD;
    stock_atual INT;
BEGIN
    -- Verificar se pedido existe e está pendente
    IF NOT EXISTS (SELECT 1 FROM pedido WHERE id_pedido = p_pedido_id) THEN
        RAISE EXCEPTION 'Pedido % não existe', p_pedido_id;
    END IF;

    IF (SELECT status FROM pedido WHERE id_pedido = p_pedido_id) <> 'Pendente' THEN
        RAISE EXCEPTION 'Pedido % já foi processado ou não está pendente', p_pedido_id;
    END IF;

    -- Verificar stock de todos os produtos
    FOR r IN
        SELECT id_produto, quantidade FROM tem2 WHERE id_pedido = p_pedido_id
    LOOP
        SELECT quantidade INTO stock_atual
        FROM stock
        WHERE id_produto = r.id_produto;

        IF stock_atual IS NULL THEN
            RAISE EXCEPTION 'Produto % não existe em stock', r.id_produto;
        ELSIF stock_atual < r.quantidade THEN
            RAISE EXCEPTION 'Stock insuficiente para produto % (disponível %, solicitado %)',
                r.id_produto, stock_atual, r.quantidade;
        END IF;
    END LOOP;

    -- Atualizar stock
    FOR r IN
        SELECT id_produto, quantidade FROM tem2 WHERE id_pedido = p_pedido_id
    LOOP
        UPDATE stock
        SET quantidade = quantidade - r.quantidade,
            ultimo_update = CURRENT_DATE
        WHERE id_produto = r.id_produto;
    END LOOP;

    -- Atualizar status do pedido
    UPDATE pedido
    SET status = 'Concluido',
        data_concluido = CURRENT_DATE
    WHERE id_pedido = p_pedido_id;

END;
$$;


/* ========================================
   Função: Quantos pedidos fez um cliente
   ======================================== */
CREATE OR REPLACE FUNCTION pedidos_por_cliente(p_cliente_id INT)
RETURNS INT AS $$
DECLARE
    total INT;
BEGIN
    SELECT COUNT(*) INTO total
    FROM pedido
    WHERE id_cliente = p_cliente_id;
    RETURN total;
END;
$$ LANGUAGE plpgsql;

/* ========================================
   Função genérica: criar utilizador (cliente ou fornecedor)
   ======================================== */
CREATE OR REPLACE FUNCTION create_usuario(
    p_nome TEXT,
    p_email TEXT,
    p_password TEXT,
    p_tipo_usuario TEXT,
    p_genero TEXT DEFAULT NULL,
    p_data_nascimento DATE DEFAULT NULL,
    p_morada TEXT DEFAULT NULL,
    p_nif TEXT DEFAULT NULL
) RETURNS INT AS $$
DECLARE
    new_id INT;
BEGIN
    INSERT INTO usuario (nome, email, password, tipo_usuario)
    VALUES (p_nome, p_email, p_password, p_tipo_usuario)
    RETURNING id_usuario INTO new_id;

    IF p_tipo_usuario = 'cliente' THEN
        INSERT INTO cliente (id_cliente, genero, data_nascimento, morada)
        VALUES (new_id, p_genero, p_data_nascimento, p_morada);
    ELSIF p_tipo_usuario = 'fornecedor' THEN
        INSERT INTO fornecedor (id_fornecedor, nif)
        VALUES (new_id, p_nif);
    END IF;

    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE VIEW vw_cliente_pedidos AS
SELECT 
    p.id_pedido,
    p.id_cliente,
    p.status,
    p.data_efetuado,
    t.id_produto,
    t.quantidade
FROM pedido p
JOIN tem2 t ON p.id_pedido = t.id_pedido;

CREATE OR REPLACE FUNCTION pedidos_por_fornecedor(p_id_fornecedor INT)
RETURNS TABLE (
    id_pedido INT,
    id_cliente INT,
    status VARCHAR,
    data_efetuado DATE,
    id_produto INT,
    quantidade INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id_pedido,
        p.id_cliente,
        p.status,
        p.data_efetuado,
        t.id_produto,
        t.quantidade
    FROM pedido p
    JOIN tem2 t ON p.id_pedido = t.id_pedido
    JOIN stock s 
        ON t.id_produto = s.id_produto
       AND s.id_fornecedor = p_id_fornecedor
    WHERE EXISTS (
        SELECT 1
        FROM stock st
        WHERE st.id_produto = t.id_produto
          AND st.id_fornecedor = p_id_fornecedor
    );
END;
$$ LANGUAGE plpgsql;
