"""Sobe a API somente leitura do painel em 127.0.0.1 (nunca em outra interface)."""
import argparse

import uvicorn

HOST = '127.0.0.1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise SystemExit('Porta inválida')
    # host fixo: a API não tem autenticação e não deve ser exposta na rede.
    uvicorn.run('radar.api:app', host=HOST, port=args.port, proxy_headers=False, server_header=False,
                access_log=False, log_level='info')


if __name__ == '__main__':
    main()
