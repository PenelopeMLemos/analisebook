import pandas as pd
import streamlit as st
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
import json

# Carrega os segredos do gspread do Streamlit Cloud
gspread_creds = st.secrets["gspread_creds"]

scopes = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Cria o objeto de credenciais a partir do dicionário JSON
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(gspread_creds), 
    scopes=scopes
)

client = gspread.authorize(credentials)

print(client)

planilha_completa = client.open(
    title="Dados Leitura",
    folder_id="1hiewQak1TVAY-fA5oN8ucXtVfmPN5p-h"
)

planilha = planilha_completa.get_worksheet(0)

dados = planilha.get_all_records()

df = pd.DataFrame(dados)

st.set_page_config(layout="wide") #ocupar toda a lateral 

#transformando e ordenar a coluna de data
df["Data de termino da leitura "] = pd.to_datetime(df["Data de termino da leitura "], dayfirst=True)
df = df.sort_values("Data de termino da leitura ")

#coluna de mês para o filtro
df["Mês/Ano"] = df["Data de termino da leitura "].dt.strftime('%m/%Y')

#lista de meses e adicionar "Todos" no início
meses_disponiveis = df["Mês/Ano"].unique().tolist()
meses_disponiveis.insert(0, "Todos")

generos_disponiveis = df["Genero "].unique().tolist()
generos_disponiveis.insert(0, "Todos")

#filtro no sidebar
selected_month = st.sidebar.selectbox("Mês", meses_disponiveis)
selected_genre = st.sidebar.selectbox("Gênero Literário", generos_disponiveis)

df_filtered = df.copy()

#filtrar a tabela com base na seleção
if selected_month == "Todos":
    df_filtered = df
else:
    df_filtered = df[df["Mês/Ano"] == selected_month]


if selected_genre != "Todos":
    df_filtered = df_filtered[df_filtered["Genero "] == selected_genre]

if df_filtered.empty:
    st.warning("Não há dados para os filtros selecionados.")
else:
      #gráfico com os dados filtrados
    fig_gen = px.bar(df_filtered, x="Genero ", y="Lido por ", title="Leitores por Gênero Literário")


st.markdown("<h1 style='text-align: left; padding-left: 20px;'>Análise Literária</h1>", unsafe_allow_html=True) #titulo da pagina

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

#quantidade de leituras por genero literario
df_gen_count = df_filtered.groupby("Genero ").agg({"Lido por ": "count"}).reset_index()

# Gráfico de pizza
fig_gen = px.pie(
    df_gen_count,
    names="Genero ",
    values="Lido por ",
    #title="Leituras por Gênero Literário",
)

col2.subheader("Leituras por Gênero Literário")
col2.plotly_chart(fig_gen, use_container_width=True) #exibir no streamlit

#top 5 livro mais lido 
df_livros_count = df_filtered.groupby("Titulo").agg({"Lido por ": "count"}).reset_index()
df_livros_count = df_livros_count.sort_values("Lido por ", ascending=False)

fig_livros = px.bar(
    df_livros_count.head(5), 
    x="Lido por ", 
    y="Titulo", 
    orientation="h", 
    #title="Top 5 Livros Mais Lidos",
    text="Lido por " 
)

fig_livros.update_traces(textposition='auto')  #coloca os valores automaticamente nas barras
fig_livros.update_layout(yaxis=dict(autorange="reversed"))  #inverter ordem (maior no topo)

col4.subheader("Top 5 Livros Mais Lidos")
col4.plotly_chart(fig_livros, use_container_width=True)

#leitores x genero 
df_grouped = df.groupby(["Lido por ", "Genero "]).agg({"Titulo": "count"}).reset_index()
df_grouped.rename(columns={"Titulo": "Quantidade"}, inplace=True)

fig_lg = px.bar(
    df_grouped,
    x="Lido por ",
    y="Quantidade",
    color="Genero ",
   # title="Quantidade de livros lidos por gênero para cada leitor",
    barmode="stack",
    width=1000,   #largura 
    height=600    #altura  
)

st.subheader("Quantidade de livros lidos por gênero para cada leitor")
st.plotly_chart(fig_lg, use_container_width=True)

#livros lidos por mês
df["Mês_Real"] = pd.to_datetime(df["Mês/Ano"], format="%m/%Y")
df_mensal = df.groupby("Mês_Real").agg({"Titulo": "count"}).reset_index()
df_mensal.rename(columns={"Titulo": "Quantidade de Livros"}, inplace=True)

# Gráfico de linha
fig_mensal = px.line(
    df_mensal,
    x="Mês_Real",
    y="Quantidade de Livros",
    #title="Livros Lidos por Mês",
    markers=True,
    labels={"Mês_Real": "Mês", "Quantidade de Livros": "Total de Livros"},
    text="Quantidade de Livros"
)

fig_mensal.update_traces(textposition="top center")

fig_mensal.update_layout(
    xaxis_title="Mês",
    yaxis_title="Livros Lidos",
    xaxis=dict(
        tickmode="linear",
        dtick="M1",
        tickformat="%b %Y"
    )
)

col3.subheader("Livros lidos por mês")
col3.plotly_chart(fig_mensal, use_container_width=True)

#top 5 leitores

# Agrupar e contar livros por leitor
df_top_leitores = df.groupby("Lido por ").agg({"Titulo": "count"}).reset_index()
df_top_leitores.rename(columns={"Titulo": "Livros Lidos"}, inplace=True)

# Ordenar do maior para o menor e pegar os 5 primeiros
df_top5 = df_top_leitores.sort_values("Livros Lidos", ascending=False).head(5)

col1.subheader("Top 5 Leitores")
for nome in df_top5["Lido por "]:
    col1.markdown(f"•{nome}")