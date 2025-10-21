# 🚀 Deploy no Railway - Instruções Completas

## Token de Autenticação Gerado
```
AUTH_TOKEN=450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57
```

## 📋 Passos para Deploy

### 1. Acessar Railway
- Vá para [railway.app](https://railway.app)
- Faça login com sua conta GitHub

### 2. Criar Novo Projeto
- Clique em "New Project"
- Selecione "Deploy from GitHub repo"
- Escolha o repositório: `kaael1/mcp-server-motherduck`

### 3. Configurar Variáveis de Ambiente
No painel do Railway, vá em "Variables" e adicione:

```bash
# Obrigatório
AUTH_TOKEN=450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57

# Opcionais (com defaults)
ALLOWED_ORIGINS=https://quati.ai,https://*.vercel.app
EXCEL_FILES_PATH=/app/excel_files
MAX_FILE_SIZE=52428800
```

### 4. Deploy Automático
- Railway detectará automaticamente o `railway.json`
- Fará o build usando Nixpacks
- Deployará com: `uvx mcp-server-motherduck --transport stream --port $PORT --db-path :memory: --json-response`

## 🧪 Testes Pós-Deploy

Após o deploy, teste os endpoints:

### Health Check
```bash
curl https://seu-app.railway.app/health
```

### Upload de Excel
```bash
curl -X POST https://seu-app.railway.app/upload \
  -H "Authorization: Bearer 450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57" \
  -F "file=@teste.xlsx"
```

### MCP Tools List
```bash
curl -X POST https://seu-app.railway.app/mcp \
  -H "Authorization: Bearer 450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57" \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'
```

### Query com Excel
```bash
curl -X POST https://seu-app.railway.app/mcp \
  -H "Authorization: Bearer 450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57" \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "query", "arguments": {"query": "SELECT * FROM \"{{file}}\" LIMIT 10", "fileId": "SEU_FILE_ID_AQUI"}}}'
```

## 🔗 Integração com LobeChat

Após o deploy, configure o LobeChat para usar:

```json
{
  "mcpServers": {
    "duckdb-excel": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Authorization: Bearer 450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57",
        "-H", "Content-Type: application/json",
        "-d", "@-",
        "https://seu-app.railway.app/mcp"
      ]
    }
  }
}
```

## ✅ Funcionalidades Implementadas

- ✅ Upload de Excel (.xlsx/.xls até 50MB)
- ✅ Análise SQL com DuckDB em memória
- ✅ Autenticação Bearer Token segura
- ✅ CORS restrito ao quati.ai
- ✅ Respostas JSON estruturadas
- ✅ Download de resultados em Excel
- ✅ Health check endpoint
- ✅ Armazenamento temporário em /tmp

## 🎯 URL do Deploy

Após o deploy, você receberá uma URL como:
`https://mcp-server-motherduck-production-xxxx.up.railway.app`

Substitua `seu-app.railway.app` por essa URL nos comandos de teste.
