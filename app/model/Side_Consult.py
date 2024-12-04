import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
#Funç t/READ arqvs saved
@st.cache_data
def read_files():
    stored_folder = "app/Arquivos_Armazenados"
    veiculo_file_path = os.path.join(stored_folder, "veiculo_data.bin")
    abastecimento_file_path = os.path.join(stored_folder, "abastecimento_data.bin")    
    #Verify if-arqv exist
    if not os.path.exists(veiculo_file_path):
        st.error(f"Arquivo não encontrado: {veiculo_file_path}")
        return None, None
    if not os.path.exists(abastecimento_file_path):
        st.error(f"Arquivo não encontrado: {abastecimento_file_path}")
        return None, None
    
    with open(veiculo_file_path, "rb") as f:
        veiculo_data = f.read()
    with open(abastecimento_file_path, "rb") as f:
        abastecimento_data = f.read()
        
    veiculo_df = pd.read_excel(io.BytesIO(veiculo_data), engine='openpyxl')
    abastecimento_df = pd.read_excel(io.BytesIO(abastecimento_data), engine='openpyxl')
    
    return veiculo_df, abastecimento_df

#Read dados->arquivos
veiculo_df, abastecimento_df = read_files()

#Verify if DataFrames were properly loaded
if veiculo_df is None or abastecimento_df is None:
    st.stop()

#Convert colun'Data Req.'p/type datetime
abastecimento_df['Data Req.'] = pd.to_datetime(abastecimento_df['Data Req.'], errors='coerce', dayfirst=True)
#Exclud coluns indesjds
columns_exclud = ["Combustível", "Vlr. Unitário", "Hora Abast.", "Abast. Externo"]
current_columns = [col for col in columns_exclud if col in abastecimento_df.columns]
if current_columns:
    abastecimento_df = abastecimento_df.drop(columns=current_columns)
#Order data BY'Data Req.'(form ascend)
abastecimento_df = abastecimento_df.sort_values(by=['Data Req.'])
#Calc dif->Km|Horim p/kdá Veículo/Equip.
abastecimento_df['Diferença de Km'] = abastecimento_df.groupby('Veículo/Equip.')['Km Atual'].diff().abs()
abastecimento_df['Diferença de Horim'] = abastecimento_df.groupby('Veículo/Equip.')['Horim. Equip.'].diff().abs()
#GET value-Litros do abastecimento anterior p/each Veículo/Equip.
abastecimento_df['Litros Anterior'] = abastecimento_df.groupby('Veículo/Equip.')['Litros'].shift(1)
#Calc Km||Horim/Litro
abastecimento_df['Km por Litro'] = abastecimento_df['Diferença de Km'] / abastecimento_df['Litros Anterior']
abastecimento_df['Horim por Litro'] = abastecimento_df['Diferença de Horim'] / abastecimento_df['Litros Anterior']
#Arredond-values
abastecimento_df['Km por Litro'] = abastecimento_df['Km por Litro'].round(3)
abastecimento_df['Horim por Litro'] = abastecimento_df['Horim por Litro'].round(3)
#Calc GAS LEFT
abastecimento_df['Combustível Restante'] = abastecimento_df['Diferença de Km'] % abastecimento_df['Litros Anterior']
abastecimento_df['Combustível Restante'] = abastecimento_df['Combustível Restante'].round(3)
#Reformt colun'Data Req.'p/exib no format desejd usand .loc[]
abastecimento_df.loc[:, 'Data Req.'] = abastecimento_df['Data Req.'].dt.strftime('%d/%m/%Y')
#Mescl tbl'abastecimento_df'c/tbl'veiculo_df'p/includ colun"PLACA/"
abastecimento_df = abastecimento_df.merge(veiculo_df[['Placa TOPCON', 'PLACA/']], left_on='Veículo/Equip.', right_on='Placa TOPCON', how='left')
#Reorgnze order-coluns
colunas_ordem = ["Requisição", "Data Req.", "Requisitante", "PLACA/", "Diferença de Km", "Km por Litro", "Combustível Restante", "Vlr. Total", "Km Atual", "Km Rodados", "Horim por Litro", "Horim. Equip.", "Litros Anterior", "Litros", "Diferença de Horim", "Veículo/Equip.", "Obs."]
abastecimento_df = abastecimento_df[colunas_ordem]
#Ajust type of data p/compatibility c/Arrow
abastecimento_df['Obs.'] = abastecimento_df['Obs.'].astype(str)
#Config->aplic Streamlit
st.title('Análise de Desempenho dos Veículos')
st.sidebar.header('Filtrar os Dados')
#Entrad->user p/filtrag
veiculo = st.sidebar.text_input('Veículo/Equip.')
data_inicial = st.sidebar.date_input('Data inicial', pd.to_datetime('2024-01-01'))
data_final = st.sidebar.date_input('Data final', pd.Timestamp.now())
percentagem = st.sidebar.selectbox('Percentagem', [10, 20, 30, 50])
#Filtr dados BY veículo|interval dDATAS
filtro = abastecimento_df[(abastecimento_df['Veículo/Equip.'].str.contains(veiculo, case=False, na=False)) &
                          (pd.to_datetime(abastecimento_df['Data Req.'], format='%d/%m/%Y') >= pd.to_datetime(data_inicial)) &
                          (pd.to_datetime(abastecimento_df['Data Req.'], format='%d/%m/%Y') <= pd.to_datetime(data_final))]
#Calc média Km/Litro p/veículo
media_km_litro = filtro['Km por Litro'].mean()
#Filtr abasteciments UNDER the'%'expected
limite = media_km_litro * (1 - percentagem / 100)
filtro_desempenho = filtro[filtro['Km por Litro'] < limite]
#SHOW dados filtrads
st.write(f"Abastecimentos com Km por Litro abaixo de {percentagem}% da média ({media_km_litro:.2f} Km por Litro):")
st.write(filtro_desempenho)
#Gráfic-desempenho
fig = px.bar(filtro_desempenho, x='Data Req.', y='Km por Litro', color='Km por Litro', hover_data=['Requisitante', 'Requisição', 'Veículo/Equip.'])
fig.update_layout(title=f"Desempenho dos Abastecimentos de {veiculo} abaixo de {percentagem}% da média", xaxis_title="Data Req.", yaxis_title="Km por Litro", xaxis_tickangle=-45)
#Plotar gráfc
st.plotly_chart(fig)
#Button p/export filtrd data t/Excel
if st.button('Exportar Dados Filtrados para Excel', key='export_button'):
    with pd.ExcelWriter('app/Arquivos_Armazenados/dados_desempenho.xlsx', engine='openpyxl') as writer:
        filtro_desempenho.to_excel(writer, index=False, sheet_name='Dados de Desempenho')
    st.write('Dados exportados para Excel com sucesso!')
    #Link p/ download-arqv Excel
    with open('app/Arquivos_Armazenados/dados_desempenho.xlsx', 'rb') as f:
        st.download_button('Baixar Dados de Desempenho', f, file_name='dados_desempenho.xlsx', key='download_button')