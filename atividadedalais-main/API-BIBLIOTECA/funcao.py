import smtplib
from email.mime.text import MIMEText

from main import user


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


    def enviando_email(destinatario, assunto, mensagem):
        user = 'gabrielbelinelo9@gmail.com'
        senha = 'AINDA NÃO FIZ ISSO'

        msg = (MIMEText(mensagem))
        msg['From'] = user
        msg['To'] = destinatario
        msg['Subject'] = 'Assunto'

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, senha)
        server.send_mensagem(msg)
        server.quit()

