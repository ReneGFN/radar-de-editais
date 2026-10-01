"""Coleta restrita ao PNCP; conteúdo bruto permanece fora do Brain."""
import hashlib
import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from .config import PROJECT, emit_json, private_root

API = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
FILES = "https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{year}/{sequence}/arquivos"
MAX_DOWNLOAD = 25 * 1024 * 1024
ALLOWED_TYPES = {2, 4, 5, 6, 7}


def normalized(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def matches_sector(text: str) -> bool:
    from .sector import classify_sector
    return classify_sector(text) in ('in_scope_candidate','mixed_requires_item_review')


def safe_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != "pncp.gov.br" or parts.username or parts.password:
        raise ValueError("Origem de download não permitida")
    # O PNCP fornece links com portas internas antigas. A rota pública usa HTTPS 443.
    # A porta informada não é contatada: todos os links são reconstruídos para 443.
    _ = parts.port
    return urlunsplit(("https", "pncp.gov.br", parts.path, parts.query, ""))


def get(client: httpx.Client, url: str, *, params=None, binary=False):
    url = safe_url(url)
    for attempt in range(3):
        try:
            # Redirects permanecem limitados à origem permitida.
            for _ in range(4):
                with client.stream("GET", url, params=params) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        url = safe_url(urljoin(url, response.headers["location"]))
                        params = None
                        continue
                    if response.status_code == 204:
                        return b"" if binary else {"data": [], "totalPaginas": 0}
                    response.raise_for_status()
                    if int(response.headers.get("content-length", "0")) > MAX_DOWNLOAD:
                        raise ValueError("Download excede o limite")
                    payload = bytearray()
                    for piece in response.iter_bytes():
                        payload.extend(piece)
                        if len(payload) > MAX_DOWNLOAD:
                            raise ValueError("Download excede o limite")
                    return bytes(payload) if binary else json.loads(payload)
            raise ValueError("Muitos redirecionamentos")
        except (httpx.TimeoutException, httpx.TransportError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
        except httpx.HTTPStatusError as exc:
            # Limite do serviço requer interromper e retomar depois, não insistir.
            if exc.response.status_code not in (500, 502, 503, 504) or attempt == 2:
                raise
            time.sleep(attempt + 1)


def select_and_download(start: str, end: str, target: int = 10, uf: str = "SP") -> dict:
    if not re.fullmatch(r"\d{8}", start) or not re.fullmatch(r"\d{8}", end):
        raise ValueError("Datas devem ter formato AAAAMMDD")
    datetime.strptime(start, "%Y%m%d")
    datetime.strptime(end, "%Y%m%d")
    if start > end or not 1 <= target <= 50 or not re.fullmatch(r"[A-Z]{2}", uf):
        raise ValueError("Intervalo, UF ou quantidade inválidos")
    root = private_root()
    collected_at = datetime.now(timezone.utc).isoformat()
    selection = {"sector": "informatica", "uf": uf, "start": start, "end": end,
                 "captured_at": collected_at, "editais": [], "rejections": [], "selection_complete": False}
    client = httpx.Client(timeout=httpx.Timeout(45, connect=15), follow_redirects=False,
                          headers={"User-Agent": "RadarDeEditais/0.1 (portfolio research)"})
    with client:
        page = 1
        while page <= 80 and len(selection["editais"]) < target:
            response = get(client, API, params={"dataInicial": start, "dataFinal": end,
                "codigoModalidadeContratacao": 6, "uf": uf, "pagina": page, "tamanhoPagina": 50})
            for item in response.get("data", []):
                if not matches_sector(item.get("objetoCompra", "")):
                    continue
                identifier = item["numeroControlePNCP"]
                cnpj, year, sequence = item["orgaoEntidade"]["cnpj"], item["anoCompra"], item["sequencialCompra"]
                files_url = FILES.format(cnpj=cnpj, year=year, sequence=sequence)
                try:
                    files = get(client, files_url)
                    if not isinstance(files, list):
                        raise ValueError("Resposta de arquivos inesperada")
                    # Apenas documentos publicados de contratação; exclui propostas de participantes.
                    allowed = [f for f in files if f.get("tipoDocumentoId") in ALLOWED_TYPES]
                    has_edital = any(f.get("tipoDocumentoId") == 2 for f in allowed)
                    if not has_edital:
                        selection["rejections"].append({"pncp_id": identifier, "reason": "sem_edital_na_listagem"})
                        continue
                    if len(allowed) > 12:
                        selection["rejections"].append({"pncp_id": identifier, "reason": "mais_de_12_documentos_requer_revisao"})
                        continue
                    docs = []
                    for info in allowed:
                        url = safe_url(info["url"])
                        content = get(client, url, binary=True)
                        if not content.startswith(b"%PDF-"):
                            selection["rejections"].append({"pncp_id": identifier, "reason": "anexo_nao_pdf", "document_sequence": info["sequencialDocumento"]})
                            continue
                        digest = hashlib.sha256(content).hexdigest()
                        pdf = root / "raw" / f"{digest}.pdf"
                        pdf.parent.mkdir(parents=True, exist_ok=True)
                        if not pdf.exists():
                            pdf.write_bytes(content)
                        docs.append({"sha256": digest, "url": url, "sequence": info["sequencialDocumento"],
                                     "type_id": info["tipoDocumentoId"], "type_name": info.get("tipoDocumentoNome"),
                                     "active": info.get("statusAtivo"), "bytes": len(content),
                                     "source_date": info.get("dataPublicacaoPncp")})
                    if not any(d["type_id"] == 2 for d in docs):
                        selection["rejections"].append({"pncp_id": identifier, "reason": "edital_pdf_ausente"})
                        continue
                    selection["editais"].append({"pncp_id": identifier, "cnpj": cnpj, "year": year,
                        "uf": item.get("unidadeOrgao", {}).get("ufSigla", uf),
                        "sequence": sequence, "agency": item["orgaoEntidade"]["razaoSocial"],
                        "object": item["objetoCompra"], "publication_date": item.get("dataPublicacaoPncp"),
                        "proposal_start": item.get("dataAberturaProposta"), "proposal_end": item.get("dataEncerramentoProposta"),
                        "official_url": f"https://pncp.gov.br/app/editais/{cnpj}/{year}/{sequence}", "documents": docs})
                    print(json.dumps({"selected": len(selection["editais"]), "pncp_id": identifier}, ensure_ascii=False), flush=True)
                    if len(selection["editais"]) == target:
                        break
                except (httpx.HTTPError, ValueError, KeyError) as exc:
                    selection["rejections"].append({"pncp_id": identifier, "reason": type(exc).__name__})
            print(json.dumps({"page": page, "selected": len(selection["editais"])}), flush=True)
            if page >= response.get("totalPaginas", 0):
                break
            page += 1
        selection["selection_complete"] = len(selection["editais"]) == target
    identity = [{"pncp_id": e["pncp_id"], "documents": e["documents"]} for e in selection["editais"]]
    snapshot = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:16]
    selection["snapshot_id"] = snapshot
    manifest = PROJECT / "datasets/manifests" / f"{snapshot}.json"
    if manifest.exists():
        existing = json.loads(manifest.read_text(encoding="utf-8"))
        previous = [{"pncp_id": e["pncp_id"], "documents": e["documents"]} for e in existing["editais"]]
        if previous != identity:
            raise ValueError("Colisão de identidade do snapshot")
        return existing
    emit_json(manifest, selection)
    return selection


def split_pages(pages: list[dict], metadata: dict, token_count=len) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=20,
        length_function=token_count)
    records = []
    for page in pages:
        if page["quality"] != "text":
            continue
        source = Document(page_content=page["text"], metadata={**metadata, "page": page["page"]})
        previous_start = -1
        for chunk in splitter.split_documents([source]):
            # O start_index nativo assume sobreposição em caracteres; aqui usamos tokens.
            start = page["text"].find(chunk.page_content, previous_start + 1)
            end = start + len(chunk.page_content)
            if start < 0 or page["text"][start:end] != chunk.page_content:
                raise ValueError("Trecho sem offsets verificáveis")
            if token_count(chunk.page_content) > 120:
                raise ValueError("Trecho excede o limite de tokens")
            previous_start = start
            identity = f"{metadata['pncp_id']}:{metadata['document_sha']}:{page['page']}:{start}:{chunk.page_content}"
            records.append({"id": hashlib.sha256(identity.encode()).hexdigest(), "text": chunk.page_content,
                "pncp_id": metadata["pncp_id"], "document_sha": metadata["document_sha"],
                "document_sequence": metadata["document_sequence"], "page": page["page"], "start": start, "end": end})
    return records


def hydrate(manifest: Path):
    """Baixa as fontes do snapshot publicado sem selecionar outro corpus."""
    selection=json.loads(manifest.read_text(encoding="utf-8"))
    root=private_root()/"raw"
    root.mkdir(parents=True,exist_ok=True)
    downloaded=0
    with httpx.Client(timeout=httpx.Timeout(45,connect=15),follow_redirects=False) as client:
        for edital in selection["editais"]:
            for source in edital["documents"]:
                digest=source["sha256"]
                if not re.fullmatch(r"[a-f0-9]{64}",digest):
                    raise ValueError("Hash inválido no manifesto")
                path=root/f"{digest}.pdf"
                if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==digest:
                    continue
                content=get(client,source["url"],binary=True)
                if not content.startswith(b"%PDF-") or hashlib.sha256(content).hexdigest()!=digest:
                    raise ValueError("Fonte mudou ou não corresponde ao PDF do snapshot")
                path.write_bytes(content)
                downloaded+=1
                print(json.dumps({"pdfs_downloaded":downloaded,"pncp_id":edital["pncp_id"]}),flush=True)
    return {"snapshot_id":selection["snapshot_id"],"downloaded":downloaded,"hashes_verified":True}


def prepare(manifest: Path) -> dict:
    from .embeddings import local_embeddings
    embeddings = local_embeddings()
    selection = json.loads(manifest.read_text(encoding="utf-8"))
    root = private_root()
    documents, chunks = [], []
    current_config={"extractor":"pypdf/plain","splitter":{"name":"RecursiveCharacterTextSplitter",
        "chunk_size_tokens":120,"overlap_tokens":20},"embedding":embeddings.provenance()}
    cached_documents={}
    cached_chunks={}
    for previous_path in (root/"prepared").glob("*.json"):
        previous=json.loads(previous_path.read_text(encoding="utf-8"))
        if any(previous.get(k)!=v for k,v in current_config.items()): continue
        for doc in previous["documents"]:
            key=(doc["pncp_id"],doc["document_sequence"],doc["document_sha"])
            cached_documents[key]=doc
        for chunk in previous["chunks"]:
            key=(chunk["pncp_id"],chunk["document_sequence"],chunk["document_sha"])
            cached_chunks.setdefault(key,{})[chunk["id"]]=chunk
    reused_documents=0
    for edital in selection["editais"]:
        for source in edital["documents"]:
            pdf = root / "raw" / f"{source['sha256']}.pdf"
            if hashlib.sha256(pdf.read_bytes()).hexdigest() != source["sha256"]:
                raise ValueError("PDF diverge do hash do manifesto")
            key=(edital["pncp_id"],source["sequence"],source["sha256"])
            if key in cached_documents:
                documents.append(cached_documents[key])
                chunks.extend(cached_chunks.get(key,{}).values())
                reused_documents+=1
                continue
            reader = PdfReader(pdf)
            if reader.is_encrypted or len(reader.pages) > 500:
                raise ValueError("PDF protegido ou com mais de 500 páginas requer revisão")
            pages = []
            for index, page in enumerate(reader.pages, start=1):
                text = page.extract_text(extraction_mode="plain") or ""
                # Conteúdo curto não é removido: fica preservado e sinalizado para revisão.
                quality = "text" if len(re.sub(r"\s", "", text)) >= 50 else "needs_review"
                pages.append({"page": index, "text": text, "quality": quality})
            meta = {"pncp_id": edital["pncp_id"], "document_sha": source["sha256"], "document_sequence": source["sequence"]}
            documents.append({**meta, "pages": pages})
            chunks.extend(split_pages(pages, meta, embeddings.token_count))
            print(json.dumps({"documents_prepared":len(documents),"pncp_id":edital["pncp_id"],
                "pages":len(pages),"chunks_so_far":len(chunks)}),flush=True)
    payload = {"snapshot_id": selection["snapshot_id"], "extractor": "pypdf/plain",
        "splitter": {"name": "RecursiveCharacterTextSplitter", "chunk_size_tokens": 120, "overlap_tokens": 20},
        "embedding": current_config["embedding"],
        "documents": documents, "chunks": chunks}
    emit_json(root / "prepared" / f"{selection['snapshot_id']}.json", payload)
    pages = [p for d in documents for p in d["pages"]]
    report = {"snapshot_id": selection["snapshot_id"], "editais": len(selection["editais"]),
        "documents": len(documents), "pages": len(pages), "pages_needing_review": sum(p["quality"] != "text" for p in pages),
        "chunks": len(chunks), "documents_reused":reused_documents,"status": "prepared_not_loaded", "pdf_text_quality": "automatic_check_only_visual_review_pending"}
    emit_json(PROJECT / "reports/preparacao.json", report)
    return report
