# 🚀 DEPLOY IMEDIATO NO RAILWAY

## ⚡ PASSO A PASSO RÁPIDO

### 1. Acesse Railway
- Vá para: https://railway.app
- Faça login com sua conta GitHub

### 2. Criar Projeto
- Clique em **"New Project"**
- Selecione **"Deploy from GitHub repo"**
- Escolha: `kaael1/mcp-server-motherduck`

### 3. Configurar Variáveis (OBRIGATÓRIO)
No painel do Railway, vá em **"Variables"** e adicione:

```bash
AUTH_TOKEN=450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57
ALLOWED_ORIGINS=https://quati.ai,https://*.vercel.app
EXCEL_FILES_PATH=/tmp/excel_files
MAX_FILE_SIZE=52428800
```

### 4. Deploy Automático
- Railway detectará automaticamente o `railway.json`
- Build será feito com Nixpacks
- Deploy com DuckDB em memória e respostas JSON

### 5. Obter URL
- Após deploy, vá em **"Settings"** → **"Networking"**
- Copie a URL pública (ex: `https://mcp-server-motherduck-production-xxxx.up.railway.app`)

## 🧪 TESTE IMEDIATO

Substitua `SEU_URL_RAILWAY` pela URL do seu deploy:

```bash
# Health Check
curl https://SEU_URL_RAILWAY/health

# Upload Excel
curl -X POST https://SEU_URL_RAILWAY/upload \
  -H "Authorization: Bearer 450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57" \
  -F "file=@teste.xlsx"

# MCP Tools
curl -X POST https://SEU_URL_RAILWAY/mcp \
  -H "Authorization: Bearer 450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57" \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'
```

## 🔗 INTEGRAÇÃO LOBECHAT

Configure no LobeChat:

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
        "https://SEU_URL_RAILWAY/mcp"
      ]
    }
  }
}
```

## ✅ FUNCIONALIDADES PRONTAS

- ✅ Upload Excel (.xlsx/.xls até 50MB)
- ✅ Análise SQL com DuckDB em memória
- ✅ Autenticação Bearer Token segura
- ✅ CORS restrito ao quati.ai
- ✅ Respostas JSON estruturadas
- ✅ Download de resultados Excel
- ✅ Health check endpoint
- ✅ Armazenamento temporário em /tmp

## 🎯 TOKEN DE AUTENTICAÇÃO

```
450c981e114c3073b6cdf07ece0c27982c0a39c267e4339524b40e2a288bfe57
```

**GUARDE ESTE TOKEN! Ele é necessário para todas as requisições.**

## 📞 SUPORTE

Se houver problemas:
1. Verifique os logs no Railway
2. Confirme se todas as variáveis foram configuradas
3. Teste o health check primeiro
4. Verifique se o token está correto

**SEU MCP ESTÁ 100% PRONTO PARA PRODUÇÃO! 🎉**
