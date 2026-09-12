import binascii
import json

import pika

from .config import (
    EXCHANGE_ECOMMERCE,
    EXCHANGE_PROMOCOES,
    URL_RABBITMQ,
)
from .seguranca import criar_envelope, validar_envelope


def abrir_conexao():
    return pika.BlockingConnection(pika.URLParameters(URL_RABBITMQ))


def preparar_exchanges(canal):
    canal.exchange_declare(
        exchange=EXCHANGE_ECOMMERCE,
        exchange_type="direct",
        durable=True,
    )
    canal.exchange_declare(
        exchange=EXCHANGE_PROMOCOES,
        exchange_type="topic",
        durable=True,
    )


def publicar_evento(produtor, evento, dados, exchange=EXCHANGE_ECOMMERCE):
    conexao = abrir_conexao()
    canal = conexao.channel()
    preparar_exchanges(canal)

    envelope = criar_envelope(produtor, evento, dados)
    canal.basic_publish(
        exchange=exchange,
        routing_key=evento,
        body=json.dumps(envelope, ensure_ascii=False).encode(),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
        ),
    )
    conexao.close()


def consumir_eventos(fila, bindings, funcao, exchange=EXCHANGE_ECOMMERCE):
    conexao = abrir_conexao()
    canal = conexao.channel()
    preparar_exchanges(canal)
    canal.queue_declare(queue=fila, durable=True)

    for binding in bindings:
        canal.queue_bind(
            exchange=exchange,
            queue=fila,
            routing_key=binding,
        )

    def receber(canal_receber, metodo, propriedades, corpo):
        try:
            envelope = json.loads(corpo.decode())
            valido = validar_envelope(envelope)
        except (
            ValueError,
            KeyError,
            TypeError,
            UnicodeDecodeError,
            FileNotFoundError,
            binascii.Error,
        ):
            valido = False

        if not valido:
            print("[seguranca] evento descartado na fila", fila)
            canal_receber.basic_ack(delivery_tag=metodo.delivery_tag)
            return

        funcao(envelope)
        canal_receber.basic_ack(delivery_tag=metodo.delivery_tag)

    canal.basic_qos(prefetch_count=1)
    canal.basic_consume(queue=fila, on_message_callback=receber)
    print("Consumidor ativo:", fila)
    canal.start_consuming()
