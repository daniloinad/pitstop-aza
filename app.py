import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

st.set_page_config(
    page_title="🛒 Pit Stop AZA",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SENHA_HASH = hashlib.sha256("mercadinho".encode()).hexdigest()

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@300;400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
  h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 2px; }
  div[data-testid="metric-container"] {
    background: #161616;
    border: 1px solid rgba(255,215,0,0.15);
    border-radius: 12px; padding: 12px;
  }
</style>
""", unsafe_allow_html=True)

# ─── BANCO DE DADOS ───
def get_conn():
    return sqlite3.connect("pitstop.db", check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS colaboradores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL,
        pontos INTEGER DEFAULT 0,
        trocas INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, colaborador TEXT, operacao TEXT,
        pontos INTEGER, motivo TEXT, saldo_apos INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS trocas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, colaborador TEXT, produto TEXT, pontos INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto TEXT UNIQUE, pontos INTEGER, quantidade INTEGER
    )""")

    colaboradores = [
        "Raianne Santos","Esteffany Souza","André Silva",
        "Larisse Garcia","Wanessa Cardoso","Arthur Alves","Wynara dos Reis"
    ]
    for nome in colaboradores:
        c.execute("INSERT OR IGNORE INTO colaboradores (nome) VALUES (?)", (nome,))

    produtos = [
        ("Bala Halls", 0, 0),
        ("Bisc. Passa Tempo", 0, 0),
        ("Bis", 300, 7),
        ("Bala Dadinho 5un", 500, 3),
        ("Cheetos", 120, 0),
        ("Chiclete Trident", 0, 0),
        ("Corona Individual", 200, 12),
        ("Crédito iFood R$50", 2000, 3),
        ("Fandangos", 120, 10),
        ("Monster", 400, 4),
        ("Monster Energético", 250, 5),
        ("Pack Corona c/6", 1200, 2),
        ("Torcida", 150, 6),
        ("Uniforme", 3000, 2),
        ("Vale Churrascaria Individual", 0, 0),
    ]
    for nome, pts, qty in produtos:
        c.execute("INSERT OR IGNORE INTO estoque (produto, pontos, quantidade) VALUES (?,?,?)", (nome, pts, qty))

    conn.commit()
    conn.close()

init_db()

def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def check_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest() == SENHA_HASH

def get_colaboradores():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM colaboradores ORDER BY pontos DESC", conn)
    conn.close()
    return df

def get_estoque():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM estoque ORDER BY produto", conn)
    conn.close()
    return df

def get_historico(colaborador=None):
    conn = get_conn()
    if colaborador:
        df = pd.read_sql("SELECT * FROM historico WHERE colaborador=? ORDER BY id DESC", conn, params=(colaborador,))
    else:
        df = pd.read_sql("SELECT * FROM historico ORDER BY id DESC", conn)
    conn.close()
    return df

def get_trocas():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM trocas ORDER BY id DESC", conn)
    conn.close()
    return df

REGRAS = {
    "⏰ Pontualidade": [
        ("🟢 +100 pts — Sem atraso na semana", "add", 100, "Não teve atraso durante a semana"),
        ("🟢 +10 pts — Sem atraso no dia", "add", 10, "Não teve atraso no dia"),
        ("🔴 -5 pts — Cada minuto de atraso", "sub", 5, "Minuto de atraso"),
    ],
    "💰 Financeiro": [
        ("🟢 +50 pts — Unificação acima de R$ 500", "add", 50, "Unificação paga acima de R$ 500,00"),
        ("🟢 +150 pts — Unificação acima de R$ 1.000", "add", 150, "Unificação paga acima de R$ 1.000,00"),
        ("🟢 +300 pts — A cada R$ 50 mil recebidos", "add", 300, "A cada R$ 50 mil recebidos no mês"),
        ("🟢 +1.000 pts — Meta de R$ 200 mil batida", "add", 1000, "Bateu meta individual de R$ 200 mil"),
    ],
    "⭐ Qualidade": [
        ("🟢 +200 pts — 2 monitorias 100% na semana", "add", 200, "2 monitorias da semana com 100%"),
    ],
    "🔒 Retenção": [
        ("🟢 +50 pts — A cada 2 retenções", "add", 50, "A cada 2 retenções realizadas"),
    ],
    "📞 Operação": [
        ("🟢 +100 pts — 140 ligações diárias acima de 5s", "add", 100, "140 ligações diárias acima de 5 segundos"),
        ("🟢 +100 pts — 200 chats diários", "add", 100, "200 chats diários"),
    ],
    "📋 Disciplina": [
        ("🟢 +50 pts — Sem atraso na pausa de 30min", "add", 50, "Não atrasou na pausa de 30 minutos"),
        ("🟢 +50 pts — Sem atraso no almoço", "add", 50, "Não atrasou no almoço"),
        ("🔴 -100 pts — Veio sem uniforme", "sub", 100, "Veio sem uniforme"),
        ("🔴 -50 pts — Ajuste de ponto", "sub", 50, "Ajuste de ponto"),
    ],
}

if "admin" not in st.session_state:
    st.session_state.admin = False

# ─── HEADER ───
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("# 🛒 Pit Stop AZA")
    st.markdown("**Equipe INAD AZA · Campanha Junho 2026 · Responsável: Danilo Rodrigues**")
with col2:
    if not st.session_state.admin:
        with st.expander("🔒 Admin"):
            senha = st.text_input("Senha", type="password", key="senha_input")
            if st.button("Entrar"):
                if check_senha(senha):
                    st.session_state.admin = True
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
    else:
        st.success("🔓 Admin ativo")
        if st.button("🔒 Sair"):
            st.session_state.admin = False
            st.rerun()

st.divider()

# ─── ABAS ───
if st.session_state.admin:
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Ranking", "📦 Estoque", "🔄 Trocas", "⚙️ Admin"])
else:
    tab1, tab2, tab3 = st.tabs(["🏆 Ranking", "📦 Estoque", "🔄 Trocas"])
    tab4 = None

# ─── RANKING ───
with tab1:
    st.subheader("🏆 Ranking de Pontuação")
    df = get_colaboradores()
    medals = ["🥇", "🥈", "🥉"]
    max_pts = df["pontos"].max() if not df.empty and df["pontos"].max() > 0 else 1

    for i, row in df.iterrows():
        pos = list(df.index).index(i)
        medal = medals[pos] if pos < 3 else f"#{pos+1}"
        col1, col2, col3, col4 = st.columns([0.5, 2.5, 1.5, 1])
        with col1:
            st.markdown(f"### {medal}")
        with col2:
            st.markdown(f"**{row['nome']}**")
            pct = int(row['pontos'] / max_pts * 100) if max_pts > 0 else 0
            st.progress(pct / 100)
        with col3:
            st.markdown(f"<span style='font-size:1.4rem;color:#FFD700;font-weight:700'>{int(row['pontos']):,} pts</span>".replace(",", "."), unsafe_allow_html=True)
        with col4:
            if st.button("📋 Histórico", key=f"h_{row['nome']}"):
                st.session_state[f"show_{row['nome']}"] = not st.session_state.get(f"show_{row['nome']}", False)

        if st.session_state.get(f"show_{row['nome']}", False):
            hist = get_historico(row['nome'])
            if hist.empty:
                st.info(f"Nenhum lançamento para {row['nome']}.")
            else:
                h = hist[["data","operacao","pontos","motivo","saldo_apos"]].copy()
                h.columns = ["Data","Operação","Pontos","Motivo","Saldo após"]
                st.dataframe(h, use_container_width=True, hide_index=True)
        st.divider()

# ─── ESTOQUE ───
with tab2:
    if not st.session_state.admin:
        st.warning("🔒 Apenas o administrador pode visualizar e editar o estoque.")
    else:
        st.subheader("📦 Estoque de Produtos")
        df_est = get_estoque()
        cols = st.columns(4)
        for i, row in df_est.iterrows():
            indisp = row['pontos'] == 0 or row['quantidade'] == 0
            with cols[i % 4]:
                status = "🚫 Indisponível" if indisp else ("⚠️ Baixo" if row['quantidade'] <= 2 else "✅ OK")
                color = "#FF1744" if indisp else ("#FFA500" if row['quantidade'] <= 2 else "#00E676")
                pts_str = "— pts" if row['pontos'] == 0 else f"{int(row['pontos']):,} pts".replace(",",".")
                st.markdown(f"""
                <div style='background:#161616;border:1px solid rgba(255,215,0,0.15);border-radius:12px;
                padding:16px;margin-bottom:12px;{"opacity:0.5" if indisp else ""}'>
                  <div style='font-weight:600;font-size:13px'>{row['produto']}</div>
                  <div style='color:#FFD700;font-size:1rem;font-weight:700'>{pts_str}</div>
                  <div style='color:{color};font-size:1.8rem;font-weight:900;line-height:1'>{int(row['quantidade'])}</div>
                  <div style='color:rgba(245,245,245,0.5);font-size:0.75rem'>{status}</div>
                </div>""", unsafe_allow_html=True)

        st.divider()
        st.markdown("### ↕️ Atualizar Quantidade")
        df_est2 = get_estoque()
        c1, c2, c3 = st.columns(3)
        with c1: prod_sel = st.selectbox("Produto", df_est2["produto"].tolist(), key="st_prod")
        with c2: st_op = st.selectbox("Operação", ["Definir total", "Adicionar", "Remover"], key="st_op")
        with c3: st_qtd = st.number_input("Quantidade", min_value=0, value=1, key="st_qtd")
        if st.button("✅ Atualizar Quantidade"):
            conn = get_conn()
            c = conn.cursor()
            if st_op == "Definir total":
                c.execute("UPDATE estoque SET quantidade=? WHERE produto=?", (st_qtd, prod_sel))
            elif st_op == "Adicionar":
                c.execute("UPDATE estoque SET quantidade=quantidade+? WHERE produto=?", (st_qtd, prod_sel))
            else:
                c.execute("UPDATE estoque SET quantidade=MAX(0,quantidade-?) WHERE produto=?", (st_qtd, prod_sel))
            conn.commit(); conn.close()
            st.success(f"✅ Estoque de {prod_sel} atualizado!"); st.rerun()

        st.divider()
        st.markdown("### ➕ Cadastrar Novo Produto")
        c1, c2, c3 = st.columns(3)
        with c1: novo_prod = st.text_input("Nome do produto", key="novo_prod")
        with c2: novo_pts = st.number_input("Pontos", min_value=0, value=0, key="novo_pts")
        with c3: novo_qtd = st.number_input("Quantidade inicial", min_value=0, value=0, key="novo_qtd")
        if st.button("➕ Cadastrar Produto"):
            if novo_prod.strip():
                try:
                    conn = get_conn()
                    conn.execute("INSERT INTO estoque (produto, pontos, quantidade) VALUES (?,?,?)", (novo_prod.strip(), novo_pts, novo_qtd))
                    conn.commit(); conn.close()
                    st.success(f"✅ {novo_prod} cadastrado!"); st.rerun()
                except: st.error("Produto já existe!")
            else: st.warning("Digite o nome!")

        st.divider()
        st.markdown("### 🗑️ Remover Produto")
        df_est3 = get_estoque()
        del_prod = st.selectbox("Produto para remover", df_est3["produto"].tolist(), key="del_prod")
        if st.button("🗑️ Remover Produto", type="secondary"):
            if st.session_state.get("confirm_del") == del_prod:
                conn = get_conn()
                conn.execute("DELETE FROM estoque WHERE produto=?", (del_prod,))
                conn.commit(); conn.close()
                st.session_state.pop("confirm_del", None)
                st.success(f"Removido: {del_prod}"); st.rerun()
            else:
                st.session_state["confirm_del"] = del_prod
                st.warning(f"Clique novamente para confirmar a remoção de **{del_prod}**")

        st.divider()
        st.markdown("### 💰 Atualizar Pontos do Produto")
        df_est4 = get_estoque()
        c1, c2 = st.columns(2)
        with c1: prod_pts_sel = st.selectbox("Produto", df_est4["produto"].tolist(), key="prod_pts_sel")
        with c2: novo_valor_pts = st.number_input("Novos pontos", min_value=0, value=0, key="novo_valor_pts")
        if st.button("💰 Atualizar Pontos"):
            conn = get_conn()
            conn.execute("UPDATE estoque SET pontos=? WHERE produto=?", (novo_valor_pts, prod_pts_sel))
            conn.commit(); conn.close()
            st.success(f"✅ Pontos de {prod_pts_sel} atualizados para {novo_valor_pts}!"); st.rerun()

# ─── TROCAS ───
with tab3:
    if not st.session_state.admin:
        st.warning("🔒 Apenas o administrador pode registrar e visualizar trocas.")
    else:
        st.subheader("🔄 Registrar Troca")
        df_cols = get_colaboradores()
        df_est5 = get_estoque()
        disponiveis = df_est5[(df_est5['pontos'] > 0) & (df_est5['quantidade'] > 0)]

        c1, c2, c3 = st.columns(3)
        with c1: tr_colab = st.selectbox("Colaborador", df_cols["nome"].tolist(), key="tr_colab")
        with c2: tr_prod = st.selectbox("Produto", disponiveis["produto"].tolist() if not disponiveis.empty else ["Nenhum disponível"], key="tr_prod")
        with c3: tr_qtd = st.number_input("Quantidade", min_value=1, value=1, key="tr_qtd")

        if not disponiveis.empty and tr_prod != "Nenhum disponível":
            prod_row = df_est5[df_est5["produto"] == tr_prod].iloc[0]
            colab_row = df_cols[df_cols["nome"] == tr_colab].iloc[0]
            total_pts = int(prod_row["pontos"]) * tr_qtd
            st.info(f"💰 Custo: **{total_pts:,} pts** · Saldo de {tr_colab}: **{int(colab_row['pontos']):,} pts** · Estoque: **{int(prod_row['quantidade'])}**".replace(",","."))

            if st.button("✅ Confirmar Troca"):
                if colab_row["pontos"] < total_pts:
                    st.error("⚠️ Pontos insuficientes!")
                elif prod_row["quantidade"] < tr_qtd:
                    st.error("⚠️ Estoque insuficiente!")
                else:
                    conn = get_conn(); cur = conn.cursor()
                    novo_saldo = int(colab_row["pontos"]) - total_pts
                    cur.execute("UPDATE colaboradores SET pontos=?, trocas=trocas+? WHERE nome=?", (novo_saldo, tr_qtd, tr_colab))
                    cur.execute("UPDATE estoque SET quantidade=quantidade-? WHERE produto=?", (tr_qtd, tr_prod))
                    cur.execute("INSERT INTO trocas (data,colaborador,produto,pontos) VALUES (?,?,?,?)", (now(), tr_colab, tr_prod, total_pts))
                    cur.execute("INSERT INTO historico (data,colaborador,operacao,pontos,motivo,saldo_apos) VALUES (?,?,?,?,?,?)", (now(), tr_colab, "Desconto", total_pts, f"Troca: {tr_prod}", novo_saldo))
                    conn.commit(); conn.close()
                    st.success(f"✅ {tr_colab} trocou {tr_prod}!"); st.rerun()

        st.divider()
        st.subheader("Histórico de Trocas")
        df_trocas = get_trocas()
        if df_trocas.empty:
            st.info("Nenhuma troca registrada ainda.")
        else:
            df_trocas.columns = ["ID","Data","Colaborador","Produto","Pontos"]
            st.dataframe(df_trocas.drop("ID",axis=1), use_container_width=True, hide_index=True)

# ─── ADMIN ───
if tab4:
    with tab4:
        st.subheader("⚙️ Painel Admin")

        st.markdown("### ➕ Lançar / Descontar Pontos")
        df_cols2 = get_colaboradores()
        c1, c2 = st.columns(2)
        with c1: pt_colab = st.selectbox("Colaborador", df_cols2["nome"].tolist(), key="pt_colab")
        with c2: categoria = st.selectbox("Categoria", list(REGRAS.keys()), key="pt_cat")

        regras_cat = REGRAS[categoria]
        regra_sel = st.selectbox("Regra", [r[0] for r in regras_cat], key="pt_regra")
        regra_data = next(r for r in regras_cat if r[0] == regra_sel)

        c1, c2 = st.columns(2)
        with c1: pt_pts = st.number_input("Pontos", min_value=1, value=regra_data[2], key="pt_pts")
        with c2: pt_op = st.selectbox("Operação", ["add","sub"], index=0 if regra_data[1]=="add" else 1, format_func=lambda x:"➕ Adicionar" if x=="add" else "➖ Descontar", key="pt_op")
        pt_motivo = st.text_input("Motivo (editável)", value=regra_data[3], key="pt_motivo")

        if st.button("✅ Confirmar Pontuação", type="primary"):
            conn = get_conn(); cur = conn.cursor()
            colab_row = df_cols2[df_cols2["nome"]==pt_colab].iloc[0]
            novo_saldo = int(colab_row["pontos"]) + pt_pts if pt_op=="add" else max(0, int(colab_row["pontos"]) - pt_pts)
            cur.execute("UPDATE colaboradores SET pontos=? WHERE nome=?", (novo_saldo, pt_colab))
            cur.execute("INSERT INTO historico (data,colaborador,operacao,pontos,motivo,saldo_apos) VALUES (?,?,?,?,?,?)", (now(), pt_colab, "Adição" if pt_op=="add" else "Desconto", pt_pts, pt_motivo, novo_saldo))
            conn.commit(); conn.close()
            st.success(f"✅ {'+'if pt_op=='add'else'-'}{pt_pts} pts para {pt_colab}! Saldo: {novo_saldo:,} pts".replace(",",".")); st.rerun()

        st.divider()
        st.markdown("### 👤 Gerenciar Colaboradores")
        c1, c2 = st.columns(2)
        with c1:
            novo_colab = st.text_input("Nome do novo colaborador", key="novo_colab")
            if st.button("➕ Adicionar Colaborador"):
                if novo_colab.strip():
                    try:
                        conn = get_conn()
                        conn.execute("INSERT INTO colaboradores (nome) VALUES (?)", (novo_colab.strip(),))
                        conn.commit(); conn.close()
                        st.success(f"✅ {novo_colab} adicionado!"); st.rerun()
                    except: st.error("Colaborador já existe!")
                else: st.warning("Digite o nome!")
        with c2:
            df_del = get_colaboradores()
            del_colab = st.selectbox("Remover colaborador", df_del["nome"].tolist(), key="del_colab")
            if st.button("🗑️ Remover", type="secondary"):
                conn = get_conn()
                conn.execute("DELETE FROM colaboradores WHERE nome=?", (del_colab,))
                conn.commit(); conn.close()
                st.success(f"Removido: {del_colab}"); st.rerun()

        st.divider()
        st.markdown("### 📋 Histórico Geral")
        df_hist = get_historico()
        if df_hist.empty:
            st.info("Nenhum lançamento ainda.")
        else:
            h = df_hist[["data","colaborador","operacao","pontos","motivo","saldo_apos"]].copy()
            h.columns = ["Data","Colaborador","Operação","Pontos","Motivo","Saldo após"]
            st.dataframe(h, use_container_width=True, hide_index=True)
