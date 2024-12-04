from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__, static_url_path='/static', static_folder='../view')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form['usuario']
    senha = request.form['senha']
    #Credenciais-exemplo
    users = {"Jose Mario": "1234", "Saulo": "5678", "Gesse": "9123"}

    if usuario in users and users[usuario] == senha:
        return redirect(url_for('app_page'))
    else:
        return 'Credenciais inválidas!'

@app.route('/app')
def app_page():
    return render_template('App.html')

if __name__ == '__main__':
    app.run(debug=True)