# Busca global v2 — 2026-10-05

Entrega local após aprovação de Renê: diagnóstico e melhoria da recuperação de contratações. Chat, geração e publicação não executados nesta etapa.

## O que mudou e por quê

A versão anterior limitava cada ramo a 60 páginas globais e combinava votos por trecho antes de escolher editais. Muitas páginas parecidas de um documento podiam ocupar esse orçamento. Agora cada ramo conserva até três páginas por contratação e combina a posição da melhor página de cada contratação: cada edital recebe um voto por ramo. A busca lexical continua por palavras e a semântica por embeddings locais; nenhuma dependência foi adicionada.

Uma terceira pista usa somente o nome oficial do órgão no manifesto. Normaliza acentos, remove termos administrativos genéricos e considera palavras presentes em no máximo dois nomes do catálogo. Quando pelo menos metade dessas palavras aparece na pergunta, a contratação recebe um voto adicional por posição, pela mesma fórmula RRF (soma de 1/(60+posição)). Isso ajuda perguntas que identificam o município ou órgão sem exigir que seu nome apareça no trecho técnico. Os limiares são heurísticos e precisam de validação independente; nomes abreviados, homônimos e termos genéricos podem falhar.

Nenhum identificador de caso, resposta esperada ou PNCP esperado foi usado no código de ranking. A análise e a seleção da mudança usaram desenvolvimento, portanto o resultado continua sujeito a ajuste ao conjunto observado. Metadados não garantem que o trecho suporte uma resposta.

## Avaliação real

Mesmo snapshot `1446c44aca18011a`, mesmas 40 perguntas factuais e hashes de referência iguais. Banco consultado com transações somente leitura, sem mudança em containers, volumes, credenciais ou corpus. Sem Groq, Jev ou holdout.

| Medida | v1 | v2 |
|---|---:|---:|
| PNCP esperado entre cinco candidatos | 21/40 (52,5%) | 35/40 (87,5%) |
| Mediana de recuperação | 348,23 ms | 398,90 ms |
| Metadados retornados conferidos no banco | Sim | Sim |

Houve 16 ganhos e duas regressões (pilot-06, pilot-31). Cinco falhas: pilot-04, pilot-06, pilot-08, pilot-31 e pilot-32. As três primeiras não identificam órgão na pergunta; as duas últimas usam nome abreviado de órgão, cujo nome oficial mais longo não alcançou o limiar de cobertura. Essas são pistas diagnósticas; não comprovam que alterar apenas esse critério resolveria os casos.

A referência contém uma contratação conhecida por pergunta, sem rotular todas as alternativas válidas. Muitas perguntas foram formuladas originalmente para um edital selecionado. Logo, a ausência do PNCP conhecido não implica necessariamente que todos os candidatos estejam errados. Uma execução por versão, condições de cache não controladas: a diferença de latência é descritiva. Os números não medem correção da resposta, qualidade do trecho nem generalização para PDFs novos. A meta de 90% não foi atingida nesta medida.

Evidências preservadas: [v1](../reports/discovery-development-v1.json) e [v2](../reports/discovery-development-v2.json). Reexecutar com `.venv/Scripts/python.exe ops/evaluate-discovery.py --report v2` no ambiente privado configurado; o script substitui somente o relatório v2. Não recria v1 usando o código novo. Testes: 11 específicos e 242 totais passaram; `pip check` sem conflitos. Auditoria atual via PyPI sem vulnerabilidades conhecidas nas dependências auditáveis; o pacote local não é auditável pelo índice. Tentativa inicial de auditoria teve bloqueio de rede/cache, resolvido pela execução autorizada fora do sandbox. Nenhum segredo foi exibido.

## Dez grupos de segurança nesta entrega

1. **Segredos — verificado no escopo:** alterações de código/testes/relatórios/documentação examinadas; nenhum valor de credencial ou texto bruto nos novos relatórios. Configuração privada e `.gitignore` preservados; histórico completo não reauditado.
2. **API/frontend — não aplicável à mudança:** nenhum endpoint ou bundle modificado; descoberta ainda não exposta ao navegador.
3. **Entradas — verificado:** testes de vazio, tipo e limite de 2.000 caracteres, seleção desconhecida e isolamento do escopo; testes novos de voto por contratação e pista de órgão.
4. **Autorização — verificado no escopo local:** snapshot fixo, catálogo permitido, resultados externos rejeitados. Ausência de login de produção não foi validada nesta etapa.
5. **Ataques — verificado no código alterado:** SQL com parâmetros para pergunta, vetor, snapshot e lista; expressões SQL fixas. Nenhum comando deriva do texto dos PDFs; testes de exploração completos não executados. XSS/CSRF não aplicáveis ao módulo sem rota/interface.
6. **Logs — verificado:** avaliação exibe somente progresso/ID/acerto; relatório contém IDs públicos e métricas, sem textos ou credenciais. Auditoria/retensão de produção não examinadas.
7. **Senhas — não aplicável:** nenhum mecanismo de senha ou recuperação alterado.
8. **Backup — não aplicável à mudança:** banco somente leitura e relatórios separados; restauração não repetida nesta etapa. Não declarar backup validado por esta execução.
9. **Dependências — verificado no escopo:** nenhum manifesto/lock alterado, 242 testes, `pip check` e auditoria atuais; pacote local fora do índice analisado funcionalmente, não por base de vulnerabilidades.
10. **Comunicação — verificado no escopo:** cálculo local e PostgreSQL local; consulta HTTPS ao índice para auditoria, sem enviar PDFs. TLS/cabeçalhos de produção não aplicáveis nem validados.

## Próximo passo proposto

Aguardar revisão de Renê. Tratar nomes abreviados e perguntas ambíguas com esclarecimento ao usuário, além de avaliar relevância dos trechos. Só então conectar geração e tela em entregas próprias. Manter holdout reservado; sem promessa de 90% em base ampliada e sem integração paga de Jev.
