# Instalação e execução local

## Painel sem serviços

Requisitos: Git e Node.js >=22.22.2. A verificação da entrega usou 24.22.1.

```powershell
git clone https://github.com/ReneGFN/radar-de-editais.git
cd radar-de-editais/frontend
npm ci
npm run dev
```

Abra http://127.0.0.1:5173. O painel e atlas usam os metadados incluídos; o chat depende das etapas seguintes. `npm run build` gera uma versão estática de consulta ao painel, com geração desabilitada. `npm run preview` não substitui o servidor de desenvolvimento para testar o chatbot.

## Chatbot completo (Windows / PowerShell 7)

Requisitos adicionais: Python 3.12, Docker Desktop com engine Linux, internet para baixar documentos/modelo e conta Groq própria com acesso ao GPT-OSS 120B. Reproduzir o corpus pode demorar; não há tempo estimado medido. Rode os comandos a partir da raiz do clone.

```powershell
py -3.12 -m venv .venv
& .venv/Scripts/python.exe -m pip install -r requirements-lock.txt
& .venv/Scripts/python.exe -m pip install --no-deps -e ./backend
$env:RADAR_PRIVATE_ROOT = Join-Path $env:LOCALAPPDATA 'RadarDeEditais'
& ./ops/start-db.ps1 -Initialize
& .venv/Scripts/python.exe -m radar.cli hydrate datasets/manifests/1446c44aca18011a.json
& .venv/Scripts/python.exe -m radar.cli prepare datasets/manifests/1446c44aca18011a.json
& .venv/Scripts/python.exe -m radar.cli load datasets/manifests/1446c44aca18011a.json
```

O diretório privado deve ficar fora do projeto, do OneDrive e de um eventual Brain. O script cria senhas aleatórias privadas e inicia somente o Compose `radar-de-editais`, com banco em `127.0.0.1:55432`; não remove volumes existentes. Conflito nessa porta deve ser resolvido antes de continuar, sem apagar outro projeto. Se já houver um volume Radar inicializado, use suas credenciais originais; gerar senhas novas não altera as do volume.

`hydrate` confere SHA-256 e rejeita PDFs alterados. Não substitua o hash para contornar falhas: isso seria outro corpus. `prepare/load` geram artefatos locais e atualizam relatórios de execução; os relatórios publicados descrevem os experimentos históricos, não essa nova execução. Não executar coleta nova para tentar reproduzir um snapshot antigo.

### Configurar sua chave sem escrevê-la no repositório

Crie/abra o arquivo privado abaixo em um editor e salve somente sua chave pessoal. Nunca copie a chave para o chat, README ou frontend.

```powershell
$radarKeyFile = Join-Path $env:RADAR_PRIVATE_ROOT 'secrets/groq_api_key'
if (-not (Test-Path -LiteralPath $radarKeyFile)) { New-Item -ItemType File -Path $radarKeyFile | Out-Null }
notepad $radarKeyFile
```

Alternativa: variável de ambiente `GROQ_API_KEY`, somente no processo backend. As credenciais devem ser da pessoa que está executando o clone. O repositório não fornece acesso à conta do autor.

### Manter dois terminais abertos

Terminal A, na raiz, com o mesmo `RADAR_PRIVATE_ROOT` configurado:

```powershell
& .venv/Scripts/python.exe ops/serve-chat.py --free-plan-confirmed
```

Use essa confirmação apenas se sua conta estiver no plano gratuito. O acesso/modelo/limites dependem da Groq e da sua conta; não presumir custo zero permanente. O serviço atual é destinado ao uso local nesse plano. Não habilita diagnóstico privado de respostas por padrão.

Terminal B:

```powershell
cd frontend
npm ci
npm run dev
```

Abra http://127.0.0.1:5173/#/chat. Se preferir a mesa: http://127.0.0.1:5173/#/explorar. Todos os serviços ficam em loopback e encerram com Ctrl+C no respectivo terminal. Não use `0.0.0.0`, túnel público ou proxy externo: a API não possui autenticação multiusuário.

## Diagnóstico

- Frontend: http://127.0.0.1:5173.
- Backend: http://127.0.0.1:8766/chat/health.
- Proxy: http://127.0.0.1:5173/chat/health.
- Health confirma processo/configuração, não disponibilidade de banco, chave ou provedor.
- Health funciona, mas perguntas falham: verificar Docker, snapshot carregado, acesso HTTPS à Groq e chave pessoal. Um processo sem permissão de saída pode responder ao health e falhar na geração.
- Porta em uso: reutilize/encerre somente o processo Radar identificado; não interrompa outro projeto.
- 429: respeitar intervalo mínimo de 35 segundos entre gerações e limites da conta.
- “Evidência insuficiente” é resultado de busca/validação, não necessariamente serviço desligado. Conferir escopo e especificidade; não desativar guardrails para obter resposta.
- O modo padrão do Vite usa relatórios estáticos para o painel e proxy `/chat` para respostas. `dev:api` é opcional para desenvolvimento da API de métricas em 8765; não é necessário para usar o chatbot.

## Testes sem Groq

```powershell
& .venv/Scripts/python.exe -m pytest backend/tests -q
cd frontend
npm test
npm run build
npm audit --omit=dev
```

Se o ambiente do agente restringir diretórios temporários, use `--basetemp` com uma pasta nova e vazia fora do OneDrive, sob o diretório temporário do usuário. Pytest gerencia essa pasta; nunca aponte para uma pasta com arquivos pessoais.

Não há suporte declarado a Linux/macOS para o script de inicialização Windows. O código Python/interface pode ser adaptado, mas isso não foi verificado nesta entrega.
