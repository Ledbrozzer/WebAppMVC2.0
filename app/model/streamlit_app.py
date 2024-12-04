import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
#Function t/READ arqv saved
@st.cache_data
def read_files():
    stored_folder = "app/Arquivos_Armazenados"
    veiculo_file_path = os.path.join(stored_folder, "veiculo_data.bin")
    abastecimento_file_path = os.path.join(stored_folder, "abastecimento_data.bin")
    #Verify-arqvs exist
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
#READ data arqv
veiculo_df, abastecimento_df = read_files()
#Verify if-DataFrames were loaded correctly
if veiculo_df is None or abastecimento_df is None:
    st.stop()
#Convrt colun'Data Req.'t/type datetime
abastecimento_df['Data Req.'] = pd.to_datetime(abastecimento_df['Data Req.'], errors='coerce', dayfirst=True)
#Exclud coluns undesird
columns_exclud = ["Combustível", "Vlr. Unitário", "Hora Abast.", "Abast. Externo"]
current_columns = [col for col in columns_exclud if col in abastecimento_df.columns]
if current_columns:
    abastecimento_df = abastecimento_df.drop(columns=current_columns)
#Order dataBY'Data Req.'form ascend
abastecimento_df = abastecimento_df.sort_values(by=['Data Req.'])
#Calc dif Km|Horim t/each Veículo/Equip.
abastecimento_df['Diferença de Km'] = abastecimento_df.groupby('Veículo/Equip.')['Km Atual'].diff().abs()
abastecimento_df['Diferença de Horim'] = abastecimento_df.groupby('Veículo/Equip.')['Horim. Equip.'].diff().abs()
#GET value Litrs abastecmnt anter t/each Veículo/Equip.
abastecimento_df['Litros Anterior'] = abastecimento_df.groupby('Veículo/Equip.')['Litros'].shift(1)
#Calc Km|Horim/Litr
abastecimento_df['Km por Litro'] = abastecimento_df['Diferença de Km'] / abastecimento_df['Litros Anterior']
abastecimento_df['Horim por Litro'] = abastecimento_df['Diferença de Horim'] / abastecimento_df['Litros Anterior']
#Arrednd values
abastecimento_df['Km por Litro'] = abastecimento_df['Km por Litro'].round(3)
abastecimento_df['Horim por Litro'] = abastecimento_df['Horim por Litro'].round(3)
#Calc Combustív Restnt
abastecimento_df['Combustível Restante'] = abastecimento_df['Diferença de Km'] % abastecimento_df['Litros Anterior']
abastecimento_df['Combustível Restante'] = abastecimento_df['Combustível Restante'].round(3)
#Reformat colun'Data Req.'t/exibt format desird usng .loc[]
abastecimento_df.loc[:, 'Data Req.'] = abastecimento_df['Data Req.'].dt.strftime('%d/%m/%Y')
#Mescl tb'abastecimento_df'c/ tb'veiculo_df't/includ colun"PLACA/"
abastecimento_df = abastecimento_df.merge(veiculo_df[['Placa TOPCON', 'PLACA/']], left_on='Veículo/Equip.', right_on='Placa TOPCON', how='left')
#Reorgnize ordem-coluns
colunas_ordem = ["Requisição", "Data Req.", "Requisitante", "PLACA/", "Diferença de Km", "Km por Litro", "Combustível Restante", "Vlr. Total", "Km Atual", "Km Rodados", "Horim por Litro", "Horim. Equip.", "Litros Anterior", "Litros", "Diferença de Horim", "Veículo/Equip.", "Obs."]
abastecimento_df = abastecimento_df[colunas_ordem]
#Ajust type data t/compatibility w/Arrow
abastecimento_df['Obs.'] = abastecimento_df['Obs.'].astype(str)
#Config-applictn Streamlit
st.title('Análise de Abastecimento')
st.sidebar.header('Filtrar os Dados')
#Entry user p/filtrgm
requisitante = st.sidebar.text_input('Requisitante', '')
veiculo = st.sidebar.text_input('Veículo', '')
data_inicial = st.sidebar.date_input('Data inicial', pd.to_datetime('2024-01-01'))
data_final = st.sidebar.date_input('Data final', pd.Timestamp.now())
km_litro_min = st.sidebar.number_input('Km por Litro (Mínimo)', value=0.0, step=0.1)
km_litro_max = st.sidebar.number_input('Km por Litro (Máximo)', value=100.0, step=0.1)
#Apply filtr t/data
filtro = abastecimento_df[(abastecimento_df['Requisitante'].str.contains(requisitante, case=False, na=False)) &
                          (abastecimento_df['Veículo/Equip.'].str.contains(veiculo, case=False, na=False)) &
                          (pd.to_datetime(abastecimento_df['Data Req.'], format='%d/%m/%Y') >= pd.to_datetime(data_inicial)) &
                          (pd.to_datetime(abastecimento_df['Data Req.'], format='%d/%m/%Y') <= pd.to_datetime(data_final)) &
                          (abastecimento_df['Km por Litro'] >= km_litro_min) &
                          (abastecimento_df['Km por Litro'] <= km_litro_max)]
#Order data filtrd'Data Req.'form ascend
filtro = filtro.sort_values(by=['Data Req.'])
#Show data filtrds
st.write("Dados Filtrados:")
st.write(filtro)
#Select analysis
analise = st.sidebar.selectbox(
    'Selecione a Análise',
    ('Análise 1: Diferença de Km(x)', 'Análise 2: Km por Litro(x)', 'Análise 3: Horim por Litro(x)', 'Análise 4: Km/Litro por Data', 'Análise 5: Performance Requisitante', 'Análise 6: Performance por Veículo', 'Análise 7: Km/Litro por Vlr Total', 'Análise 8: Top5|Bottom10 Km/Litro')
)
#Functn d'analysis
def analise1(filtro):
    fig = px.histogram(filtro, x='Diferença de Km', color='Diferença de Km', hover_data=['Veículo/Equip.'], title='Análise 1: Diferença de Km(x)')
    return fig
def analise2(filtro):
    fig = px.histogram(filtro, x='Km por Litro', color='Km por Litro', hover_data=['Veículo/Equip.', 'Data Req.'], title='Análise 2: Km por Litro(x)')
    return fig
def analise3(filtro):
    fig = px.histogram(filtro, x='Horim por Litro', color='Horim por Litro', hover_data=['Veículo/Equip.', 'Data Req.'], title='Análise 3: Horim por Litro(x)')
    return fig
def analise4(filtro):
    fig = px.histogram(filtro, x='Data Req.', y='Km por Litro', color='Km por Litro', hover_data=['Veículo/Equip.'], title='Análise 4: Km/Litro por Data')
    return fig
def analise5(filtro):
    fig = px.histogram(filtro, x='Km por Litro', y='Requisitante', color='Requisitante', hover_data=['Data Req.'], title='Análise 5: Performance Requisitante')
    return fig
def analise6(filtro):
    fig = px.histogram(filtro, x='Km por Litro', y='Veículo/Equip.', color='Data Req.', hover_data=['Km por Litro'], title='Análise 6: Performance por Veículo')
    return fig
def analise7(filtro):
    fig = px.histogram(filtro, x='Vlr. Total', y='Km por Litro', color='Vlr. Total', hover_data=['Veículo/Equip.'], title='Análise 7: Km/Litro por Vlr Total')
    return fig
def analise8(filtro):
    agrupado = filtro.groupby(['Veículo/Equip.', 'Requisitante']).agg({
        'Data Req.': 'max',
        'PLACA/': 'first',
        'Km por Litro': 'mean',
        'Km Atual': 'max'
    }).reset_index()
    #Select Top5|Bottom10
    top5 = agrupado.nlargest(5, 'Km por Litro')
    bottom10 = agrupado.nsmallest(10, 'Km por Litro')
    #Grafc Top5
    fig_top5 = px.bar(top5, x='Veículo/Equip.', y='Km por Litro', color='Km por Litro', hover_data=['Requisitante', 'Data Req.'])
    fig_top5.update_layout(title="Veículos/Equipamentos com MAIOR Km por Litro", xaxis_title="Veículo/Equip.", yaxis_title="Km por Litro", xaxis_tickangle=-45)
    #Grafc Bottom10
    fig_bottom10 = px.bar(bottom10, x='Veículo/Equip.', y='Km por Litro', color='Km por Litro', hover_data=['Requisitante', 'Data Req.'])
    fig_bottom10.update_layout(title="Veículos/Equipamentos com MENOR Km por Litro", xaxis_title="Veículo/Equip.", yaxis_title="Km por Litro", xaxis_tickangle=-45)
    return fig_top5, fig_bottom10
#Init var'fig't/Avoid'NameError'
fig = None
#Show grafc select
if analise == 'Análise 1: Diferença de Km(x)':
    fig = analise1(filtro)
elif analise == 'Análise 2: Km por Litro(x)':
    fig = analise2(filtro)
elif analise == 'Análise 3: Horim por Litro(x)':
    fig = analise3(filtro)
elif analise == 'Análise 4: Km/Litro por Data':
    fig = analise4(filtro)
elif analise == 'Análise 5: Performance Requisitante':
    fig = analise5(filtro)
elif analise == 'Análise 6: Performance por Veículo':
    fig = analise6(filtro)
elif analise == 'Análise 7: Km/Litro por Vlr Total':
    fig = analise7(filtro)
elif analise == 'Análise 8: Top5|Bottom10 Km/Litro':
    fig_top5, fig_bottom10 = analise8(filtro)
    st.plotly_chart(fig_top5)
    st.plotly_chart(fig_bottom10)
#Plot grafc
if fig:
    st.plotly_chart(fig)
#Buttn t/export data filtrd t/Excel
if st.button('Exportar Dados Filtrados para Excel', key='export_button'):
    with pd.ExcelWriter('app/Arquivos_Armazenados/dados_filtrados.xlsx', engine='openpyxl') as writer:
        filtro.to_excel(writer, index=False, sheet_name='Dados Filtrados')
    st.write('Dados exportados para Excel com sucesso!')
    #Link download arqv Excel
    with open('app/Arquivos_Armazenados/dados_filtrados.xlsx', 'rb') as f:
        st.download_button('Baixar Dados Filtrados', f, file_name='dados_filtrados.xlsx', key='download_button')