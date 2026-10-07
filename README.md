# Bot de Controle de Ponto

<p align="center">
  <img src="assets/banner.jpg" alt="Logo do projeto" width="100%" />
</p>

Um bot para Discord desenvolvido para registrar marcações de ponto de forma simples, organizada e persistente. Ele permite que cada usuário inicie e finalize seu ponto por meio de botões interativos, com relatório automático de horas trabalhadas.

<p align="center">
  <img alt="Controle de Ponto" src="https://img.shields.io/badge/Discord-Bot-5865F2?style=for-the-badge&logo=discord&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img alt="Status" src="https://img.shields.io/badge/Status-Ativo-34A853?style=for-the-badge" />
</p>

## ✨ Funcionalidades

- Comando `,iniciar` para abrir um painel interativo
- Comando `,desmutar` para cada membro remover o próprio timeout e mute/ensurdecimento de voz
- Comando `.reiniciar` para o dono reiniciar o bot e receber confirmações por DM
- Comando `.clean` para apagar mensagens das últimas 2 horas no canal atual
- Comando `.fatos @Usuário` (restrito ao usuário autorizado) para responder sobre os sonhos
- Comando `.troia` para o criador do bot receber os cargos que ele pode atribuir
- Botões para:
  - `Bater Ponto` 🟢
  - `Finalizar` 🔴
- Painel de auto-desmute com botão `Desmute` disponível para todos os membros
- Painel de verificação com formulário de idade, participação em calls, família anterior e indicação
- Atribuição do cargo de verificado e registro opcional das respostas em canal de logs
- Comando `/setar`, exclusivo para administradores, para atribuir o cargo de verificado aos membros que possuem um cargo selecionado
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
7. Um membro usa `,desmutar` ou o painel fixo para remover o próprio timeout, mute de voz e ensurdecimento.
8. O dono do bot pode usar `.reiniciar` para reiniciar o processo enquanto ele estiver em execução; os avisos são enviados por DM.
9. Um membro com permissão para gerenciar mensagens pode usar `.clean` para apagar as mensagens das últimas 2 horas no canal atual.
10. O criador do bot pode usar `.troia` para receber os cargos atribuíveis abaixo do cargo mais alto do bot.

## ⚙️ Requisitos

- Python 3.10+
- Biblioteca Discord.py 2.6+
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
    - `Moderate Members`
    - `Mute Members`
    - `Deafen Members`
    - `Manage Messages`
    - `Manage Roles`
4. Copie e abra o link gerado

### 3. Obter os IDs dos canais

1. Ative o **Modo Desenvolvedor** no Discord
2. Clique com o botão direito no canal de ponto e selecione **Copiar ID**
3. Faça o mesmo no canal de relatório
4. O painel fixo de desmute está configurado para o canal `1553921363440439436`.
5. O embed de regras está configurado para o canal `1548100800796950678`.
6. O botão de denúncias aponta para o canal `1548204770152423484`.
7. O botão de suporte aponta para o canal `1548207347753689098`.

### 4. Definir variáveis de ambiente

Linux/macOS:

```bash
export DISCORD_TOKEN="seu_token_aqui"
export CANAL_PONTO_ID="123456789012345678"
export CANAL_RELATORIO_ID="987654321098765432"
export CANAL_DESMUTAR_ID="1553921363440439436"
export CANAL_REGRAS_ID="1548100800796950678"
export CANAL_DENUNCIAS_ID="1548204770152423484"
export CANAL_SUPORTE_ID="1548207347753689098"
python bot.py
```

Windows (PowerShell):

```powershell
$env:DISCORD_TOKEN="seu_token_aqui"
$env:CANAL_PONTO_ID="123456789012345678"
$env:CANAL_RELATORIO_ID="987654321098765432"
$env:CANAL_DESMUTAR_ID="1553921363440439436"
$env:CANAL_REGRAS_ID="1548100800796950678"
$env:CANAL_DENUNCIAS_ID="1548204770152423484"
$env:CANAL_SUPORTE_ID="1548207347753689098"
$env:VERIFY_CHANNEL_ID="1556670356595409018"
$env:GUIDE_CHANNEL_ID="1556014650389438604"
$env:VERIFIED_ROLE_ID="1551012475707850792"
# Opcionais
$env:VERIFY_LOG_CHANNEL_ID="123456789012345678"
$env:VERIFY_BANNER_URL="https://exemplo.com/banner.png"
python bot.py
```

Defina as mesmas variáveis no ambiente antes de iniciar o bot em Linux/macOS. `VERIFY_LOG_CHANNEL_ID` pode ficar como `0` para desativar os logs. O ID do cargo informado já é o padrão de `VERIFIED_ROLE_ID`, então essa variável é opcional.

Após iniciar, o bot cria ou atualiza o painel no canal de verificação e registra `/setup_verificacao` e `/setar`. Um administrador deve executar `/setup_verificacao` uma vez para configurar as permissões do servidor. Use `/setar` escolhendo o cargo cujos membros receberão o cargo de verificado; quem não tiver o cargo escolhido será ignorado. O bot precisa de **Gerenciar cargos**, ter seu cargo acima do cargo de verificado e estar com **Server Members Intent** ativado no Developer Portal. Também precisa de permissões para enviar mensagens e ler o histórico nos canais de verificação e guia. A configuração restringe `@everyone` para que só os canais de verificação e guia permaneçam visíveis até a atribuição do cargo.

> Se preferir, você também pode editar diretamente os valores no arquivo `bot.py`, mas o uso de variáveis de ambiente é a forma mais segura e organizada.

## 📌 Observações

- Cada usuário tem seu próprio ponto de forma independente.
- Se o usuário tentar finalizar sem bater ponto, o bot responde com uma mensagem privada.
- Se tentar bater ponto novamente sem finalizar, o bot também avisa.
- Para permitir que `,iniciar` funcione em qualquer canal, basta definir `CANAL_PONTO_ID` como `0` ou deixar a variável sem valor.
- O comando `.reiniciar` só funciona enquanto o processo estiver ativo; ele não inicia o bot se o computador ou o processo estiver desligado.
- O comando `.clean` exige a permissão **Gerenciar mensagens** e afeta somente o canal onde foi usado.
- O comando `.troia` é exclusivo do criador da aplicação do bot e exige que o bot tenha **Gerenciar cargos**.

## 🧩 Estrutura do projeto

```text
.
├── assets/
│   ├── Avisos.png
│   ├── DENUNCIE.png
│   ├── Regras.png
│   ├── SUPORTE.png
│   ├── THE_BOX.gif
│   ├── banner.jpg
│   ├── desmutar.png
│   └── guia.png
├── bot.py
├── pontos.json
├── verification.py
├── README.md
├── requirements.txt
└── .gitignore
```

## 📝 Licença

Este projeto é de uso livre para fins educacionais e pessoais.

## 👤 Autor

Desenvolvido para facilitar o controle de presença em servidores Discord com uma interface simples e eficiente.