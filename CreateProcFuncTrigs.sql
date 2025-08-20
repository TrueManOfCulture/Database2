/* ========================================
   TRIGGER 1: Atualizar DATA_CONCLUIDO quando pedido for concluído
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
   TRIGGER 2: Impedir criação de pedido se cliente não existir
   (já é garantido pelo FK, mas deixamos para mensagens customizadas)
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
   TRIGGER 3: Verificar stock antes de adicionar produto ao pedido (TEM2)
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
   PROCEDURE: Processar pedido
   - Atualiza stock
   - Marca pedido como concluído
   ======================================== */
CREATE OR REPLACE PROCEDURE processar_pedido(p_pedido_id INT)
LANGUAGE plpgsql
AS $$
DECLARE
    r RECORD;
BEGIN
    -- reduzir stock conforme os produtos associados
    FOR r IN
        SELECT id_produto, quantidade FROM tem2 WHERE id_pedido = p_pedido_id
    LOOP
        UPDATE stock
        SET quantidade = quantidade - r.quantidade,
            ultimo_update = CURRENT_DATE
        WHERE id_produto = r.id_produto;

        IF NOT FOUND THEN
            RAISE NOTICE 'Produto % não existe em stock', r.id_produto;
        END IF;
    END LOOP;

    -- atualizar status do pedido
    UPDATE pedido
    SET status = 'Concluido',
        data_concluido = CURRENT_DATE
    WHERE id_pedido = p_pedido_id;
END;
$$;


/* ========================================
   FUNCTION: Quantos pedidos fez um cliente
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

