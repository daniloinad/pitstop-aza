import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

# ─── CONFIG ───
st.set_page_config(
    page_title="🛒 Pit Stop AZA",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SENHA_HASH = hashlib.sha256("mercadinho".encode()).hexdigest()

# ─── ESTILOS ───
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@300;400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
  .main { background-color: #0A0A0A; color: #F5F5F5; }
  h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 2px; }
  .titulo { font-family: 'Bebas Neue', sans-serif; font-size: 2.5rem; color: #FFD700; }
  .subtitulo { color: rgba(245,245,245,0.55); font-size: 0.85rem; letter-spacing: 2px; text-transform: uppercase; }
  .gold { color: #FFD700; }
  .green { color: #00E676; }
  .red { color: #FF1744; }
  .stButton>button { font-family: 'Barlow', sans-serif; font-weight: 700; letter-spacing: 1px; }
  div[data-testid="metric-container"] { background: #161616; border: 1px solid rgba(255,215,0,0.15); border-radius: 12px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# ─── BANCO DE DADOS ───
def get_conn():
    conn = sqlite3.connect("pitstop.db", check_same_thread=False)
    return conn

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
        data TEXT,
        colaborador TEXT,
        operacao TEXT,
        pontos INTEGER,
        motivo TEXT,
        saldo_apos INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS trocas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        colaborador TEXT,
        produto TEXT,
        pontos INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto TEXT UNIQUE,
        pontos INTEGER,
        quantidade INTEGER
    )""")

    # Inserir colaboradores padrão
    colaboradores = [
        "Raianne Santos", "Esteffany Souza", "André Silva",
        "Larisse Garcia", "Wanessa Cardoso", "Arthur Alves", "Wynara dos Reis"
    ]
    for nome in colaboradores:
        c.execute("INSERT OR IGNORE INTO colaboradores (nome) VALUES (?)", (nome,))

    # Inserir produtos padrão
    produtos = [
        ("Fandangos", 120, 10), ("Coca-Cola", 150, 8), ("Torcida", 150, 6),
        ("Corona Individual", 200, 12), ("Monster Energético", 250, 5),
        ("Bis", 300, 7), ("Monster", 400, 4), ("Bala Dadinho", 500, 3),
        ("Pack Corona c/6", 1200, 2), ("Vinho Pérgola", 1500, 2),
        ("Crédito iFood R$50", 2000, 3), ("Uniforme", 3000, 2),
    ]
    for nome, pts, qty in produtos:
        c.execute("INSERT OR IGNORE INTO estoque (produto, pontos, quantidade) VALUES (?,?,?)", (nome, pts, qty))

    conn.commit()
    conn.close()

init_db()

# ─── HELPERS ───
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
    df = pd.read_sql("SELECT * FROM estoque ORDER BY pontos", conn)
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

# ─── REGRAS ───
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

# ─── SESSION STATE ───
if "admin" not in st.session_state:
    st.session_state.admin = False

# ─── HEADER ───
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="titulo">🛒 Pit Stop AZA</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">Equipe INAD AZA · Campanha Junho 2026 · Responsável: Danilo Rodrigues</div>', unsafe_allow_html=True)
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

# ─── ABA 1: RANKING ───
with tab1:
    st.subheader("Ranking de Pontuação")
    df = get_colaboradores()
    if df.empty:
        st.info("Nenhum colaborador cadastrado.")
    else:
        medals = ["🥇", "🥈", "🥉"]
        max_pts = df["pontos"].max() if df["pontos"].max() > 0 else 1

        for i, row in df.iterrows():
            pos = df.index.get_loc(i)
            medal = medals[pos] if pos < 3 else f"#{pos+1}"
            col1, col2, col3, col4 = st.columns([0.5, 2.5, 1.5, 1])
            with col1:
                st.markdown(f"### {medal}")
            with col2:
                st.markdown(f"**{row['nome']}**")
                progress = int(row['pontos'] / max_pts * 100) if max_pts > 0 else 0
                st.progress(progress / 100)
            with col3:
                st.markdown(f"<span style='font-size:1.5rem;color:#FFD700;font-weight:700'>{int(row['pontos']):,} pts</span>".replace(",", "."), unsafe_allow_html=True)
            with col4:
                if st.button(f"📋 Histórico", key=f"hist_{row['nome']}"):
                    st.session_state[f"show_hist_{row['nome']}"] = True

            if st.session_state.get(f"show_hist_{row['nome']}", False):
                hist = get_historico(row['nome'])
                if hist.empty:
                    st.info(f"Nenhum lançamento para {row['nome']}.")
                else:
                    hist_display = hist[["data", "operacao", "pontos", "motivo", "saldo_apos"]].copy()
                    hist_display.columns = ["Data", "Operação", "Pontos", "Motivo", "Saldo após"]
                    st.dataframe(hist_display, use_container_width=True, hide_index=True)
                if st.button("Fechar", key=f"close_hist_{row['nome']}"):
                    st.session_state[f"show_hist_{row['nome']}"] = False
                    st.rerun()
            st.divider()

# ─── ABA 2: ESTOQUE ───
with tab2:
    if not st.session_state.admin:
        st.warning("🔒 Apenas o administrador pode visualizar e editar o estoque.")
    else:
        st.subheader("Estoque de Produtos")
        df_est = get_estoque()
        cols = st.columns(4)
        for i, row in df_est.iterrows():
            with cols[i % 4]:
                status = "🔴 Esgotado" if row['quantidade'] == 0 else ("⚠️ Baixo" if row['quantidade'] <= 2 else "✅ OK")
                color = "#FF1744" if row['quantidade'] <= 2 else "#00E676"
                st.markdown(f"""
                <div style='background:#161616;border:1px solid rgba(255,215,0,0.15);border-radius:12px;padding:16px;margin-bottom:12px;'>
                  <div style='font-weight:600'>{row['produto']}</div>
                  <div style='color:#FFD700;font-size:1.1rem;font-weight:700'>{int(row['pontos']):,} pts</div>
                  <div style='color:{color};font-size:2rem;font-weight:900;line-height:1'>{int(row['quantidade'])}</div>
                  <div style='color:rgba(245,245,245,0.5);font-size:0.8rem'>{status}</div>
                </div>
                """, unsafe_allow_html=True)

        st.subheader("Atualizar Estoque")
        df_est2 = get_estoque()
        prod_opcoes = df_est2["produto"].tolist()
        col1, col2, col3 = st.columns(3)
        with col1:
            prod_sel = st.selectbox("Produto", prod_opcoes, key="st_prod")
        with col2:
            st_op = st.selectbox("Operação", ["Definir total", "Adicionar", "Remover"], key="st_op")
        with col3:
            st_qtd = st.number_input("Quantidade", min_value=0, value=1, key="st_qtd")

        if st.button("✅ Atualizar Estoque"):
            conn = get_conn()
            c = conn.cursor()
            if st_op == "Definir total":
                c.execute("UPDATE estoque SET quantidade=? WHERE produto=?", (st_qtd, prod_sel))
            elif st_op == "Adicionar":
                c.execute("UPDATE estoque SET quantidade=quantidade+? WHERE produto=?", (st_qtd, prod_sel))
            else:
                c.execute("UPDATE estoque SET quantidade=MAX(0,quantidade-?) WHERE produto=?", (st_qtd, prod_sel))
            conn.commit()
            conn.close()
            st.success(f"Estoque de {prod_sel} atualizado!")
            st.rerun()

# ─── ABA 3: TROCAS ───
with tab3:
    if not st.session_state.admin:
        st.warning("🔒 Apenas o administrador pode registrar e visualizar trocas.")
    else:
        st.subheader("Registrar Troca")
        df_cols = get_colaboradores()
        df_est3 = get_estoque()

        col1, col2, col3 = st.columns(3)
        with col1:
            tr_colab = st.selectbox("Colaborador", df_cols["nome"].tolist(), key="tr_colab")
        with col2:
            tr_prod = st.selectbox("Produto", df_est3["produto"].tolist(), key="tr_prod")
        with col3:
            tr_qtd = st.number_input("Quantidade", min_value=1, value=1, key="tr_qtd")

        prod_row = df_est3[df_est3["produto"] == tr_prod].iloc[0]
        colab_row = df_cols[df_cols["nome"] == tr_colab].iloc[0]
        total_pts = int(prod_row["pontos"]) * tr_qtd

        st.info(f"💰 Custo: **{total_pts:,} pts** · Saldo de {tr_colab}: **{int(colab_row['pontos']):,} pts** · Estoque disponível: **{int(prod_row['quantidade'])}**".replace(",", "."))

        if st.button("✅ Confirmar Troca"):
            if colab_row["pontos"] < total_pts:
                st.error("⚠️ Pontos insuficientes!")
            elif prod_row["quantidade"] < tr_qtd:
                st.error("⚠️ Estoque insuficiente!")
            else:
                conn = get_conn()
                c = conn.cursor()
                novo_saldo = int(colab_row["pontos"]) - total_pts
                c.execute("UPDATE colaboradores SET pontos=?, trocas=trocas+? WHERE nome=?", (novo_saldo, tr_qtd, tr_colab))
                c.execute("UPDATE estoque SET quantidade=quantidade-? WHERE produto=?", (tr_qtd, tr_prod))
                c.execute("INSERT INTO trocas (data,colaborador,produto,pontos) VALUES (?,?,?,?)", (now(), tr_colab, tr_prod, total_pts))
                c.execute("INSERT INTO historico (data,colaborador,operacao,pontos,motivo,saldo_apos) VALUES (?,?,?,?,?,?)",
                          (now(), tr_colab, "Desconto", total_pts, f"Troca: {tr_prod}", novo_saldo))
                conn.commit()
                conn.close()
                st.success(f"✅ Troca registrada! {tr_colab} trocou {tr_prod}")
                st.rerun()

        st.divider()
        st.subheader("Histórico de Trocas")
        df_trocas = get_trocas()
        if df_trocas.empty:
            st.info("Nenhuma troca registrada ainda.")
        else:
            df_trocas.columns = ["ID", "Data", "Colaborador", "Produto", "Pontos"]
            st.dataframe(df_trocas.drop("ID", axis=1), use_container_width=True, hide_index=True)

# ─── ABA 4: ADMIN ───
if tab4:
    with tab4:
        st.subheader("⚙️ Painel Admin")

        # LANÇAR PONTOS
        st.markdown("### ➕ Lançar / Descontar Pontos")
        df_cols2 = get_colaboradores()
        col1, col2 = st.columns(2)
        with col1:
            pt_colab = st.selectbox("Colaborador", df_cols2["nome"].tolist(), key="pt_colab")
        with col2:
            categoria = st.selectbox("Categoria", list(REGRAS.keys()), key="pt_cat")

        regras_cat = REGRAS[categoria]
        opcoes = [r[0] for r in regras_cat]
        regra_sel = st.selectbox("Regra", opcoes, key="pt_regra")

        regra_data = next(r for r in regras_cat if r[0] == regra_sel)
        op_auto, pts_auto, motivo_auto = regra_data[1], regra_data[2], regra_data[3]

        col1, col2 = st.columns(2)
        with col1:
            pt_pts = st.number_input("Pontos", min_value=1, value=pts_auto, key="pt_pts")
        with col2:
            pt_op = st.selectbox("Operação", ["add", "sub"], index=0 if op_auto=="add" else 1,
                                  format_func=lambda x: "➕ Adicionar" if x=="add" else "➖ Descontar", key="pt_op")

        pt_motivo = st.text_input("Motivo (editável)", value=motivo_auto, key="pt_motivo")

        if st.button("✅ Confirmar Pontuação", type="primary"):
            conn = get_conn()
            c = conn.cursor()
            colab_row2 = df_cols2[df_cols2["nome"] == pt_colab].iloc[0]
            if pt_op == "add":
                novo_saldo = int(colab_row2["pontos"]) + pt_pts
            else:
                novo_saldo = max(0, int(colab_row2["pontos"]) - pt_pts)
            c.execute("UPDATE colaboradores SET pontos=? WHERE nome=?", (novo_saldo, pt_colab))
            c.execute("INSERT INTO historico (data,colaborador,operacao,pontos,motivo,saldo_apos) VALUES (?,?,?,?,?,?)",
                      (now(), pt_colab, "Adição" if pt_op=="add" else "Desconto", pt_pts, pt_motivo, novo_saldo))
            conn.commit()
            conn.close()
            st.success(f"✅ {'+'if pt_op=='add' else '-'}{pt_pts} pts para {pt_colab}! Novo saldo: {novo_saldo:,} pts".replace(",","."))
            st.rerun()

        st.divider()

        # GERENCIAR COLABORADORES
        st.markdown("### 👤 Gerenciar Colaboradores")
        col1, col2 = st.columns(2)
        with col1:
            novo_colab = st.text_input("Nome do novo colaborador", key="novo_colab")
            if st.button("➕ Adicionar Colaborador"):
                if novo_colab.strip():
                    try:
                        conn = get_conn()
                        conn.execute("INSERT INTO colaboradores (nome) VALUES (?)", (novo_colab.strip(),))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ {novo_colab} adicionado!")
                        st.rerun()
                    except:
                        st.error("Colaborador já existe!")
                else:
                    st.warning("Digite o nome!")

        with col2:
            df_del = get_colaboradores()
            del_colab = st.selectbox("Remover colaborador", df_del["nome"].tolist(), key="del_colab")
            if st.button("🗑️ Remover", type="secondary"):
                conn = get_conn()
                conn.execute("DELETE FROM colaboradores WHERE nome=?", (del_colab,))
                conn.commit()
                conn.close()
                st.success(f"Removido: {del_colab}")
                st.rerun()

        st.divider()

        # HISTÓRICO GERAL
        st.markdown("### 📋 Histórico Geral de Lançamentos")
        df_hist = get_historico()
        if df_hist.empty:
            st.info("Nenhum lançamento ainda.")
        else:
            df_hist_display = df_hist[["data","colaborador","operacao","pontos","motivo","saldo_apos"]].copy()
            df_hist_display.columns = ["Data","Colaborador","Operação","Pontos","Motivo","Saldo após"]
            st.dataframe(df_hist_display, use_container_width=True, hide_index=True)
