import imaplib

email = 'ksenobit16bit@yandex.ru'
password = 'harlaaqhkqaaaasy'

mail = imaplib.IMAP4_SSL('imap.yandex.ru')
mail.login(email,password)
mail.list()
mail.select("&BB8EPgQ0BD8EOARBBEwEOgQ4-|&BC8EPQQ0BDUEOgRB-|taxi")

result, data = mail.search(None, '(FROM "yandex.*")')

ids = data[0]
id_list = ids.split()
latest_email_id = id_list[-1]

result, data = mail.fetch(latest_email_id, "(RFC822)")
raw_email = data[0][1]
raw_email_string = raw_email.decode('utf-8')