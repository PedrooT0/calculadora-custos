from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])

def custos():
    resultado = {}

    if request.method == 'POST':
        campos_fixos = [
            'aluguel', 'agua', 'energia', 'internet/celular', 'salarios', 'contador',
            'marketing', 'Software', 'Combustivel', 'manutencao', 'seguros', 'outros'
        ]
        custos_fixos = sum(float(request.form.get(campo, 0) or 0) for campo in campos_fixos)

        vendas_mes = int(request.form.get('vendas', 1))
        custo_fixo_por_venda = round(custos_fixos / vendas_mes, 2)

        # Cálculo automático
        custos_variaveis = round(custo_fixo_por_venda * 0.3, 2)
        margem_lucro = round((custo_fixo_por_venda + custos_variaveis) * 0.2, 2)

        resultado = {
            'custos_fixos': custos_fixos,
            'custo_fixo_por_venda': custo_fixo_por_venda,
            'custos_variaveis': custos_variaveis,
            'margem_lucro': margem_lucro
        }

    return render_template('custos.html', resultado=resultado)


if __name__ == '__main__':
    app.run(debug=True)

