#!/usr/bin/env python3
"""
Script de teste para o deploy do MCP Server no Railway
Execute após o deploy para verificar se tudo está funcionando
"""

import requests
import json
import os
import sys

# Configurações
AUTH_TOKEN = "450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57"
BASE_URL = input("Digite a URL do seu deploy Railway (ex: https://mcp-server-motherduck-production-xxxx.up.railway.app): ").strip()

if not BASE_URL:
    print("❌ URL é obrigatória!")
    sys.exit(1)

if not BASE_URL.startswith("https://"):
    BASE_URL = f"https://{BASE_URL}"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def test_health_check():
    """Testa o endpoint de health check"""
    print("🔍 Testando Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check OK: {data}")
            return True
        else:
            print(f"❌ Health Check falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no Health Check: {e}")
        return False

def test_mcp_tools_list():
    """Testa o endpoint MCP tools/list"""
    print("🔍 Testando MCP Tools List...")
    try:
        payload = {"method": "tools/list"}
        response = requests.post(f"{BASE_URL}/mcp", headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ MCP Tools List OK: {len(data.get('result', {}).get('tools', []))} tools encontrados")
            return True
        else:
            print(f"❌ MCP Tools List falhou: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro no MCP Tools List: {e}")
        return False

def test_upload_endpoint():
    """Testa o endpoint de upload (sem arquivo real)"""
    print("🔍 Testando Upload Endpoint...")
    try:
        # Teste sem arquivo para verificar autenticação
        response = requests.post(f"{BASE_URL}/upload", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, timeout=10)
        if response.status_code == 400:
            print("✅ Upload Endpoint OK (erro esperado sem arquivo)")
            return True
        else:
            print(f"❌ Upload Endpoint inesperado: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no Upload Endpoint: {e}")
        return False

def test_unauthorized_access():
    """Testa acesso não autorizado"""
    print("🔍 Testando Acesso Não Autorizado...")
    try:
        response = requests.get(f"{BASE_URL}/mcp", timeout=10)
        if response.status_code == 401:
            print("✅ Autenticação funcionando (acesso negado sem token)")
            return True
        else:
            print(f"❌ Autenticação pode estar com problema: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no teste de autenticação: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes do MCP Server no Railway")
    print(f"🌐 URL: {BASE_URL}")
    print(f"🔑 Token: {AUTH_TOKEN[:20]}...")
    print("-" * 50)
    
    tests = [
        test_health_check,
        test_unauthorized_access,
        test_mcp_tools_list,
        test_upload_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("-" * 50)
    print(f"📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Seu MCP está funcionando perfeitamente!")
        print("\n🔗 Integração com LobeChat:")
        print(f"URL: {BASE_URL}/mcp")
        print(f"Token: {AUTH_TOKEN}")
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs no Railway.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
