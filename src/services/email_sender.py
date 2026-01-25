import smtplib
import os
from datetime import datetime
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

# async def send_reset_password_email_notification(user_email: str):
#     fromaddr = "alekseyelcha07@mail.ru"
#     toaddr = f"{user_email}"
#     passw = os.getenv("MAIL_SERVICE_SECRET")
#
#     msg = MIMEMultipart()
#     msg['From'] = fromaddr
#     msg['To'] = toaddr
#     msg['Subject'] = "LinkShortener // Ваш пароль был обновлён"
#
#     # HTML шаблон письма
#     html_content = f"""
#     <!DOCTYPE html>
#     <html lang="ru">
#     <head>
#         <meta charset="UTF-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#         <title>Уведомление об обновлении пароля</title>
#         <style>
#             * {{
#                 margin: 0;
#                 padding: 0;
#                 box-sizing: border-box;
#             }}
#
#             body {{
#                 font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
#                 line-height: 1.6;
#                 color: #333;
#                 background-color: #f5f7fa;
#                 padding: 20px;
#             }}
#
#             .email-container {{
#                 max-width: 600px;
#                 margin: 0 auto;
#                 background-color: #ffffff;
#                 border-radius: 12px;
#                 overflow: hidden;
#                 box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
#             }}
#
#             .email-header {{
#                 background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#                 padding: 30px 40px;
#                 text-align: center;
#                 color: white;
#             }}
#
#             .email-logo {{
#                 font-size: 28px;
#                 font-weight: bold;
#                 margin-bottom: 10px;
#                 letter-spacing: 0.5px;
#             }}
#
#             .email-title {{
#                 font-size: 22px;
#                 font-weight: 600;
#                 margin-bottom: 5px;
#             }}
#
#             .email-subtitle {{
#                 font-size: 16px;
#                 opacity: 0.9;
#             }}
#
#             .email-content {{
#                 padding: 40px;
#             }}
#
#             .alert-box {{
#                 background-color: #fff8e1;
#                 border-left: 4px solid #ffc107;
#                 padding: 16px 20px;
#                 margin-bottom: 25px;
#                 border-radius: 4px;
#             }}
#
#             .alert-title {{
#                 font-weight: 600;
#                 color: #ff9800;
#                 margin-bottom: 8px;
#                 display: flex;
#                 align-items: center;
#                 gap: 8px;
#             }}
#
#             .info-box {{
#                 background-color: #e8f5e9;
#                 border-left: 4px solid #4caf50;
#                 padding: 16px 20px;
#                 margin: 25px 0;
#                 border-radius: 4px;
#             }}
#
#             .info-title {{
#                 font-weight: 600;
#                 color: #2e7d32;
#                 margin-bottom: 8px;
#                 display: flex;
#                 align-items: center;
#                 gap: 8px;
#             }}
#
#             .user-email {{
#                 font-weight: bold;
#                 color: #667eea;
#                 background-color: #f0f4ff;
#                 padding: 4px 8px;
#                 border-radius: 4px;
#                 display: inline-block;
#                 margin: 5px 0;
#             }}
#
#             .action-box {{
#                 background-color: #e3f2fd;
#                 border-radius: 8px;
#                 padding: 25px;
#                 text-align: center;
#                 margin: 30px 0;
#                 border: 1px solid #bbdefb;
#             }}
#
#             .action-button {{
#                 display: inline-block;
#                 background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#                 color: white;
#                 text-decoration: none;
#                 padding: 14px 32px;
#                 border-radius: 50px;
#                 font-weight: 600;
#                 font-size: 16px;
#                 margin: 15px 0;
#                 transition: all 0.3s ease;
#                 box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
#             }}
#
#             .action-button:hover {{
#                 transform: translateY(-2px);
#                 box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
#             }}
#
#             .steps-list {{
#                 margin: 20px 0 20px 20px;
#             }}
#
#             .steps-list li {{
#                 margin-bottom: 12px;
#                 padding-left: 5px;
#             }}
#
#             .contact-info {{
#                 margin-top: 30px;
#                 padding-top: 20px;
#                 border-top: 1px solid #e0e0e0;
#                 font-size: 14px;
#                 color: #666;
#                 text-align: center;
#             }}
#
#             .footer {{
#                 background-color: #f8f9fa;
#                 padding: 20px 40px;
#                 text-align: center;
#                 color: #666;
#                 font-size: 14px;
#                 border-top: 1px solid #e0e0e0;
#             }}
#
#             .footer a {{
#                 color: #667eea;
#                 text-decoration: none;
#             }}
#
#             .icon {{
#                 font-size: 18px;
#             }}
#
#             @media only screen and (max-width: 600px) {{
#                 .email-content {{
#                     padding: 20px;
#                 }}
#
#                 .email-header {{
#                     padding: 20px;
#                 }}
#
#                 .action-button {{
#                     padding: 12px 24px;
#                     width: 100%;
#                 }}
#             }}
#         </style>
#     </head>
#     <body>
#         <div class="email-container">
#             <div class="email-header">
#                 <div class="email-logo">🔗 LinkShortener</div>
#                 <h1 class="email-title">Уведомление об обновлении пароля</h1>
#                 <p class="email-subtitle">Ваша безопасность — наш приоритет</p>
#             </div>
#
#             <div class="email-content">
#                 <div class="alert-box">
#                     <div class="alert-title">
#                         <span class="icon">⚠️</span> Внимание!
#                     </div>
#                     <p>Пароль от вашего аккаунта был успешно обновлён.</p>
#                 </div>
#
#                 <p>Здравствуйте!</p>
#                 <p>Мы обнаружили, что пароль для вашего аккаунта <span class="user-email">{user_email}</span> был изменён.</p>
#
#                 <div class="info-box">
#                     <div class="info-title">
#                         <span> Что произошло?</span>
#                     </div>
#                     <p>Система зафиксировала успешное обновление пароля для вашего аккаунта.</p>
#                 </div>
#
#                 <div class="action-box">
#                     <h3 style="margin-bottom: 15px; color: #333;">Если это были не вы:</h3>
#                     <p style="margin-bottom: 20px;">Немедленно восстановите доступ к аккаунту:</p>
#
#                     <a href="http://localhost:8000/" class="action-button">Восстановить доступ</a>
#
#                     <div style="margin-top: 20px; text-align: left;">
#                         <p style="font-weight: 600; margin-bottom: 10px;">Следуйте этим шагам:</p>
#                         <ol class="steps-list">
#                             <li>Перейдите на главную страницу сервиса</li>
#                             <li>Нажмите на кнопку «Войти» в правом верхнем углу</li>
#                             <li>Выберите «Не помню пароль»</li>
#                             <li>Следуйте инструкциям для восстановления доступа</li>
#                         </ol>
#                     </div>
#                 </div>
#
#                 <div class="contact-info">
#                     <p>Если у вас возникли проблемы или вопросы, пожалуйста, обратитесь в нашу службу поддержки.</p>
#                 </div>
#             </div>
#
#             <div class="footer">
#                 <p>© {datetime.now().year} LinkShortener. Все права защищены.</p>
#                 <p>Это письмо отправлено автоматически. Пожалуйста, не отвечайте на него.</p>
#                 <p>Если вы не запрашивали смену пароля, проигнорируйте это сообщение или <a href="mailto:alekseyelcha07@mail.ru">сообщите в поддержку</a>.</p>
#             </div>
#         </div>
#     </body>
#     </html>
#     """
#
#     # Альтернативная текстовая версия для почтовых клиентов, которые не поддерживают HTML
#     text_content = f"""Внимание! Ваш пароль от аккаунта {user_email} был успешно обновлён!
#
# Если это были не Вы, немедленно восстановите доступ:
# Перейдите на http://localhost:8000/, нажмите на кнопку «Войти» в правом верхнем углу и нажмите на «Не помню пароль»
# Далее, следуя инструкции, обновите пароль!
#
# В случае возникновения проблем обратитесь в поддержку, написав на этот email.
#
# ---
# © {datetime.now().year} LinkShortener
# """
#
#     # Создаем MIME-части для HTML и текстовой версии
#     part1 = MIMEText(text_content, 'plain', 'utf-8')
#     part2 = MIMEText(html_content, 'html', 'utf-8')
#
#     # Добавляем обе версии (почтовый клиент выберет подходящую)
#     msg.attach(part1)
#     msg.attach(part2)
#
#     try:
#         server = smtplib.SMTP_SSL('smtp.mail.ru', 465)
#         server.login(fromaddr, passw)
#         text = msg.as_string()
#         server.sendmail(fromaddr, toaddr, text)
#         print(f"Письмо успешно отправлено на {user_email}!")
#
#     except Exception as e:
#         print(f"Ошибка при отправке письма: {e}")
#         raise SendEmailError
#     finally:
#         if 'server' in locals():
#             server.quit()



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
