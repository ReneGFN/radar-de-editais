"""Apresenta afirmações e fontes verificáveis sem pedir metadados ao modelo."""
import re
from urllib.parse import urlsplit,urlunsplit


def plain(value):
    return re.sub(r"([\\`*_{}\[\]()<>!|#])",r"\\\1",str(value)).replace('\n',' ')


def source_url(url,page):
    parsed=urlsplit(url)
    if (parsed.scheme!='https' or parsed.hostname not in ('pncp.gov.br','www.pncp.gov.br')
        or parsed.username or parsed.password or parsed.port not in (None,443)):
        raise ValueError('Link de fonte oficial inválido')
    if not isinstance(page,int) or isinstance(page,bool) or page<1:
        raise ValueError('Página inválida')
    return urlunsplit((parsed.scheme,parsed.netloc,parsed.path,parsed.query,'page='+str(page)))


def render_markdown(result):
    if result['status']!='answered':
        # reason pode conter explicações factuais sem evidência; não apresentá-las como resposta.
        message=('Não encontrei evidência suficiente para uma resposta citada no escopo consultado.'
                 if result['status']=='insufficient_evidence' else
                 'Não posso atender a este pedido com uma resposta factual sustentada pelas fontes.')
        return message+'\n\nVocê pode reformular a pergunta ou indicar o edital e o item que deseja conferir.\n'
    if result.get('citation_integrity')!='passed':
        raise ValueError('Resposta sem validação de fontes')
    citations={(c['id'],c['quote']):c for c in result['citations']}
    numbered={};sources=[];lines=[]
    for claim in result['claims']:
        refs=[]
        for evidence in claim['evidence']:
            key=(evidence['chunk_id'],evidence['quote'])
            if key not in citations:raise ValueError('Afirmação sem fonte validada')
            if key not in numbered:
                numbered[key]=len(sources)+1;sources.append(citations[key])
            refs.append('['+str(numbered[key])+']')
        if not refs:raise ValueError('Afirmação sem fonte validada')
        lines.extend([plain(claim['text'])+' '+ ' '.join(dict.fromkeys(refs)),''])
    lines.extend(['## Fontes para conferência',''])
    for number,source in enumerate(sources,1):
        link=source_url(source['url'],source['page'])
        lines.extend(['**['+str(number)+'] Edital PNCP '+plain(source['pncp_id'])+
            ' — arquivo '+str(source['document_sequence'])+', página '+str(source['page'])+' do PDF**',
            '', '[Abrir documento oficial](<'+link+'>)', '',
            '> '+plain(source['quote']), ''])
    lines.append('Confira a passagem no documento original. A abertura direta na página depende do visualizador; a numeração acima conta as páginas do PDF, incluindo capa.')
    return '\n'.join(lines)+'\n'
