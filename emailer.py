import smtplib
from email.mime.text import MIMEText


def send_email(recv, miner):
    mail_host = 'smtp.163.com'
    mail_user = 'CaptainPoolAdmin'
    mail_pass = 'ZFFHKHKKMQNIZZDW'
    sender = 'CaptainPoolAdmin@163.com'
    message = MIMEText(f'Following Miner/s is/are offline: {miner}', 'plain', 'utf-8')
    message['Subject'] = 'Offline Alert!!!'
    message['From'] = sender
    retry = 3

    while retry:
        try:
            for r in recv:
                message['To'] = r
                smtpObj = smtplib.SMTP()
                smtpObj.connect(mail_host, 25)
                smtpObj.login(mail_user, mail_pass)
                smtpObj.sendmail(sender, r, message.as_string())
                smtpObj.quit()
                print(f'alert email sent to {recv}')

        except smtplib.SMTPException as e:
            print('error', e)
            retry -= 1
        raise ConnectionError('failed connecting to mail server')


if __name__ == "__main__":
    send_email(['timrainer@qq.com'], ['DualDragonROG0', 'DualDragonTUF0'])