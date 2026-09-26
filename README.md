# Bot de Controle de Ponto

<p align="center">
  <img src="banner.svg" alt="Logo do projeto" width="100%" />
</p>

Um bot para Discord desenvolvido para registrar marcações de ponto de forma simples, organizada e persistente. Ele permite que cada usuário inicie e finalize seu ponto por meio de botões interativos, com relatório automático de horas trabalhadas.

<p align="center">
  <img alt="Controle de Ponto" src="https://img.shields.io/badge/Discord-Bot-5865F2?style=for-the-badge&logo=discord&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img alt="Status" src="https://img.shields.io/badge/Status-Ativo-34A853?style=for-the-badge" />
</p>

## ✨ Funcionalidades

- Comando `,iniciar` para abrir um painel interativo
- Botões para:
  - `Bater Ponto` 🟢
  - `Finalizar` 🔴
- Registro individual por usuário
- Cálculo automático da duração do ponto
- Armazenamento em `pontos.json` para manter os dados mesmo após reiniciar o bot
- Relatório em embed no canal configurado com o total de horas por pessoa
- Validação de regras para evitar erros como:
  - bater ponto sem finalizar
  - finalizar sem ter iniciado
  - duplicidade de ponto em andamento

## 🏗️ Como funciona

O fluxo do bot é simples:

1. O usuário digita `,iniciar` no canal permitido.
2. O bot envia uma mensagem com botões interativos.
3. Ao clicar em `Bater Ponto`, o horário de início é salvo.
4. Ao clicar em `Finalizar`, o sistema calcula o tempo decorrido.
5. O registro é salvo em `pontos.json`.
6. O relatório é atualizado automaticamente no canal de relatório.

## ⚙️ Requisitos

- Python 3.10+
- Biblioteca Discord.py
- Um servidor Discord com permissões para adicionar um bot

## 🚀 Instalação

Clone o repositório e instale as dependências:

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
pip install -r requirements.txt
```

## 🔐 Configuração

### 1. Criar o bot no Discord

1. Acesse o [Discord Developer Portal](https://discord.com/developers/applications)
2. Clique em **New Application**
3. Vá em **Bot** e clique em **Add Bot**
4. Ative os intents:
   - `Message Content Intent`
   - `Server Members Intent`
5. Copie o token do bot

### 2. Convidar para o servidor

1. Acesse **OAuth2** → **URL Generator**
2. Marque o escopo `bot`
3. Selecione as permissões:
   - `Send Messages`
   - `Embed Links`
   - `Read Message History`
   - `Manage Messages`
4. Copie e abra o link gerado

### 3. Obter os IDs dos canais

1. Ative o **Modo Desenvolvedor** no Discord
2. Clique com o botão direito no canal de ponto e selecione **Copiar ID**
3. Faça o mesmo no canal de relatório

### 4. Definir variáveis de ambiente

Linux/macOS:

```bash
export DISCORD_TOKEN="seu_token_aqui"
export CANAL_PONTO_ID="123456789012345678"
export CANAL_RELATORIO_ID="987654321098765432"
python bot.py
```

Windows (PowerShell):

```powershell
$env:DISCORD_TOKEN="seu_token_aqui"
$env:CANAL_PONTO_ID="123456789012345678"
$env:CANAL_RELATORIO_ID="987654321098765432"
python bot.py
```

> Se preferir, você também pode editar diretamente os valores no arquivo `bot.py`, mas o uso de variáveis de ambiente é a forma mais segura e organizada.

## 📌 Observações

- Cada usuário tem seu próprio ponto de forma independente.
- Se o usuário tentar finalizar sem bater ponto, o bot responde com uma mensagem privada.
- Se tentar bater ponto novamente sem finalizar, o bot também avisa.
- Para permitir que `,iniciar` funcione em qualquer canal, basta definir `CANAL_PONTO_ID` como `0` ou deixar a variável sem valor.

## 🧩 Estrutura do projeto

```text
.
├── bot.py
├── pontos.json
├── README.md
├── requirements.txt
└── .gitignore
```

## 📝 Licença

Este projeto é de uso livre para fins educacionais e pessoais.

## 👤 Autor

Desenvolvido para facilitar o controle de presença em servidores Discord com uma interface simples e eficiente.
