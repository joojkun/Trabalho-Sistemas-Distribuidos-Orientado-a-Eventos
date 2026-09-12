# Trabalho de Microsserviços de E-commerce

Backend de um sistema de e-commerce desenvolvido em Python para demonstrar
microsserviços, arquitetura orientada a eventos, RabbitMQ e assinatura digital
com RSA.

Os processos são independentes. Um processo não chama diretamente uma função
de outro processo: a comunicação acontece por eventos publicados no RabbitMQ.

> Os exemplos deste documento usam Windows e o comando `python`. No Windows
> também é possível usar `py` no lugar de `python`.

---

## 1. Visão geral do projeto

### O que o sistema faz

O sistema permite:

- visualizar um catálogo de produtos;
- criar pedidos com um ou mais produtos;
- reservar produtos no estoque;
- simular aprovação ou recusa de pagamentos;
- emitir uma nota fiscal simples e enviar o pedido;
- cancelar automaticamente pedidos quando o estoque não está disponível ou o
  pagamento é recusado;
- excluir pedidos pelo terminal;
- consultar os pedidos e seus status;
- publicar promoções por categoria;
- entregar promoções para dois consumidores diferentes.

O fluxo principal é distribuído entre cinco microsserviços:

1. O **Principal** cria um pedido e publica `pedido.criado`.
2. O **Estoque** verifica as quantidades disponíveis.
3. Se houver estoque, o Estoque reserva os produtos e publica
   `pedido.estoque_ok`.
4. O **Pagamento** recebe esse evento e sorteia aprovação ou recusa.
5. Se aprovado, publica `pagamento.aprovado`.
6. A **Entrega** emite uma nota fiscal simples e publica `pedido.enviado`.
7. Se faltar estoque ou o pagamento for recusado, o Principal publica
   `pedido.excluido`. O Estoque devolve os produtos que estavam reservados.

### Fluxo textual dos eventos

```text
Principal
    |
    | pedido.criado
    v
Estoque
    |-------------------------------> estoque.indisponivel
    |                                      |
    |                                      v
    |                               Principal publica
    |                               pedido.excluido
    |
    | pedido.estoque_ok
    v
Pagamento
    |-------------------------------> pagamento.recusado
    |                                      |
    |                                      v
    |                               Principal publica
    |                               pedido.excluido
    |
    | pagamento.aprovado
    v
Entrega
    |
    | pedido.enviado
    v
Principal atualiza o status para "enviado"
```

### Exchanges utilizados

| Exchange | Tipo | Uso |
| --- | --- | --- |
| `eCommerce` | `direct` | Pedidos, estoque, pagamentos e entregas |
| `Promoções` | `topic` | Eventos de promoção por categoria |

Não é utilizado exchange do tipo `fanout`.

### Processos implementados

- **Microsserviço Principal**: interface de terminal e acompanhamento de pedidos.
- **Microsserviço Estoque**: reserva e devolução de produtos.
- **Microsserviço Pagamento**: aprovação ou recusa aleatória.
- **Microsserviço Entrega**: emissão de nota e envio.
- **Microsserviço Promoções**: publicação periódica de promoções.
- **Consumidor C1**: recebe promoções das categorias A e B.
- **Consumidor C2**: recebe promoções de todas as categorias.

---

## 2. Pré-requisitos e instalação

### Python

O projeto foi desenvolvido e testado com **Python 3.11**. A implementação usa
recursos comuns do Python 3.9 ou superior.

Confira a versão instalada:

```powershell
python --version
```

ou:

```powershell
py --version
```

### RabbitMQ com Docker

A maneira mais simples de iniciar o RabbitMQ é usando Docker:

```powershell
docker run -d --name rabbitmq `
  -p 5672:5672 `
  -p 15672:15672 `
  rabbitmq:management
```

Em uma única linha, o mesmo comando é:

```powershell
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
```

O projeto também possui o arquivo [docker-compose.yml](docker-compose.yml):

```powershell
docker compose up -d
```

Para verificar se o container está executando:

```powershell
docker ps
```

Para parar o container:

```powershell
docker stop rabbitmq
```

Para removê-lo:

```powershell
docker rm rabbitmq
```

### Painel de gerenciamento

Depois que o RabbitMQ estiver executando, abra:

```text
http://localhost:15672
```

O usuário e a senha padrão usados neste trabalho são:

```text
Usuário: guest
Senha: guest
```

A porta `5672` é usada pelos programas Python. A porta `15672` é usada pelo
painel web de gerenciamento.

### Dependências Python

As dependências estão em [requirements.txt](requirements.txt):

- `pika`: cliente Python para RabbitMQ;
- `cryptography`: geração de chaves RSA e assinatura digital.

Instale-as com:

```powershell
python -m pip install -r requirements.txt
```

### Geração das chaves RSA

Antes da primeira execução, gere os pares de chaves:

```powershell
python gerar_chaves.py
```

O comando cria uma chave privada e uma chave pública para cada serviço:

```text
chaves/
├── principal/
├── estoque/
├── pagamento/
├── entrega/
└── promocoes/
```

Cada pasta contém:

```text
private_key.pem
public_key.pem
```

A chave privada é usada pelo próprio produtor para assinar eventos. Os demais
processos procuram a chave pública correspondente dentro da pasta do produtor
para verificar a mensagem.

Se as duas chaves já existirem, o script não as substitui.

---

## 3. Estrutura de pastas e arquivos

```text
Trab_1_SD/
├── chaves/
│   ├── principal/
│   ├── estoque/
│   ├── pagamento/
│   ├── entrega/
│   └── promocoes/
├── comum/
│   ├── __init__.py
│   ├── config.py
│   ├── mensagens.py
│   └── seguranca.py
├── catalogo.py
├── principal.py
├── estoque.py
├── pagamento.py
├── entrega.py
├── promocoes.py
├── consumidor_c1.py
├── consumidor_c2.py
├── gerar_chaves.py
├── simulacao.py
├── requirements.txt
├── docker-compose.yml
└── README.md
```

### Arquivos dos microsserviços

| Arquivo | Responsabilidade |
| --- | --- |
| [principal.py](principal.py) | Menu do usuário, pedidos e status |
| [estoque.py](estoque.py) | Controle de quantidades e reservas |
| [pagamento.py](pagamento.py) | Simulação de aprovação ou recusa |
| [entrega.py](entrega.py) | Nota fiscal e envio |
| [promocoes.py](promocoes.py) | Publicação de promoções |
| [consumidor_c1.py](consumidor_c1.py) | Promoções A e B |
| [consumidor_c2.py](consumidor_c2.py) | Promoções A, B e C |

### Arquivos compartilhados

- [catalogo.py](catalogo.py): catálogo fixo com quatro produtos, preços e
  categorias.
- [comum/config.py](comum/config.py): nomes dos exchanges, localização das
  chaves e URL do RabbitMQ.
- [comum/mensagens.py](comum/mensagens.py): conexão, declaração de exchanges,
  publicação e consumo de mensagens.
- [comum/seguranca.py](comum/seguranca.py): geração de chaves, criação de
  envelopes e validação das assinaturas.
- [gerar_chaves.py](gerar_chaves.py): criação inicial dos pares RSA.
- [simulacao.py](simulacao.py): teste local dos fluxos sem conectar ao
  RabbitMQ.

As filas são criadas pelo próprio código quando cada consumidor é iniciado.
Não existe uma pasta separada para cada serviço porque cada microsserviço é um
script independente na raiz do trabalho.

---

## 4. Como executar o sistema

### Preparação

Na pasta do projeto, instale as dependências, inicie o RabbitMQ e gere as
chaves:

```powershell
python -m pip install -r requirements.txt
docker compose up -d
python gerar_chaves.py
```

Por padrão, os programas usam:

```text
amqp://guest:guest@localhost:5672/%2F
```

Para usar outro endereço de RabbitMQ, defina a variável `RABBITMQ_URL` antes
de iniciar cada processo:

```powershell
$env:RABBITMQ_URL = "amqp://usuario:senha@servidor:5672/%2F"
```

### Ordem recomendada

Abra um terminal para cada processo. Primeiro inicie os consumidores e depois
o Principal:

```powershell
python estoque.py
```

```powershell
python pagamento.py
```

```powershell
python entrega.py
```

```powershell
python consumidor_c1.py
```

```powershell
python consumidor_c2.py
```

```powershell
python promocoes.py
```

```powershell
python principal.py
```

Essa ordem não é obrigatória para o RabbitMQ, pois as filas e os bindings são
declarados pelos processos. Ela apenas facilita acompanhar o fluxo no
terminal.

### Menu do Principal

Ao executar [principal.py](principal.py), o menu apresenta:

```text
1 - Visualizar produtos
2 - Realizar pedido
3 - Excluir pedido
4 - Consultar pedidos
0 - Sair
```

#### Visualizar produtos

Escolha `1`. O programa mostra código, nome, preço e categoria de cada produto.

#### Criar um pedido

Escolha `2`, informe o código e a quantidade de cada produto e digite `fim`
quando terminar:

```text
Codigo do produto (fim para terminar): 1
Quantidade: 2
Codigo do produto (fim para terminar): 4
Quantidade: 1
Codigo do produto (fim para terminar): fim
```

O Principal cria um identificador, calcula o valor total e publica
`pedido.criado`.

#### Excluir um pedido

Escolha `3` e informe o identificador exibido na criação do pedido. O Principal
publica `pedido.excluido`, e o Estoque devolve os itens reservados.

Pedidos com status `enviado` não são excluídos pelo menu.

#### Consultar pedidos

Escolha `4` para exibir os identificadores, produtos e status dos pedidos
conhecidos pelo processo Principal.

### Forçar resultado do pagamento

Normalmente o resultado é escolhido aleatoriamente. Para demonstrar um
pagamento aprovado ou recusado, defina `PAGAMENTO_RESULTADO` antes de iniciar o
serviço de pagamento:

```powershell
$env:PAGAMENTO_RESULTADO = "aprovado"
python pagamento.py
```

ou:

```powershell
$env:PAGAMENTO_RESULTADO = "recusado"
python pagamento.py
```

Os valores aceitos são `aprovado` e `recusado`. Se a variável não for definida,
o serviço usa uma escolha aleatória.

---

## 5. Conceitos utilizados

### Arquitetura orientada a eventos

Na arquitetura orientada a eventos, um processo publica um fato ocorrido e
outros processos interessados reagem a esse fato.

Por exemplo, o Principal não chama uma função do Estoque. Ele publica:

```text
pedido.criado
```

O Estoque está inscrito nesse evento e reage verificando a disponibilidade.
Isso reduz o acoplamento: o Principal não precisa conhecer a implementação,
porta ou estado interno do Estoque.

Neste trabalho:

- os processos são independentes;
- cada processo possui sua própria fila;
- eventos são publicados em exchanges;
- consumidores recebem apenas os eventos ligados às suas filas;
- não existem chamadas HTTP, sockets diretos ou imports de outro
  microsserviço para executar sua lógica.

### RabbitMQ, exchanges e filas

O produtor não entrega diretamente uma mensagem para um consumidor. Ele envia a
mensagem para um exchange. O exchange verifica a routing key e encaminha a
mensagem para as filas que possuem bindings compatíveis.

Uma fila armazena mensagens até que seu consumidor as processe. Como cada
consumidor tem sua própria fila, o Estoque, o Pagamento e o Principal podem
receber cópias diferentes do mesmo evento sem compartilhar uma fila.

### Exchange `direct`

O exchange `eCommerce` é do tipo `direct`. Nesse tipo, a routing key precisa
corresponder exatamente ao binding.

Exemplo:

```text
Routing key publicada: pedido.criado
Binding compatível:    pedido.criado
```

Um binding `pedido.criado` não recebe `pedido.excluido`.

### Exchange `topic`

O exchange `Promoções` é do tipo `topic`. Ele permite routing keys formadas por
palavras separadas por ponto e bindings com padrões.

As promoções usam:

```text
promocao.categoria.A
promocao.categoria.B
promocao.categoria.C
```

O C1 possui dois bindings exatos:

```text
promocao.categoria.A
promocao.categoria.B
```

O C2 possui o binding:

```text
promocao.categoria.*
```

O caractere `*` substitui exatamente uma palavra da routing key. Por isso,
`promocao.categoria.*` recebe A, B e C.

### Routing key e binding

Uma **routing key** é o nome usado pelo produtor para classificar o evento.
Neste projeto, ela também corresponde ao nome do evento.

Um **binding** é a ligação entre uma fila e um exchange. Ele informa quais
routing keys devem ser encaminhadas para aquela fila.

Exemplo:

```text
Fila: fila.pagamento
Binding: pedido.estoque_ok
```

Assim, o Pagamento recebe somente pedidos cujo estoque foi aprovado.

### Publishers e subscribers

Um publisher produz e publica eventos. Um subscriber, também chamado de
consumer, recebe eventos de uma fila e executa uma ação.

Um mesmo processo pode publicar e consumir:

- o Principal publica `pedido.criado` e `pedido.excluido`, mas também consome
  os eventos de acompanhamento;
- o Estoque consome pedidos e publica resultados do estoque;
- o Pagamento consome `pedido.estoque_ok` e publica o resultado;
- a Entrega consome pagamento aprovado e publica o envio;
- Promoções apenas publica;
- C1 e C2 apenas consomem promoções.

### Criptografia assimétrica RSA

Cada microsserviço possui um par de chaves:

- **chave privada**: fica com o produtor e não deve ser usada por outros
  serviços para assinar mensagens;
- **chave pública**: pode ser distribuída aos consumidores para verificação.

Uma assinatura digital permite verificar duas propriedades:

1. **Autenticidade**: a mensagem foi assinada pelo produtor identificado.
2. **Integridade**: o conteúdo não foi alterado depois da assinatura.

O código usa RSA com PKCS#1 v1.5 e SHA-256.

### Hash e assinatura

Antes de assinar, o código monta uma representação JSON ordenada contendo
`Event`, `Producer` e `Data`. Em seguida:

1. calcula o hash SHA-256 desse conteúdo;
2. assina o hash com a chave privada do produtor;
3. codifica a assinatura em Base64;
4. coloca o resultado no campo `Signature`.

O hash é um resumo de tamanho fixo do conteúdo. Assinar o resumo é mais
eficiente do que aplicar a operação RSA ao conteúdo inteiro e ainda permite
detectar qualquer alteração nos dados. A assinatura não inclui o próprio campo
`Signature`, pois ele ainda não existia no momento da assinatura.

### Verificação da assinatura

Quando chega uma mensagem, [comum/mensagens.py](comum/mensagens.py):

1. converte o JSON recebido para um dicionário;
2. lê o campo `Producer`;
3. procura `chaves/<produtor>/public_key.pem`;
4. reconstrói o conteúdo canônico;
5. calcula novamente o SHA-256;
6. verifica a assinatura com a chave pública;
7. chama a lógica do consumidor somente se a assinatura for válida.

Uma mensagem inválida é confirmada no RabbitMQ e descartada. Assim, ela não
fica sendo reentregue indefinidamente nem chega à lógica de negócio.

---

## 6. Descrição detalhada dos microsserviços

### Microsserviço Principal

Arquivo: [principal.py](principal.py)

**Consome do exchange `eCommerce`:**

- `pedido.estoque_ok`
- `estoque.indisponivel`
- `pagamento.aprovado`
- `pagamento.recusado`
- `pedido.enviado`

**Publica no exchange `eCommerce`:**

- `pedido.criado`
- `pedido.excluido`

O Principal mantém os pedidos em memória durante sua execução. Ao receber
eventos, atualiza o status. Quando recebe `estoque.indisponivel` ou
`pagamento.recusado`, publica `pedido.excluido`.

### Microsserviço Estoque

Arquivo: [estoque.py](estoque.py)

**Consome:**

- `pedido.criado`
- `pedido.excluido`

**Publica:**

- `pedido.estoque_ok`
- `estoque.indisponivel`

O estoque inicial fica no dicionário `quantidades`. Quando todos os itens estão
disponíveis, as quantidades são reduzidas e a reserva fica registrada. Se algum
item não puder ser atendido, o evento de indisponibilidade é publicado sem
alterar o estoque. Ao receber `pedido.excluido`, os itens reservados são
devolvidos.

### Microsserviço Pagamento

Arquivo: [pagamento.py](pagamento.py)

**Consome:**

- `pedido.estoque_ok`

**Publica:**

- `pagamento.aprovado`
- `pagamento.recusado`

O resultado é escolhido com `random.choice`. Para testes, a variável
`PAGAMENTO_RESULTADO` pode forçar o resultado.

### Microsserviço Entrega

Arquivo: [entrega.py](entrega.py)

**Consome:**

- `pagamento.aprovado`

**Publica:**

- `pedido.enviado`

Ao receber o pagamento aprovado, cria um número de nota no formato
`NF-<ID_DO_PEDIDO>`, inclui a data de envio e publica os dados do pedido.

### Microsserviço Promoções

Arquivo: [promocoes.py](promocoes.py)

**Consome:** nenhum evento.

**Publica no exchange `Promoções`:**

- `promocao.categoria.A`
- `promocao.categoria.B`
- `promocao.categoria.C`

O produto e o desconto são escolhidos aleatoriamente. Uma promoção é publicada
a cada dez segundos.

### Consumidor C1

Arquivo: [consumidor_c1.py](consumidor_c1.py)

**Consome do exchange `Promoções`:**

- `promocao.categoria.A`
- `promocao.categoria.B`

Possui a fila própria `fila.C1` e apenas imprime as promoções recebidas.

### Consumidor C2

Arquivo: [consumidor_c2.py](consumidor_c2.py)

**Consome do exchange `Promoções`:**

- `promocao.categoria.*`

Possui a fila própria `fila.C2`, recebe todas as categorias e apenas imprime as
promoções recebidas.

### Tabela geral de eventos

| Evento (routing key) | Publicado por | Consumido por |
| --- | --- | --- |
| `pedido.criado` | Principal | Estoque |
| `pedido.estoque_ok` | Estoque | Principal, Pagamento |
| `estoque.indisponivel` | Estoque | Principal |
| `pagamento.aprovado` | Pagamento | Principal, Entrega |
| `pagamento.recusado` | Pagamento | Principal |
| `pedido.excluido` | Principal | Estoque |
| `pedido.enviado` | Entrega | Principal |
| `promocao.categoria.A` | Promoções | C1, C2 |
| `promocao.categoria.B` | Promoções | C1, C2 |
| `promocao.categoria.C` | Promoções | C2 |

Os sete primeiros eventos usam o exchange `eCommerce`. Os três últimos usam o
exchange `Promoções`.

---

## 7. Formato do envelope de evento

Toda mensagem publicada possui um envelope JSON com quatro campos:

| Campo | Descrição |
| --- | --- |
| `Event` | Nome do evento e routing key |
| `Producer` | Nome do microsserviço que assinou e publicou |
| `Data` | Dados específicos do evento |
| `Signature` | Assinatura RSA do conteúdo de `Event`, `Producer` e `Data` |

### Exemplo de pedido criado

```json
{
  "Event": "pedido.criado",
  "Producer": "principal",
  "Data": {
    "pedido_id": "a1b2c3d4",
    "produtos": [
      {
        "produto_id": "1",
        "quantidade": 2
      }
    ],
    "valor_total": 240.0,
    "status": "criado"
  },
  "Signature": "BASE64_DA_ASSINATURA_RSA"
}
```

O produtor cria esse JSON antes de publicar no exchange `eCommerce`:

```python
publicar_evento("principal", "pedido.criado", pedido)
```

O consumidor valida o envelope antes de executar sua função de negócio:

```python
envelope = json.loads(corpo.decode())
if validar_envelope(envelope):
    funcao(envelope)
```

Na implementação real, uma mensagem cuja assinatura não confere é descartada
e não é processada.

### Exemplo de evento de promoção

```json
{
  "Event": "promocao.categoria.A",
  "Producer": "promocoes",
  "Data": {
    "produto_id": "1",
    "nome": "Teclado",
    "desconto": 20,
    "preco_original": 120.0
  },
  "Signature": "BASE64_DA_ASSINATURA_RSA"
}
```

---

## 8. Casos de teste sugeridos

### 8.1 Fluxo de sucesso

Inicie todos os processos e force o pagamento aprovado:

```powershell
$env:PAGAMENTO_RESULTADO = "aprovado"
python pagamento.py
```

No Principal:

```text
1 - Visualizar produtos
2 - Realizar pedido
```

Crie um pedido com quantidade disponível. Os terminais devem mostrar:

```text
Estoque reservado para <pedido>
Pagamento aprovado: <pedido>
Nota emitida e pedido enviado: <pedido>
```

O status final no Principal deve ser:

```text
enviado
```

### 8.2 Estoque indisponível

Crie um pedido com uma quantidade maior do que o estoque existente. Por
exemplo, o produto `3` começa com apenas três unidades:

```text
Codigo do produto: 3
Quantidade: 4
```

O Estoque publica `estoque.indisponivel`. O Principal publica
`pedido.excluido` e o pedido fica com status:

```text
cancelado_estoque
```

### 8.3 Pagamento recusado

Inicie o Pagamento forçando a recusa:

```powershell
$env:PAGAMENTO_RESULTADO = "recusado"
python pagamento.py
```

Crie um pedido com estoque disponível. O fluxo esperado é:

```text
pedido.criado
pedido.estoque_ok
pagamento.recusado
pedido.excluido
```

O status final no Principal deve ser:

```text
cancelado_pagamento
```

### 8.4 Assinatura inválida

O teste abaixo cria um envelope válido e depois altera os dados sem recalcular
a assinatura:

```powershell
python -c "from comum.seguranca import criar_envelope, validar_envelope; e=criar_envelope('principal','pedido.criado',{'pedido_id':'teste'}); print(validar_envelope(e)); e['Data']['pedido_id']='alterado'; print(validar_envelope(e))"
```

O resultado esperado é:

```text
True
False
```

Na aplicação, esse evento seria descartado pelo consumidor.

### 8.5 Simulação sem RabbitMQ

Para testar os três caminhos sem iniciar os processos ou o RabbitMQ:

```powershell
python simulacao.py --cenario todos
```

Saída esperada:

```text
sucesso -> enviado
estoque -> cancelado_estoque
pagamento -> cancelado_pagamento
```

Também é possível executar apenas um cenário:

```powershell
python simulacao.py --cenario sucesso
```

---

## 9. Possíveis problemas e soluções

### Erro de conexão com RabbitMQ

Sintomas comuns:

```text
pika.exceptions.AMQPConnectionError
ConnectionRefusedError
```

Confira se o RabbitMQ está executando:

```powershell
docker ps
```

Se o container não existir, crie-o:

```powershell
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
```

Se o container estiver parado:

```powershell
docker start rabbitmq
```

Também confira a variável `RABBITMQ_URL`:

```powershell
echo $env:RABBITMQ_URL
```

Para voltar ao endereço padrão:

```powershell
$env:RABBITMQ_URL = "amqp://guest:guest@localhost:5672/%2F"
```

### Filas ou bindings não aparecem

As filas são declaradas somente quando o respectivo processo é iniciado.
Execute cada consumidor pelo menos uma vez:

```powershell
python estoque.py
python pagamento.py
python entrega.py
python consumidor_c1.py
python consumidor_c2.py
```

Depois atualize a página `http://localhost:15672` e confira as abas
**Exchanges** e **Queues and Streams**.

### Chave pública ausente

Se aparecer uma mensagem de descarte relacionada à segurança, confira se
existe a chave pública do produtor:

```powershell
Get-ChildItem chaves -Recurse
```

Se necessário, gere as chaves novamente:

```powershell
python gerar_chaves.py
```

Não altere manualmente uma chave pública depois que eventos começarem a ser
publicados, pois os eventos assinados com a chave antiga deixarão de validar.

### Assinatura inválida

Uma assinatura inválida ocorre quando os dados foram alterados ou quando a
chave pública não corresponde à chave privada usada pelo produtor. O consumidor
imprime:

```text
[seguranca] evento descartado na fila <nome-da-fila>
```

A mensagem não é enviada para a lógica do microsserviço.

### Nenhuma promoção aparece

O serviço Promoções publica uma mensagem a cada dez segundos. Confira se ele
está executando:

```powershell
python promocoes.py
```

Depois confira se C1 e C2 estão ativos:

```powershell
python consumidor_c1.py
python consumidor_c2.py
```

### Pagamento sempre aleatório

Esse é o comportamento padrão. Para uma demonstração repetível, defina:

```powershell
$env:PAGAMENTO_RESULTADO = "aprovado"
```

ou:

```powershell
$env:PAGAMENTO_RESULTADO = "recusado"
```

### Os status sumiram depois de reiniciar o Principal

Os pedidos são mantidos em memória no dicionário `pedidos` de
[principal.py](principal.py). O projeto não implementa persistência em banco
de dados. Por isso, ao reiniciar o processo, os pedidos da execução anterior
não ficam disponíveis para consulta.

---

## 10. Créditos e identificação

Preencha os dados do grupo antes da entrega:

```text
Disciplina: ______________________________________________
Professor(a): ____________________________________________
Instituição: _____________________________________________

Integrante 1: ____________________________________________
Integrante 2: ____________________________________________
Integrante 3: ____________________________________________
Integrante 4: ____________________________________________
```

---

## Resumo dos comandos

Instalação:

```powershell
python -m pip install -r requirements.txt
docker compose up -d
python gerar_chaves.py
```

Execução dos serviços:

```powershell
python estoque.py
python pagamento.py
python entrega.py
python promocoes.py
python consumidor_c1.py
python consumidor_c2.py
python principal.py
```

Teste local:

```powershell
python simulacao.py --cenario todos
```
