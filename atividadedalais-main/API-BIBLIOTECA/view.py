import os.path

from flask import jsonify, request, Response, send_from_directory
from main import app, con
from flask_bcrypt import generate_password_hash, check_password_hash
from fpdf import FPDF
import os
import pygal

import threading #view

if not os.path.exists(app.config['UPLOUD_FOLDER']):
    os.makedirs(app.config['UPLOUD_FOLDER'])




@app.route('/livro', methods=['GET'])
def livro():
    try:
        cur = con.cursor()
        cur.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livro")
        livros = cur.fetchall()

        livros_list = []

        for livro in livros:
            livros_list.append({
                'id_livro': livro[0],
                'titulo': livro[1],
                'autor': livro[2],
                'ano_publicacao': livro[3]
            })

        return jsonify(
            mensagem='Lista de Livros',
            livros=livros_list
        ), 200

    except Exception as e:
        return jsonify(
            mensagem=f'Erro ao acessar o banco de dados: {e}'
        ), 500
    finally:
        cur.close()


@app.route('/livro', methods=['POST'])
def criar_livro():
    try:

        data = request.get_json()

        titulo = data.get('titulo')
        autor = data.get('autor')
        ano_publicacao = data.get('ano_publicacao')
        imagem = request.files.get("imagem")

        if not all([titulo, autor, ano_publicacao]):
            return jsonify({'erro': 'Todos os campos são obrigatórios'}), 400

        cur = con.cursor()

        cur.execute('SELECT 1 FROM livro WHERE titulo = ?', (titulo,))
        if cur.fetchone():
            return jsonify({'erro': 'Livro já cadastrado'}), 400

        cur.execute("""INSERT INTO livro (titulo, autor, ano_publicacao) 
                    VALUES (?, ?, ?)RETURNIG ID_LIVRO""", (titulo, autor, ano_publicacao))

        codigo_livro =cur.fetchone()[0]
        con.commit()
        caminho_imagem =None

        if imagem:
            nome_imagem = f"{codigo_livro}.jpeg"
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "livros")
            os.makedirs(caminho_imagem_destino, exit_ok=True)
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)
            imagem.save(caminho_imagem)




        cur.execute("SELECT id_livro FROM livro WHERE titulo = ?", (titulo,))
        livro_id = cur.fetchone()[0]

        return jsonify({
            'mensagem': "Livro cadastrado com sucesso",
            'livro': {
                'id_livro': livro_id,
                'titulo': titulo,
                'autor': autor,
                'ano_publicacao': ano_publicacao
            }
        }), 201

    except Exception as e:
        con.rollback()
        return jsonify({
            'mensagem': f'Erro ao cadastrar livro: {e}'
        }), 500
    finally:
        if 'cur' in locals():
            cur.close()


@app.route('/edit_livros/<int:id>', methods=['PUT'])
def editar_livros(id):
    cur = con.cursor()

    cur.execute("""
        SELECT id_livro, titulo, autor, ano_publicacao
        FROM livro 
        WHERE id_livro = ?
    """, (id,))

    tem_livro = cur.fetchone()

    if not tem_livro:
        cur.close()
        return jsonify({"error": "Livro não encontrado"}), 404

    data = request.get_json()
    titulo = data.get('titulo')
    autor = data.get('autor')
    ano_publicacao = data.get('ano_publicacao')

    cur.execute("""
        UPDATE livro 
        SET titulo = ?, autor = ?, ano_publicacao = ?
        WHERE id_livro = ?
    """, (titulo, autor, ano_publicacao, id))

    con.commit()
    cur.close()

    return jsonify({
        "mensagem": "Livro atualizado com sucesso",
        "livro": {
            'id_livro': id,
            'titulo': titulo,
            'autor': autor,
            'ano_publicacao': ano_publicacao
        }
    })

@app.route('/deletar_livros/<int:id>', methods=['DELETE'])
def deletar_livros(id):
    cur = con.cursor()
    cur.execute("select 1 from livro where id_livro = ?", (id,))
    if not cur.fetchone():
        cur.close()
        return jsonify({"erro": "livro não encontrado"}), 404
    cur.execute("delete from livro where id_livro = ?", (id,))
    con.commit()
    cur.close()
    return jsonify(
        {"mensage": "livro excluido com sucesso", 'id_livro': id}
    )


# CREATE
@app.route('/usuario', methods=['POST'])
def criar_usuario():
    cur = con.cursor()


    dados = request.get_json()
    cur = con.cursor()

    senha = dados.get('senha')

    senha_hash = generate_password_hash(senha)

    cur.execute("INSERT INTO usuario (nome, usuario, senha) VALUES (?, ?, ?)",
                (dados['nome'], dados['usuario'], dados['senha']))
    cur.execute("""
        INSERT INTO usuarios (usuarios, senha)
        VALUES (?, ?)
    """, (criar_usuario, senha_hash))

    con.commit()



@app.route('/login', methods=['POST'])
def login():
    cur = None
    try:
        data = request.get_json()


        if not data:
            return jsonify({'erro': 'JSON inválido'}), 400

        usuario = data.get('usuario')
        senha = data.get('senha')

        if not usuario or not senha:
            return jsonify({'erro': 'Todos os campos são obrigatórios'}), 400

        cur = con.cursor()

        cur.execute("SELECT senha FROM usuario WHERE usuario = ?", (usuario,))
        resultado = cur.fetchone()

        # Verifica se o usuário existe
        if not resultado:
            return jsonify({'mensagem': 'Usuário ou senha inválidos'}), 401

        senha_hash = resultado[0]

        def senha_forte(senha):
            if not senha:
                return False

            maiusculo = minuscula = numero = caracterEspecial = False

            for s in senha:
                if s.isupper():
                    maiusculo = True
                elif s.islower():
                    minuscula = True
                elif s.isdigit():
                    numero = True
                elif not s.isalnum():
                    caracterEspecial = True

            if len(senha) >= 8 and maiusculo and minuscula and numero and caracterEspecial:
                return True
            else:
                return False

        # Verifica a senha com bcrypt
        if not check_password_hash(senha_hash, senha):
            return jsonify({'mensagem': 'Usuário ou senha inválidos'}), 401

        return jsonify({'mensagem': 'Login realizado com sucesso'}), 200

    except Exception as e:
        return jsonify({'erro': f'Erro no login: {e}'}), 500

    finally:
        if cur:
            cur.close()


# READ
@app.route('/usuario', methods=['GET'])
def listar_usuarios():
    cur = con.cursor()

    cur.execute("SELECT * FROM usuario")
    usuarios = cur.fetchall()

    con.close()
    return jsonify(usuarios)


# UPDATE
@app.route('/usuario/<int:id>', methods=['PUT'])
def atualizar_usuario(id):
    dados = request.json
    cur = con.cursor()

    cur.execute("""
        UPDATE usuario
        SET nome = ?, usuario = ?, senha = ?
        WHERE id = ?
    """, (dados['nome'], dados['usuario'], dados['senha'], id))

    con.commit()
    con.close()
    return {"mensagem": "Usuário atualizado"}


# DELETE
@app.route('/usuario/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    cur = con.cursor()

    cur.execute("DELETE FROM usuario WHERE id = ?", (id,))
    con.commit()
    con.close()

    return {"mensagem": "Usuário deletado"}



@app.route('/pdf_usuarios')
def pdf_usuarios():
    cur = con.cursor()
    return gerar_pdf_usuarios(cur)


from fpdf import FPDF

def gerar_pdf_usuarios(cur):
    pdf = FPDF()
    pdf.add_page()

    # Título
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Relatorio de Usuarios", 0, 1, "C")
    pdf.ln(5)

    # Cabeçalho
    pdf.set_font("Arial", "B", 12)
    pdf.cell(30, 10, "ID_usuario", 1)
    pdf.cell(60, 10, "Usuario", 1)
    pdf.cell(100, 10, "Senha", 1)
    pdf.ln()

    # Buscar dados do banco
    cur.execute("SELECT id_usuario, usuarios, senha FROM usuarios")
    dados = cur.fetchall()

    # Conteúdo
    pdf.set_font("Arial", "", 11)

    for user in dados:
        id_usuario = str(user[0])
        nome_usuario = str(user[1])
        senha = str(user[2])

        senha_curta = senha[:20] + "..."

        pdf.cell(30, 10, id_usuario, 1)
        pdf.cell(60, 10, nome_usuario, 1)
        pdf.cell(100, 10, senha_curta, 1)
        pdf.ln()

    # IMPORTANTE: corrigir encoding
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return pdf_bytes


@app.route('/grafico')
def grafico():
    cur = con.cursor()
    cur.execute("""SELECT ano_publicacao. count(*)
                from livros
                group by ano_publicacao
                order by ano_publicacao
    """)
    resultado = cur.fetchall()
    cur.close()



    grafico = pygal.Bar()
    grafico.title = 'Quantidade de Livros por ano'

    for g in resultado:
        grafico.add(str(g[0]), (g[1])
    return Response(grafico.render(), mimetype='image/svg+xml')


@app.route('enviar_email', methods=['POST'])
def enviar_email():
    dados = request.json
    assunto = dados.get('Subject')
    mensagem = dados.get('From')
    destinatario = dados.get('To')

    thread = threading.Thread(target=enviar_email, args=(assunto, mensagem, destinatario,))

    thread.start()

    return jsonify({'mensagem': 'Email enviado com sucesso'})