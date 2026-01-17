import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.exeptions import SendEmailError

async def send_reset_password_email(user_email: str, reset_link: str):
    fromaddr = "alekseyelcha07@mail.ru"
    toaddr = f"{user_email}"
    passw = os.getenv("MAIL_SERVICE_SECRET")

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "LinkShortener // Ссылка для сброса пароля"

    html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Сброс пароля</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f4;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    background-color: #9dceff;
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 300;
                }}
                .content {{
                    position: relative;
                    padding: 30px;
                    font-size: 16px;
                }}
                .reset-button {{
                    position: relative;
                    display: block;
                    width: 250px;
                    margin: 30px auto;
                    padding: 15px 30px;
                    background-color: f8f9fa;
                    color: white;
                    text-decoration: none;
                    border-radius: 50px;
                    font-size: 18px;
                    font-weight: bold;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                    transition: transform 0.3s, box-shadow 0.3s;
                }}
                .reset-button:hover {{
                    position: relative;
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
                }}
                .link-text {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 4px solid #667eea;
                    margin: 20px 0;
                    font-size: 14px;
                    word-break: break-all;
                    color: #666;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 14px;
                    color: #666;
                    border-top: 1px solid #eee;
                }}
                .warning {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-size: 14px;
                }}
                .highlight {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #2d3436;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Сброс пароля</h1>
                </div>

                <div class="content">
                    <p class="highlight">Здравствуйте!</p>

                    <p>Вы получили это письмо, потому что запросили сброс пароля для вашей учетной записи в <strong>LinkShortener</strong>.</p>

                    <p>Для сброса пароля нажмите на кнопку ниже:</p>

                    <a href="{reset_link}" class="reset-button">Сбросить пароль</a>

                    <p>Или скопируйте и вставьте следующую ссылку в браузер:</p>

                    <div class="link-text">
                        {reset_link}
                    </div>

                    <div class="warning">
                        ⚠️ <strong>Внимание:</strong> Ссылка действительна в течение 1 часа.
                        Если вы не запрашивали сброс пароля, проигнорируйте это письмо.
                    </div>

                    <p>Если у вас возникли проблемы, пожалуйста, свяжитесь с нашей поддержкой - напишите нам на почту УРУРУ.</p>

                    <p>С уважением,<br>
                    <strong>Команда LinkShortener</strong></p>
                </div>
            </div>
        </body>
        </html>
        """

    body = (f"Ссылка для сброса пароля: {reset_link}"
            f"\n"
            f"Если Вы не запрашивали смену пароля, проигнорируйте это сообщение.")
    # msg.attach(MIMEText(body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL('smtp.mail.ru', 465)

        server.login(fromaddr, passw)

        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        print("Письмо успешно отправлено!")

    except Exception as e:
        raise SendEmailError


async def send_reset_password_email_notification(user_email: str):
    fromaddr = "alekseyelcha07@mail.ru"
    toaddr = f"{user_email}"
    passw = os.getenv("MAIL_SERVICE_SECRET")

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "LinkShortener // Ваш пароль был обновлён"

    body = (f"Внимание! Ваш пароль от аккаунта {user_email} был успешно обновлён!\n"
            f"\n"
        f"Если это были не Вы, немедленно восстановите доступ: "
    f"Перейдите на http://localhost:8000/, нажмите на кнопку «Войти» в правом верхнем углу и нажмите на «Не помню пароль»\n"
    f"Далее, следуя инструкции, обновите пароль!\n"
    f"\n"
    f"В случае возникновения проблем обратитесь в поддержку, написав на этот email.")
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL('smtp.mail.ru', 465)

        server.login(fromaddr, passw)

        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        print("Письмо успешно отправлено!")

    except Exception as e:
        raise SendEmailError


async def send_email_validation(user_email: str, validate_url: str):
    fromaddr = "alekseyelcha07@mail.ru"
    toaddr = f"{user_email}"
    passw = os.getenv("MAIL_SERVICE_SECRET")

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "LinkShortener // Подтвердите email для создания аккаунта"

    body = (f"Перейдите по ссылке: {validate_url} для завершения регистрации!")
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL('smtp.mail.ru', 465)

        server.login(fromaddr, passw)

        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        print("Письмо успешно отправлено!")

    except Exception as e:
        raise SendEmailError
