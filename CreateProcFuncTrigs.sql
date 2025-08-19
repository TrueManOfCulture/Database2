CREATE OR REPLACE FUNCTION calcular_total_pedido(pedido_id INT)
RETURNS FLOAT8 AS $$
DECLARE
    total FLOAT8 := 0;
    rec RECORD;  
BEGIN

    FOR rec IN
        SELECT p.PRECO
        FROM PRODUTO p
        JOIN PEDIDO_PRODUTO pdp ON pdp.ID_PRODUTO = p.ID_PRODUTO
        WHERE pdp.ID_PEDIDO = pedido_id
    LOOP
        total := total + rec.PRECO;
    END LOOP;
    RETURN total;
END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION atualizar_estoque_pedido()
RETURNS TRIGGER AS $$
BEGIN
    -- Verifica se a quantidade de produto no estoque é suficiente
    IF NOT verificar_estoque_disponivel(NEW.ID_PRODUTO, NEW.QUANTIDADE) THEN
        RAISE EXCEPTION 'Estoque insuficiente para o produto %', NEW.ID_PRODUTO;
    END IF;
    
    -- Atualiza o estoque removendo a quantidade do produto vendido
    UPDATE STOCK
    SET QUANTIDADE = QUANTIDADE - NEW.QUANTIDADE
    WHERE ID_PRODUTO = NEW.ID_PRODUTO;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_atualizar_estoque_pedido
AFTER INSERT ON PEDIDO_PRODUTO
FOR EACH ROW
EXECUTE FUNCTION atualizar_estoque_pedido();

CREATE OR REPLACE FUNCTION verificar_exclusao_produto()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM PEDIDO_DETALHE pd WHERE pd.ID_PRODUTO = OLD.ID_PRODUTO) THEN
        RAISE EXCEPTION 'Não é possível excluir o produto % porque ele está em um pedido.', OLD.ID_PRODUTO;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION verificar_exclusao_produto()
RETURNS TRIGGER AS $$
BEGIN
    -- Verifica se o produto está relacionado com algum pedido
    IF EXISTS (SELECT 1 FROM PEDIDO_PRODUTO pp WHERE pp.ID_PRODUTO = OLD.ID_PRODUTO) THEN
        RAISE EXCEPTION 'Não é possível excluir o produto % porque ele está em um pedido.', OLD.ID_PRODUTO;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_verificar_exclusao_produto
BEFORE DELETE ON PRODUTO
FOR EACH ROW
EXECUTE FUNCTION verificar_exclusao_produto();


CREATE OR REPLACE PROCEDURE adicionar_produto_estoque(
    p_nome VARCHAR(1024),
    p_descricao VARCHAR(1024),
    p_preco FLOAT8,
    p_categoria VARCHAR(1024),
    p_marca VARCHAR(1024),
    p_condicao VARCHAR(1024),
    p_detalhes_condicao VARCHAR(1024),
    p_quantidade INT4,
    p_id_usuario INT4
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_produto INT;
BEGIN
    -- Inserir o novo produto na tabela PRODUTO
    INSERT INTO PRODUTO (NOME, DESCRICAO, PRECO, CATEGORIA, MARCA, CONDICAO, DETALHES_CONDICAO)
    VALUES (p_nome, p_descricao, p_preco, p_categoria, p_marca, p_condicao, p_detalhes_condicao)
    RETURNING ID_PRODUTO INTO v_id_produto; -- Retorna o ID do produto recém-criado

    -- Inserir o novo estoque para o produto
    INSERT INTO STOCK (ID_PRODUTO, QUANTIDADE, ULTIMO_UPDATE_DATA, ID_USUARIO)
    VALUES (v_id_produto, p_quantidade, CURRENT_DATE, p_id_usuario);

    -- Exibe uma mensagem de sucesso (opcional)
    RAISE NOTICE 'Produto com ID % foi criado e adicionado ao estoque.', v_id_produto;
END;
$$;

CREATE OR REPLACE PROCEDURE adicionar_produto_estoque(
    p_nome VARCHAR(1024),
    p_descricao VARCHAR(1024),
    p_preco FLOAT8,
    p_categoria VARCHAR(1024),
    p_marca VARCHAR(1024),
    p_condicao VARCHAR(1024),
    p_detalhes_condicao VARCHAR(1024),
    p_quantidade INT4,
    p_id_usuario INT4
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_produto INT;
BEGIN
    -- Inserir o novo produto na tabela PRODUTO
    INSERT INTO PRODUTO (NOME, DESCRICAO, PRECO, CATEGORIA, MARCA, CONDICAO, DETALHES_CONDICAO)
    VALUES (p_nome, p_descricao, p_preco, p_categoria, p_marca, p_condicao, p_detalhes_condicao)
    RETURNING ID_PRODUTO INTO v_id_produto; -- Retorna o ID do produto recém-criado

    -- Inserir o novo estoque para o produto
    INSERT INTO STOCK (ID_PRODUTO, QUANTIDADE, ULTIMO_UPDATE_DATA, ID_USUARIO)
    VALUES (v_id_produto, p_quantidade, CURRENT_DATE, p_id_usuario);

    -- Exibe uma mensagem de sucesso (opcional)
    RAISE NOTICE 'Produto com ID % foi criado e adicionado ao estoque.', v_id_produto;
END;
$$;
