
import streamlit as st
import pandas as pd
import sqlite3
from colorama import Fore, Style, init

init(autoreset=True)  # Reset automático das cores no terminal

# Conexão com o banco de dados SQLite
conn = sqlite3.connect("produtos.db", check_same_thread=False)
cursor = conn.cursor()

# Criar tabela se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto TEXT,
    tipo TEXT,
    quantidade INTEGER,
    peso REAL,
    desconto REAL,
    peso_final REAL
)
""")
conn.commit()

st.title("📦 Pesagem das frutas")

# ✅ CALCULADORA NORMAL
st.subheader("🧮 Calcular e descontar peso")

num1 = st.number_input("Número 1", step=1.0, format="%.2f")
num2 = st.number_input("Número 2", step=1.0, format="%.2f")

operacao = st.selectbox("Operação", ["Somar", "Subtrair", "Multiplicar", "Dividir"])

if st.button("Calcular"):
    if operacao == "Somar":
        resultado = num1 + num2
    elif operacao == "Subtrair":
        resultado = num1 - num2
    elif operacao == "Multiplicar":
        resultado = num1 * num2
    elif operacao == "Dividir":
        resultado = num1 / num2 if num2 != 0 else "Erro: divisão por zero"

    st.success(f"Resultado: {resultado}")

st.markdown("---")

# Lista de produtos
produtos_lista = {
    "a": "tomate", "b": "cebola", "c": "cenoura", "d": "melão",
    "e": "manga", "f": "abacate", "g": "beterraba", "h": "goiaba",
    "i": "chuchu", "j": "pepino", "l": "pocam", "m": "laranja",
    "n": "batata", "o": "repolho", "p": "coco", "q": "limão", "r": "maracujá",
    "s": "pêra", "t": "kiwí"
}

# Formulário de entrada
produto = st.selectbox("Selecione o produto:", list(produtos_lista.values()))
tipo = st.radio("Tipo de embalagem:", ["Caixa", "Saco"])
quantidade = st.number_input("Quantidade:", min_value=1, value=1)

# Peso total real fornecido pelo usuário
peso_total_informado = st.number_input("Peso total (kg):", min_value=0.0, step=0.1)

# Desconto opcional
descontar = st.checkbox("Descontar peso?")
desconto = st.number_input("Descontar quantos kg no total?", min_value=0.0, step=0.1) if descontar else 0.0

peso_final = max(peso_total_informado - desconto, 0)

# Salvar no banco (com soma se já existir)
if st.button("Salvar dados"):
    cursor.execute("""
        SELECT id, quantidade, peso, desconto, peso_final
        FROM produtos
        WHERE produto = ? AND tipo = ?
    """, (produto, tipo))
    registro_existente = cursor.fetchone()

    if registro_existente:
        id_existente, qtd_existente, peso_existente, desconto_existente, peso_final_existente = registro_existente
        nova_quantidade = qtd_existente + quantidade
        novo_peso = peso_existente + peso_total_informado
        novo_desconto = desconto_existente + desconto
        novo_peso_final = peso_final_existente + peso_final

        cursor.execute("""
            UPDATE produtos
            SET quantidade = ?, peso = ?, desconto = ?, peso_final = ?
            WHERE id = ?
        """, (nova_quantidade, novo_peso, novo_desconto, novo_peso_final, id_existente))
        conn.commit()
        st.success(f"Registro atualizado: {nova_quantidade} {tipo.lower()}(s) de {produto} | Peso final total: {novo_peso_final:.2f} kg")
    else:
        cursor.execute("""
            INSERT INTO produtos (produto, tipo, quantidade, peso, desconto, peso_final)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (produto, tipo, quantidade, peso_total_informado, desconto, peso_final))
        conn.commit()
        st.success(f"{quantidade} {tipo.lower()}(s) de {produto} salvos com sucesso! Peso final: {peso_final:.2f} kg")

# Filtro por produto
st.subheader("🔎 Filtro de produtos")
todos_os_produtos = ["Todos"] + list(produtos_lista.values())
filtro = st.selectbox("Filtrar por produto:", todos_os_produtos)

query = "SELECT * FROM produtos"
params = ()
if filtro != "Todos":
    query += " WHERE produto = ?"
    params = (filtro,)
df = pd.read_sql_query(query, conn, params=params)

# Exibir a tabela
st.subheader("📋 Registros filtrados:")
st.dataframe(df)

# Peso total do filtro
peso_geral = df["peso_final"].sum() if not df.empty else 0
st.info(f"🔢 Peso total ({filtro}): {peso_geral:.2f} kg")

# Função para exportar com tabela formatada
def exportar_para_txt(dataframe):
    colunas = ["ID", "Produto", "Tipo", "Quantidade", "Peso", "Desconto", "Peso Final"]
    dados = [colunas]

    for _, row in dataframe.iterrows():
        dados.append([
            row["id"],
            row["produto"],
            row["tipo"],
            row["quantidade"],
            f"{row['peso']:.2f}",
            f"{row['desconto']:.2f}",
            f"{row['peso_final']:.2f}"
        ])

    larguras = [max(len(str(item)) for item in col) for col in zip(*dados)]

    def linha_horizontal():
        return "+" + "+".join("-" * (largura + 2) for largura in larguras) + "+\n"

    tabela_txt = linha_horizontal()
    for i, linha in enumerate(dados):
        partes = []
        for idx, item in enumerate(linha):
            if idx in [1, 2]:
                partes.append(" " + str(item).ljust(larguras[idx]) + " ")
            else:
                partes.append(" " + str(item).rjust(larguras[idx]) + " ")

        # Exibir no terminal com cor no cabeçalho
        if i == 0:
            linha_formatada = "|" + "|".join(Fore.YELLOW + Style.BRIGHT + parte + Style.RESET_ALL for parte in partes) + "|"
            print(linha_horizontal(), end="")
            print(linha_formatada)
            print(linha_horizontal(), end="")
        else:
            print("|" + "|".join(partes) + "|")

        tabela_txt += "|" + "|".join(partes) + "|\n"
        if i == 0:
            tabela_txt += linha_horizontal()
    tabela_txt += linha_horizontal()

    peso_geral = dataframe["peso_final"].sum()
    tabela_txt += f"\nPeso total ({filtro}): {peso_geral:.2f} kg\n"

    with open("relatorio_produtos_filtrado.txt", "w", encoding="utf-8") as f:
        f.write(tabela_txt)
    return "relatorio_produtos_filtrado.txt"

# Botão para exportar
if not df.empty and st.button("📄 Exportar filtrado para TXT"):
    arquivo_txt = exportar_para_txt(df)
    with open(arquivo_txt, "rb") as f:
        st.download_button("📥 Baixar relatório filtrado (.txt)", f, file_name=arquivo_txt)

# Excluir registro individual
st.subheader("🗑 Excluir registro individual")
if not df.empty:
    ids_disponiveis = df["id"].tolist()
    id_para_excluir = st.selectbox("Selecione o ID do registro para excluir:", ids_disponiveis)
    if st.button("Excluir registro selecionado"):
        cursor.execute("DELETE FROM produtos WHERE id = ?", (id_para_excluir,))
        conn.commit()
        st.success(f"Registro com ID {id_para_excluir} excluído com sucesso!")
        st.experimental_rerun()
else:
    st.info("Nenhum registro disponível para exclusão.")

# Excluir todos os registros
st.subheader("⚠ Excluir TODOS os registros")
senha_correta = "hortifruti"
senha_usuario = st.text_input("Digite a senha para excluir todos os registros:", type="password")

if st.button("Excluir TODOS os registros"):
    if senha_usuario == senha_correta:
        cursor.execute("DELETE FROM produtos")
        conn.commit()
        st.success("🚨 Todos os registros foram excluídos com sucesso!")
        st.experimental_rerun()
    else:
        st.error("❌ Senha incorreta. A exclusão foi cancelada.")