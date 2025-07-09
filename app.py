from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/custos', methods=['GET', 'POST'])
@login_required
def custos():
    resultado = {}
    if request.method == 'POST':
        campos_fixos = ['aluguel', 'agua', 'energia', 'internet/celular', 'salarios', 'contador',
                        'marketing', 'Software', 'Combustivel', 'manutencao', 'seguros', 'outros']
        custos_fixos = sum(float(request.form.get(campo, 0) or 0) for campo in campos_fixos)
        vendas_mes = int(request.form.get('vendas', 1))
        custo_fixo_por_venda = round(custos_fixos / vendas_mes, 2)
        custos_variaveis = round(custo_fixo_por_venda * 0.3, 2)
        margem_lucro = round((custo_fixo_por_venda + custos_variaveis) * 0.2, 2)
        resultado = {
            'custos_fixos': custos_fixos,
            'custo_fixo_por_venda': custo_fixo_por_venda,
            'custos_variaveis': custos_variaveis,
            'margem_lucro': margem_lucro
        }
    return render_template('custos.html', resultado=resultado)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            return redirect(url_for('custos'))
        flash('E-mail ou senha incorretos.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.')
            return redirect(url_for('register'))
        novo_usuario = Usuario(email=email, senha=generate_password_hash(senha))
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Cadastro realizado com sucesso!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

