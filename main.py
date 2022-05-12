import imaplib
import base64

email = 'ksenobit16bit@yandex.ru'
password = 'harlaaqhkqaaaasy'

mail = imaplib.IMAP4_SSL('imap.yandex.ru')
mail.login(email,password)
mail.list()
mail.select("&BB8EPgQ0BD8EOARBBEwEOgQ4-|&BC8EPQQ0BDUEOgRB-|taxi")

result, data = mail.search(None, '(FROM "no-reply@taxi.yandex.ru")')

ids = data[0]
id_list = ids.split()
latest_email_id = id_list[-1]

result, data = mail.fetch(latest_email_id, "(RFC822)")
raw_email = data[0][1]
raw_email_string = raw_email.decode('utf-8')
print (raw_email_string)
#decoded_mail = base64.b64decode(raw_email_string.encode("utf-8")).decode("utf-8")
#print (decoded_mail)