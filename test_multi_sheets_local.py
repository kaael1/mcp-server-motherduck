#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste local para múltiplas sheets
Execute com: python test_multi_sheets_local.py
"""
import requests
import json
import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_URL = "http://localhost:8080"

def test_upload():
    """Teste 1: Upload de arquivo Excel"""
    print("🔍 Teste 1: Upload de arquivo Excel...")
    
    # Verificar se arquivo de teste existe
    if not os.path.exists("test_excel.xlsx"):
        print("❌ Arquivo test_excel.xlsx não encontrado!")
        print("💡 Crie um arquivo Excel com múltiplas sheets para testar")
        return None
    
    with open("test_excel.xlsx", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            files={"file": f}
        )
    
    if response.status_code == 200:
        data = response.json()
        file_id = data.get("fileId")
        print(f"✅ Upload OK - FileID: {file_id}")
        return file_id
    else:
        print(f"❌ Upload falhou: {response.status_code}")
        print(response.text)
        return None

def test_list_sheets(file_id):
    """Teste 2: Listar sheets"""
    print(f"\n🔍 Teste 2: Listar sheets do arquivo {file_id}...")
    
    response = requests.get(f"{BASE_URL}/files/{file_id}/sheets")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Lista de sheets OK:")
        print(json.dumps(data, indent=2))
        return True
    else:
        print(f"❌ Listar sheets falhou: {response.status_code}")
        print(response.text)
        return False

def test_query_with_sheet(file_id, sheet_name):
    """Teste 3: Query com sheet específica"""
    print(f"\n🔍 Teste 3: Query na sheet '{sheet_name}'...")
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "query",
            "arguments": {
                "query": f"SELECT * FROM \"{sheet_name}\" LIMIT 3",
                "fileId": file_id,
                "sheet": sheet_name
            }
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/mcp",
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Query OK:")
        print(json.dumps(data, indent=2)[:500] + "...")
        return True
    else:
        print(f"❌ Query falhou: {response.status_code}")
        print(response.text)
        return False

def test_discover_structure(file_id):
    """Teste 4: Descobrir estrutura"""
    print(f"\n🔍 Teste 4: Descobrir estrutura do arquivo {file_id}...")
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "discover_structure",
            "arguments": {
                "fileId": file_id,
                "sheet": "*",
                "sampleRows": 3
            }
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/mcp",
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Discover structure OK:")
        print(json.dumps(data, indent=2)[:1000] + "...")
        return True
    else:
        print(f"❌ Discover structure falhou: {response.status_code}")
        print(response.text)
        return False

def test_tools_list():
    """Teste 5: Listar tools disponíveis"""
    print(f"\n🔍 Teste 5: Listar tools MCP...")
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    }
    
    response = requests.post(
        f"{BASE_URL}/mcp",
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        tools = data.get("result", {}).get("tools", [])
        print(f"✅ Tools disponíveis: {[t['name'] for t in tools]}")
        return True
    else:
        print(f"❌ Listar tools falhou: {response.status_code}")
        print(response.text)
        return False

def main():
    print("🚀 Iniciando testes locais de múltiplas sheets")
    print(f"🌐 Servidor: {BASE_URL}\n")
    
    # Teste 1: Upload
    file_id = test_upload()
    if not file_id:
        sys.exit(1)
    
    # Teste 2: Listar sheets
    if not test_list_sheets(file_id):
        print("⚠️  Teste de listar sheets falhou, mas continuando...")
    
    # Teste 3: Query com sheet (assumindo Sheet1 existe)
    if not test_query_with_sheet(file_id, "Sheet1"):
        print("⚠️  Teste de query com sheet falhou, mas continuando...")
    
    # Teste 4: Discover structure
    if not test_discover_structure(file_id):
        print("⚠️  Teste de discover structure falhou, mas continuando...")
    
    # Teste 5: Tools list
    test_tools_list()
    
    print("\n" + "="*50)
    print("✅ Testes concluídos! Verifique os resultados acima.")
    print("="*50)

if __name__ == "__main__":
    main()

