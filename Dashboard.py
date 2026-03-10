import pandas as pd
import requests
import streamlit as st
import plotly.express as px

st.set_page_config(layout = 'wide')
st.set_page_config(page_icon='⌛')

def formatar_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('DASHBOARD DE VENDAS')

url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Sul', 'Sudeste', 'Norte', 'Nordeste']
st.sidebar.title('Filtro')
regiao = st.sidebar.selectbox('Região', regioes)
if regiao == 'Brasil':
    regiao=''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)
if todos_anos:
    ano=''
else:
    ano = st.sidebar.slider('Ano', 2020,2023)

query_string = {'regiao':regiao.lower(), 'ano':ano}    
response  = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())

if filtro_vendedores:
    dados=dados[dados['Vendedor'].isin(filtro_vendedores)]

estilo_vendas = dados.groupby('Local da compra')[['Preço']].sum()
estilo_vendas = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(estilo_vendas, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

qtd_estado = dados
qtd_estado['QTD por estado'] = qtd_estado['Local da compra'].count()
qtd_estado = dados.groupby('Local da compra')[['QTD por estado']].count()
qtd_estado = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(qtd_estado, left_on='Local da compra', right_index=True).sort_values('QTD por estado', ascending=False)

qtd_cat = dados
qtd_cat['qtd'] = qtd_cat['Categoria do Produto'].count()
qtd_cat = qtd_cat.groupby('Categoria do Produto')[['qtd']].count()

dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

fig_mapa = px.scatter_geo(estilo_vendas, lat='lat', lon='lon',
                          size='Preço', hover_name='Local da compra',
                          hover_data={'lat':False, 'lon':False},
                          scope = 'south america',
                          template = 'seaborn',
                          title='Mapa do total de vendas por estado')

fig_mapa_estado = px.scatter_geo(qtd_estado, lat='lat', lon='lon',
                          size='QTD por estado', hover_name='Local da compra',
                          hover_data={'lat':False, 'lon':False},
                          scope = 'south america',
                          template = 'seaborn',
                          title='Mapa da quantidade de vendas por estado')

fig_receita_mensal = px.line(receita_mensal, x = 'Mes', y = 'Preço',
                             markers=True, color='Ano', line_dash='Ano',
                             range_y=(0,receita_mensal.max()),
                             title='Receita Mensal')

fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_mapa_barra = px.bar(estilo_vendas.head(), x = 'Local da compra', y = 'Preço',
                        title='Receita por estado (TOP 5)', text_auto = True)

fig_mapa_barra.update_layout(yaxis_title='Receita')

fig_receita_categorias = px.bar(receita_categorias, title='Receita por categoria')

fig_receita_categorias.update_layout(yaxis_title='Receita')

fig_qtd_cat = px.bar(qtd_cat, title='Quantidade de vendas por tipo de produto')

fig_qtd_cat.update_layout(yaxis_title='Quantidade')

aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1:
    col1, col2 = st.columns(2)

    with col1:
        st.metric('Receita', formatar_numero(dados['Preço'].sum()), 'R$')
        st.plotly_chart(fig_mapa, use_container_width = True)
        st.plotly_chart(fig_mapa_barra, use_container_width = True)
        st.dataframe(dados)
    with col2:
        st.metric('Quantidade de vendas', formatar_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_categorias, use_container_width = True)

with aba2:
    col1, col2 = st.columns(2)

    with col1:
        st.metric('Receita', formatar_numero(dados['Preço'].sum()), 'R$')
        st.plotly_chart(fig_qtd_cat, use_container_width=True)
        
    with col2:
        st.metric('Quantidade de vendas', formatar_numero(dados.shape[0]))
        st.plotly_chart(fig_mapa_estado, use_container_width=True)
            
with aba3:
    col1, col2 = st.columns(2)
    qtd = st.number_input('Quantidade de vendedores', 2, 10, 5)

    with col1:
        st.metric('Receita', formatar_numero(dados['Preço'].sum()), 'R$')
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd), x = 'sum',
                                        y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd).index,
                                        title='Receita por vendedores', text_auto=True)
        fig_receita_vendedores.update_layout(yaxis_title='Vendedor(a)', xaxis_title='Receita')
        st.plotly_chart(fig_receita_vendedores, use_container_width = True)
        
    with col2:
        st.metric('Quantidade de vendas', formatar_numero(dados.shape[0]))
        fig_venda_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd), x = 'count',
                                        y=vendedores[['count']].sort_values('count', ascending=False).head(qtd).index,
                                        title='Quantidade de vendas por vendedor')
        fig_venda_vendedores.update_layout(yaxis_title='Vendedor(a)', xaxis_title='Quantidade de vendas')
        st.plotly_chart(fig_venda_vendedores, use_container_width = True)
