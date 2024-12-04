import os
import atexit
import signal
import subprocess
from flask import Flask, render_template, request, jsonify, redirect, url_for

os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '0'  #Deactivate-autodebug
app = Flask(__name__, template_folder='../view', static_folder='../view')
#Global Vars t/armazen data from arqvs|their'names
veiculo_data = None
abastecimento_data = None
veiculo_filename = None
abastecimento_filename = None
streamlit_processes = []  #List t/armazen process fromStreamlit

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        users = {"Jose Mario": "1234", "Saulo": "5678", "Gesse": "9123"}

        if usuario in users and users[usuario] == senha:
            return redirect(url_for('app_page'))
        else:
            return 'Credenciais inválidas!'
    return render_template('index.html')

@app.route('/app', methods=['GET', 'POST'])
def app_page():
    return render_template('App.html')

@app.route('/process_files', methods=['POST'])
def process_files():
    if 'veiculoFile' not in request.files or 'abastecimentoFile' not in request.files:
        return jsonify({'error': 'Ambos os arquivos são necessários'})
    veiculo_file = request.files['veiculoFile']
    abastecimento_file = request.files['abastecimentoFile']

    global veiculo_data, abastecimento_data, veiculo_filename, abastecimento_filename
    veiculo_data = veiculo_file.read()
    abastecimento_data = abastecimento_file.read()
    veiculo_filename = veiculo_file.filename
    abastecimento_filename = abastecimento_file.filename

    stored_folder = "app/Arquivos_Armazenados"  #Update t/'app/Arquivos_Armazenados'
    os.makedirs(stored_folder, exist_ok=True)

    with open(os.path.join(stored_folder, "veiculo_data.bin"), "wb") as f:
        f.write(veiculo_data)
    with open(os.path.join(stored_folder, "abastecimento_data.bin"), "wb") as f:
        f.write(abastecimento_data)
    return jsonify({'result': 'Arquivos importados com sucesso', 'veiculo_filename': veiculo_filename, 'abastecimento_filename': abastecimento_filename})

@app.route('/main_consult', methods=['GET'])
def main_consult():
    return redirect("http://localhost:8501/main")

@app.route('/side_consult', methods=['GET'])
def side_consult():
    return redirect("http://localhost:8502")

@app.route('/start_streamlit')
def start_streamlit():
    stored_folder = "app/Arquivos_Armazenados"
    streamlit_control_path = os.path.join(stored_folder, "streamlit_control")
    with open(streamlit_control_path, "w") as f:
        f.write("control")
    streamlit_path = os.path.join(os.getcwd(), "app/model/streamlit_app.py")
    streamlit_side_path = os.path.join(os.getcwd(), "app/model/side_consult.py")
    
    if request.args.get('consult_type') == 'main':
        process = subprocess.Popen(["streamlit", "run", streamlit_path, "--server.port", "8501"])
    else:
        process = subprocess.Popen(["streamlit", "run", streamlit_side_path, "--server.port", "8502"])
    #Add process t/t-process list
    streamlit_processes.append(process)
    return "Streamlit iniciado. Por favor, acesse a análise na nova aba do navegador."

@app.route('/clean_and_shutdown', methods=['POST'])
def clean_and_shutdown():
    global streamlit_processes
    stored_folder = "app/Arquivos_Armazenados"
    #Clear t-armazen arqvs
    for filename in os.listdir(stored_folder):
        file_path = os.path.join(stored_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Erro ao deletar {file_path}: {e}")
    #Finish all process from Streamlit
    for process in streamlit_processes:
        process.terminate()
    streamlit_processes = []  #Clear t-process list
    shutdown_server()
    return "Aplicação fechada e arquivos limpos."

def shutdown_server():
    os.kill(os.getpid(), signal.SIGINT)
#Registr-funç dlimpeza no'atexit'
atexit.register(shutdown_server)

if __name__ == '__main__':
    app.run(debug=False, port=5001)