# 🛒 Pit Stop AZA

Sistema de controle de pontuação e estoque da Campanha INAD AZA - Junho 2026.

---

## 🚀 Como publicar no Streamlit Cloud (passo a passo)

### 1. Criar conta no GitHub
- Acesse [github.com](https://github.com) e crie sua conta

### 2. Criar repositório no GitHub
- Clique em **"New repository"**
- Nome: `pitstop-aza`
- Deixe como **Public**
- Clique em **"Create repository"**

### 3. Subir os arquivos
- No repositório criado, clique em **"uploading an existing file"**
- Suba os arquivos: `app.py`, `requirements.txt`, `.gitignore`
- Clique em **"Commit changes"**

### 4. Criar conta no Streamlit Cloud
- Acesse [share.streamlit.io](https://share.streamlit.io)
- Clique em **"Sign up"** e entre com sua conta do GitHub

### 5. Publicar o app
- Clique em **"New app"**
- Selecione o repositório `pitstop-aza`
- Branch: `main`
- Main file path: `app.py`
- Clique em **"Deploy!"**

### 6. Pronto! 🎉
- Seu site vai estar disponível em um link como:
  `https://danilo-pitstop-aza.streamlit.app`
- Compartilhe o link com a equipe!

---

## ⚠️ Importante sobre os dados

O banco de dados (`pitstop.db`) é criado automaticamente quando o app roda.
No Streamlit Cloud os dados ficam salvos enquanto o app estiver ativo.

**Para garantir segurança dos dados**, recomendamos fazer backup periódico
exportando os dados pela aba Admin.

---

## 🔒 Senha Admin
A senha padrão é: **mercadinho**
