#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_URL = "http://localhost:8080"

# Inicializar sessão
s = requests.Session()
r1 = s.post(
    f'{BASE_URL}/mcp',
    headers={'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'},
    json={'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'test', 'version': '1.0'}}}
)
print('✅ Sessão iniciada')

# Listar tools
r2 = s.post(
    f'{BASE_URL}/mcp',
    headers={'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'},
    json={'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'}
)

data = r2.json()
tools = data.get('result', {}).get('tools', [])
print(f'✅ Tools encontrados: {[t["name"] for t in tools]}')
print(f'\nTotal de tools: {len(tools)}')

# Mostrar detalhes dos tools
for tool in tools:
    print(f'\n📦 Tool: {tool["name"]}')
    print(f'   Descrição: {tool["description"][:80]}...')
    props = tool.get('inputSchema', {}).get('properties', {})
    print(f'   Parâmetros: {list(props.keys())}')

