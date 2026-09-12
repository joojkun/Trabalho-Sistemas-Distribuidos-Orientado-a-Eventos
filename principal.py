import threading
import uuid

from catalogo import PRODUTOS, listar_produtos
from comum.mensagens import consumir_eventos, publicar_evento


pedidos = {}
trava_pedidos = threading.Lock()


def tratar_evento(envelope):
    evento = envelope["Event"]
    dados = envelope["Data"]
    pedido_id = dados["pedido_id"]

    with trava_pedidos:
        pedido = pedidos.get(pedido_id)
        if pedido is None:
            return

        if evento == "pedido.estoque_ok":
            pedido["status"] = "aguardando_pagamento"
        elif evento == "estoque.indisponivel":
            pedido["status"] = "cancelado_estoque"
        elif evento == "pagamento.aprovado":
            pedido["status"] = "pagamento_aprovado"
        elif evento == "pagamento.recusado":
            pedido["status"] = "cancelado_pagamento"
        elif evento == "pedido.enviado":
            pedido["status"] = "enviado"

    if evento in ("estoque.indisponivel", "pagamento.recusado"):
        publicar_evento("principal", "pedido.excluido", pedido)
        print("Pedido", pedido_id, "foi excluido.")
    else:
        print("Pedido", pedido_id, "->", pedido["status"])


def iniciar_consumidor():
    bindings = [
        "pedido.estoque_ok",
        "estoque.indisponivel",
        "pagamento.aprovado",
        "pagamento.recusado",
        "pedido.enviado",
    ]
    consumidor = threading.Thread(
        target=consumir_eventos,
        args=("fila.principal", bindings, tratar_evento),
        daemon=True,
    )
    consumidor.start()


def fazer_pedido():
    listar_produtos()
    itens = []

    while True:
        codigo = input("Codigo do produto (fim para terminar): ").strip()
        if codigo.lower() == "fim":
            break
        if codigo not in PRODUTOS:
            print("Produto inexistente.")
            continue

        try:
            quantidade = int(input("Quantidade: "))
        except ValueError:
            print("Quantidade invalida.")
            continue

        if quantidade <= 0:
            print("A quantidade deve ser positiva.")
            continue
        itens.append({"produto_id": codigo, "quantidade": quantidade})

    if not itens:
        print("Nenhum item foi informado.")
        return

    pedido_id = uuid.uuid4().hex[:8]
    pedido = {
        "pedido_id": pedido_id,
        "produtos": itens,
        "valor_total": sum(
            PRODUTOS[item["produto_id"]]["preco"] * item["quantidade"]
            for item in itens
        ),
        "status": "criado",
    }
    with trava_pedidos:
        pedidos[pedido_id] = pedido

    publicar_evento("principal", "pedido.criado", pedido)
    print("Pedido criado:", pedido_id)


def excluir_pedido():
    pedido_id = input("Id do pedido: ").strip()
    with trava_pedidos:
        pedido = pedidos.get(pedido_id)
        if pedido is None:
            print("Pedido nao encontrado.")
            return
        if pedido["status"] == "enviado":
            print("Um pedido enviado nao pode ser excluido.")
            return
        pedido["status"] = "cancelamento_solicitado"

    publicar_evento("principal", "pedido.excluido", pedido)
    with trava_pedidos:
        pedido["status"] = "cancelado"
    print("Solicitacao de exclusao enviada.")


def consultar_pedidos():
    with trava_pedidos:
        if not pedidos:
            print("Nenhum pedido.")
            return
        for pedido in pedidos.values():
            print(pedido["pedido_id"], "-", pedido["status"], pedido["produtos"])


def menu():
    iniciar_consumidor()
    while True:
        print("\n1 - Visualizar produtos")
        print("2 - Realizar pedido")
        print("3 - Excluir pedido")
        print("4 - Consultar pedidos")
        print("0 - Sair")
        opcao = input("Opcao: ").strip()

        if opcao == "1":
            listar_produtos()
        elif opcao == "2":
            fazer_pedido()
        elif opcao == "3":
            excluir_pedido()
        elif opcao == "4":
            consultar_pedidos()
        elif opcao == "0":
            break
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    menu()
