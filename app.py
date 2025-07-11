from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os, json

app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'usuarios.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MODELOS
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)

class DadosUsuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    dados_json = db.Column(db.Text, nullable=True)
    usuario = db.relationship('Usuario', backref=db.backref('dados', lazy=True))

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    cliente = db.Column(db.String(100))
    ambiente = db.Column(db.String(100))
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    cidade = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    telefone = db.Column(db.String(50))
    descricao = db.Column(db.Text)
    data_compra = db.Column(db.String(20))
    data_entrega = db.Column(db.String(20))
    valor = db.Column(db.Float)
    desconto = db.Column(db.Float)
    pagamento = db.Column(db.String(20))
    parcelas = db.Column(db.Integer)
    taxa = db.Column(db.Float)

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nome = db.Column(db.String(100))
    cnpj = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.String(200))
    instagram = db.Column(db.String(100))
    facebook = db.Column(db.String(100))
    site = db.Column(db.String(100))
    usuario = db.relationship('Usuario', backref=db.backref('empresa', lazy=True))

class ParametrosCalculo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    margem_lucro = db.Column(db.Float)
    custo_fixo_percentual = db.Column(db.Float)
    taxa_maquininha = db.Column(db.Float)
    desconto_avista = db.Column(db.Float)
    usuario = db.relationship('Usuario', backref=db.backref('parametros', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

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

@app.route('/custos', methods=['GET', 'POST'])
@login_required
def custos():
    resultado = {}
    dados_salvos = DadosUsuario.query.filter_by(usuario_id=current_user.id).first()
    dados = {}

    if request.method == 'POST':
        campos = [
            'aluguel', 'agua', 'energia', 'internet/celular', 'salarios', 'contador',
            'marketing', 'Software', 'Combustivel', 'manutencao', 'seguros', 'outros',
            'vendas', 'materiais', 'maoDeObra', 'frete', 'design', 'valorVenda'
        ]

        dados = {campo: float(request.form.get(campo, 0) or 0) for campo in campos}

        fixos = campos[:12]
        vendas_mes = max(1, int(dados['vendas']))
        total_fixos = sum(dados[c] for c in fixos)
        fixo_por_venda = round(total_fixos / vendas_mes, 2)

        materiais = dados['materiais'] * 1.10
        custo_projeto = round(materiais + dados['maoDeObra'] + dados['frete'] + dados['design'] + fixo_por_venda, 2)
        lucro = round(dados['valorVenda'] - custo_projeto, 2)

        resultado = {
            'custos_fixos': f"{total_fixos:.2f}",
            'custo_fixo_por_venda': f"{fixo_por_venda:.2f}",
            'custo_projeto': f"{custo_projeto:.2f}",
            'lucro': f"{lucro:.2f}"
        }

        if not dados_salvos:
            dados_salvos = DadosUsuario(usuario_id=current_user.id)
            db.session.add(dados_salvos)
        dados_salvos.dados_json = json.dumps(dados)
        db.session.commit()
        flash("Dados salvos com sucesso!")

    elif dados_salvos:
        dados = json.loads(dados_salvos.dados_json)
        fixos = [
            'aluguel', 'agua', 'energia', 'internet/celular', 'salarios', 'contador',
            'marketing', 'Software', 'Combustivel', 'manutencao', 'seguros', 'outros'
        ]
        vendas_mes = max(1, int(dados.get('vendas', 1)))
        total_fixos = sum(float(dados.get(c, 0)) for c in fixos)
        fixo_por_venda = round(total_fixos / vendas_mes, 2)
        materiais = float(dados.get('materiais', 0)) * 1.10
        mao = float(dados.get('maoDeObra', 0))
        frete = float(dados.get('frete', 0))
        venda = float(dados.get('valorVenda', 0))
        design = float(dados.get('design', 0))  # pegar o valor do design
        custo_projeto = round(materiais + mao + frete + design + fixo_por_venda, 2)
        lucro = round(venda - custo_projeto, 2)

        resultado = {
            'custos_fixos': f"{total_fixos:.2f}",
            'custo_fixo_por_venda': f"{fixo_por_venda:.2f}",
            'custo_projeto': f"{custo_projeto:.2f}",
            'lucro': f"{lucro:.2f}"
        }

    return render_template('custos.html', resultado=resultado, dados=dados)

@app.route('/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    cliente_id = request.args.get('editar')
    cliente_para_editar = None

    if request.method == 'POST':
        id_form = request.form.get('id')
        if id_form:
            cliente_existente = Cliente.query.filter_by(id=id_form, usuario_id=current_user.id).first()
            if cliente_existente:
                cliente_existente.cliente = request.form.get('cliente', '')
                cliente_existente.ambiente = request.form.get('ambiente', '')
                cliente_existente.endereco = request.form.get('endereco', '')
                cliente_existente.numero = request.form.get('numero', '')
                cliente_existente.cidade = request.form.get('cidade', '')
                cliente_existente.bairro = request.form.get('bairro', '')
                cliente_existente.telefone = request.form.get('telefone', '')
                cliente_existente.descricao = request.form.get('descricao', '')
                cliente_existente.data_compra = request.form.get('data_compra', '')
                cliente_existente.data_entrega = request.form.get('data_entrega', '')
                cliente_existente.valor = float(request.form.get('valor', 0))
                cliente_existente.desconto = float(request.form.get('desconto', 0))
                cliente_existente.pagamento = request.form.get('pagamento', '')
                cliente_existente.parcelas = int(request.form.get('parcelas', 1))
                cliente_existente.taxa = float(request.form.get('taxa', 0))
                db.session.commit()
                flash("Cliente atualizado com sucesso!")
        else:
            novo = Cliente(
                usuario_id=current_user.id,
                cliente=request.form.get('cliente', ''),
                ambiente=request.form.get('ambiente', ''),
                endereco=request.form.get('endereco', ''),
                numero=request.form.get('numero', ''),
                cidade=request.form.get('cidade', ''),
                bairro=request.form.get('bairro', ''),
                telefone=request.form.get('telefone', ''),
                descricao=request.form.get('descricao', ''),
                data_compra=request.form.get('data_compra', ''),
                data_entrega=request.form.get('data_entrega', ''),
                valor=float(request.form.get('valor', 0)),
                desconto=float(request.form.get('desconto', 0)),
                pagamento=request.form.get('pagamento', ''),
                parcelas=int(request.form.get('parcelas', 1)),
                taxa=float(request.form.get('taxa', 0))
            )
            db.session.add(novo)
            db.session.commit()
            flash("Cliente salvo com sucesso!")
        return redirect(url_for('clientes'))

    if cliente_id:
        cliente_para_editar = Cliente.query.filter_by(id=cliente_id, usuario_id=current_user.id).first()

    lista = Cliente.query.filter_by(usuario_id=current_user.id).all()
    clientes_formatados = []
    for c in lista:
        desconto = c.desconto or 0
        valor_com_desconto = round(c.valor - (c.valor * desconto / 100), 2)
        clientes_formatados.append({
            'id': c.id,
            'cliente': c.cliente,
            'data_compra': c.data_compra,
            'data_entrega': c.data_entrega,
            'valor': c.valor,
            'desconto': desconto,
            'valor_com_desconto': valor_com_desconto,
            'ambiente': c.ambiente,
            'pagamento': c.pagamento,
            'parcelas': c.parcelas,
            'taxa': c.taxa,
            'cidade': c.cidade,
            'telefone': c.telefone,
            'descricao': c.descricao
        })
    parametros = ParametrosCalculo.query.filter_by(usuario_id=current_user.id).first()
    empresa = Empresa.query.filter_by(usuario_id=current_user.id).first()  # <--- ADICIONE AQUI
    # Calcular o custo fixo por venda novamente para passar pro template
    dados_salvos = DadosUsuario.query.filter_by(usuario_id=current_user.id).first()
    resultado = {}
    if dados_salvos:
        dados = json.loads(dados_salvos.dados_json)
        fixos = [
            'aluguel', 'agua', 'energia', 'internet/celular', 'salarios', 'contador',
            'marketing', 'Software', 'Combustivel', 'manutencao', 'seguros', 'outros'
        ]
        vendas_mes = max(1, int(dados.get('vendas', 1)))
        total_fixos = sum(float(dados.get(c, 0)) for c in fixos)
        fixo_por_venda = round(total_fixos / vendas_mes, 2)
        resultado['custo_fixo_por_venda'] = fixo_por_venda

    return render_template(
        'clientes.html',
        clientes=clientes_formatados,
        cliente_editar=cliente_para_editar.__dict__ if cliente_para_editar else None,
        parametros=parametros,
        resultado=resultado,
        empresa=empresa  # <<--- AQUI
    )

@app.route('/clientes/excluir', methods=['POST'])
@login_required
def excluir_cliente():
    id_cliente = request.form['id']
    cliente = Cliente.query.filter_by(id=id_cliente, usuario_id=current_user.id).first()
    if cliente:
        db.session.delete(cliente)
        db.session.commit()
        flash("Cliente excluído com sucesso!")
    return redirect(url_for('clientes'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    empresa = Empresa.query.filter_by(usuario_id=current_user.id).first()
    parametros = ParametrosCalculo.query.filter_by(usuario_id=current_user.id).first()

    def safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    if request.method == 'POST':
        if not empresa:
            empresa = Empresa(usuario_id=current_user.id)

        empresa.nome = request.form.get('nome_empresa')
        empresa.cnpj = request.form.get('cnpj')
        empresa.telefone = request.form.get('telefone')
        empresa.endereco = request.form.get('endereco')
        empresa.instagram = request.form.get('instagram')
        empresa.facebook = request.form.get('facebook')
        empresa.site = request.form.get('site')

        db.session.add(empresa)  # <- ESSA LINHA É A CHAVE

        if not parametros:
            parametros = ParametrosCalculo(usuario_id=current_user.id)
            db.session.add(parametros)
        parametros.margem_lucro = safe_float(request.form.get('margem_lucro'))
        parametros.custo_fixo_percentual = safe_float(request.form.get('custo_fixo'))
        parametros.taxa_maquininha = safe_float(request.form.get('taxa_maquininha'))
        parametros.desconto_avista = safe_float(request.form.get('desconto_avista'))

        db.session.commit()
        flash('Dados salvos com sucesso!')

    return render_template('home.html', empresa=empresa, parametros=parametros)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
