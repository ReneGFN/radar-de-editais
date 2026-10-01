# Base de informática e operação local

## Decisões aprovadas em 2026-09-30

Renê escolheu computadores, monitores e acessórios. LangChain coordena o núcleo; Groq será o provedor da geração. Dify fica como opção futura. A implementação desta etapa cobre coleta, preparação, PostgreSQL/pgvector e busca híbrida; geração, API e painel continuam planejados.

## Estrutura implementada

```text
backend/src/radar/
  ingestion.py    consulta PNCP, baixa PDFs, extrai páginas e divide trechos
  embeddings.py   transforma texto em vetores localmente
  storage.py      cria schema e carrega um snapshot em transação
  retrieval.py    coordena as duas buscas com LangChain
  cli.py          comandos de operação
backend/tests/   controles de entrada, downloads, offsets e combinação
datasets/manifests/  fontes oficiais e hashes, sem cópias dos PDFs
reports/         evidências agregadas, sem texto bruto
ops/             inicialização e verificação local
compose.yaml     PostgreSQL isolado
requirements-lock.txt  versões instaladas
```

## Como funciona

Execução verificada: snapshot `b1ee54ef84e97078`, 10 editais, 14 PDFs, 682 páginas e 4.664 trechos/vetores. Dezesseis páginas requerem revisão por pouco texto. Carga repetida sem duplicação, filtros e offsets conferidos no banco; backup restaurado em banco separado com os mesmos 4.664 trechos. Banco saudável; medição após verificação de 93,79 MiB dentro do limite de 768 MiB. Medições pontuais não são benchmark de latência ou garantia de consumo máximo.

1. Consulta pregões eletrônicos por estado no PNCP. A base ampliada preserva dez de SP e acrescenta dois de PR, RS, MG, RJ, BA, PE, GO, MT, PA e AM. Cotas geográficas e ordem da API formam amostra de conveniência, sem representatividade. A API e fontes podem mudar; manifesto fixa URLs e hashes da captura.
2. Exige um edital PDF e limita anexos, bytes, páginas e origem de downloads. Apenas documentos de contratação tipificados são coletados. Propostas e documentos de participantes não entram. PDFs mistos podem incluir itens além de informática: o conjunto de avaliação deve escolher explicitamente os itens de informática.
3. Preserva o texto por página, sinaliza páginas com pouco texto e calcula trechos com offsets verificáveis. Cada trecho contém identificador, hash do documento, número da página e intervalo de caracteres.
4. Usa embeddings multilíngues locais de 384 dimensões. O modelo inicial é MiniLM via FastEmbed/ONNX, escolhido para começar em CPU e conter consumo de memória. Trechos têm até 120 tokens com sobreposição de 20; a janela do modelo é de 128. Arquivos do modelo têm hashes registrados. Isso evita truncamento silencioso, mas os trechos curtos podem separar tabelas ou cláusulas: qualidade será avaliada, não presumida. [Fonte do modelo](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).
5. PostgreSQL guarda snapshots, documentos, páginas e trechos. pgvector faz a busca semântica por distância cosseno; busca textual usa `tsvector` em português e `simple`. Na base pequena, busca vetorial exata evita tuning prematuro de índices aproximados. [Documentação do pgvector](https://github.com/pgvector/pgvector).
6. LangChain executa as duas buscas em paralelo; Reciprocal Rank Fusion combina posições dos resultados, sem misturar escalas de scores. Ambas aplicam filtros de snapshot e edital antes da ordenação. A saída é um `Document` com texto e metadados de citação. Não é ainda uma resposta gerada por IA.

## Docker e armazenamento

- Projeto Compose `radar-de-editais`, volume `radar-de-editais_radar_db` e rede próprios.
- Banco exposto somente em `127.0.0.1:55432`; limite de 768 MiB e 1 CPU. Imagem fixada por digest; pgvector 0.8.6 verificado no banco.
- PDFs, texto extraído, cache de modelos, vetores, credenciais e backups ficam em `%LOCALAPPDATA%\RadarDeEditais`, fora do Brain/OneDrive. Em execução pelo aplicativo Windows, `LOCALAPPDATA` pode apontar para o diretório privado do pacote do Codex; use o mesmo ambiente ou configure o caminho privado explicitamente. Não mova senhas para o projeto.
- ACL do diretório privado permite usuário atual e SYSTEM. Senhas aleatórias de 32 bytes ficam em arquivos montados como secrets. O carregador é dono apenas do schema Radar, sem superuser, criação de bancos ou papéis. Uma API futura precisará de usuário próprio somente leitura.
- Tracing externo do LangChain está desativado. Nenhuma chamada ao Groq foi feita nesta etapa.
- Ao ligar Docker Desktop, serviços existentes com política de reinício podem iniciar. O isolamento não elimina competição pela RAM; esta tarefa não auditou outros projetos.

## Reprodução em PowerShell

Requer PowerShell 7, Python 3.12, Docker Desktop e internet para downloads iniciais. Na pasta do projeto:

```powershell
py -3.12 -m venv .venv
& .venv/Scripts/python.exe -m pip install -r requirements-lock.txt
& .venv/Scripts/python.exe -m pip install --no-deps -e ./backend
& ./ops/start-db.ps1 -Initialize
& .venv/Scripts/python.exe -m radar.cli collect --start 20260928 --end 20260930 --uf SP --count 10
& .venv/Scripts/python.exe ops/expand-corpus.py datasets/manifests/b1ee54ef84e97078.json --start 20260921 --end 20261001
# Para repetir a base publicada sem selecionar novos editais:
& .venv/Scripts/python.exe -m radar.cli hydrate datasets/manifests/4f8ddffaa01b6a20.json
# Substitua pelo manifesto gerado, revisado e escolhido:
& .venv/Scripts/python.exe -m radar.cli prepare datasets/manifests/SNAPSHOT.json
& .venv/Scripts/python.exe -m radar.cli load datasets/manifests/SNAPSHOT.json
& .venv/Scripts/python.exe -m radar.cli search 'Qual é o prazo de entrega?' --snapshot SNAPSHOT --edital ID_PNCP
& .venv/Scripts/python.exe -m pytest backend/tests -q
& .venv/Scripts/python.exe ops/verify-local.py datasets/manifests/SNAPSHOT.json
```

Uma nova consulta ao PNCP pode gerar outro snapshot. A carga do mesmo snapshot é idempotente; divergência de configuração é rejeitada para não alterar um experimento já carregado. Atualizações posteriores serão novos snapshots, sem substituir documentos de uma avaliação anterior.

`hydrate` verifica cada hash, não troca o snapshot se a fonte mudou. As fontes continuam dependentes da disponibilidade oficial. `expand-corpus.py` permite `--resume` de um manifesto intermediário, revalidando setor e cotas, para retomar coleta parcial. Bases intermediárias não são a referência ativa. O intervalo adicional é 2026-09-21 a 2026-10-01, com fallback para início de setembro se um estado não alcançar dois editais.

A preparação reaproveita documentos com mesmo hash/configuração. A carga reaproveita vetores com mesma configuração e fingerprint do conteúdo; checkpoints privados permitem retomada. Nem PDFs nem caches são redistribuídos no GitHub.

Ao verificar backups, o dump contém todos os snapshots do banco e a conferência da restauração usa o snapshot solicitado. Os bancos separados de teste ficam preservados; sua existência não equivale a backup agendado.

## Limites e próximos controles

Não há autenticação de aplicação, frontend, API pública, OCR, interpretação robusta de tabelas, escolha automática da versão vigente ou resolução de retificações. Página física do PDF não necessariamente coincide com a numeração impressa. `active` da fonte é preservado e não constitui análise de vigência jurídica. A revisão visual é amostral; validação completa dos itens e respostas requer revisão humana.

Teste da base inicial registrado em [buscas](../reports/snapshots/b1ee54ef84e97078/buscas.json): `SSD` e `prazo entrega` retornaram resultados nas duas modalidades. A pergunta longa `Qual é o prazo de entrega dos computadores?` retornou apenas na busca semântica: a consulta lexical usa AND entre termos relevantes e ficou restritiva. Isso é uma limitação observada da baseline, não um resultado de precisão. Avaliar normalização/reescrita ou consulta lexical menos restritiva com perguntas de referência antes de alterar a configuração.

Backups ficam fora do Brain; a verificação cria um banco separado de restauração e compara contagens. Ainda não há agendamento ou política de retenção. Não distribuir os PDFs no GitHub até revisar licença, privacidade e condições de reutilização. A base inicial é material de laboratório; não é um serviço de acompanhamento de oportunidades vigentes.

Próximo passo: definir perguntas de referência com páginas e trechos esperados, revisar manualmente e só então integrar geração com Groq e medir recuperação, apoio, latência e custo.
