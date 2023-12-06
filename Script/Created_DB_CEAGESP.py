from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from cryptography.fernet import Fernet
import re
import json
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

try:
    
    # Função para ler a chave de criptografia de um arquivo
    def load_key(key_file):
        with open(key_file, 'rb') as file:
            return file.read()

    # Função para descriptografar as informações
    def decrypt_info(key, encrypted_info):
        f = Fernet(key)
        decrypted_info = f.decrypt(encrypted_info).decode()
        return decrypted_info

    # Carregue a chave de criptografia
    encryption_key = load_key('../Sending_Email/chave.txt')

    # Ler as informações criptografadas do arquivo
    with open('../Sending_Email/credenciais.txt', 'rb') as file:
        encrypted_email = file.readline().strip()
        encrypted_password = file.readline().strip()

    # Descriptografe as informações
    email_address = decrypt_info(encryption_key, encrypted_email)
    email_password = decrypt_info(encryption_key, encrypted_password)

    # Configurações do servidor SMTP do Gmail
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    
    # URL da página que você deseja fazer scraping
    url = 'https://ceagesp.gov.br/cotacoes'

    # Inicializa o driver do Chrome
    driver = webdriver.Chrome()

    # Acesse a página
    driver.get(url)
    driver.implicitly_wait(3)

    # Execute o código JavaScript para obter as datas disponíveis
    script = """
    return JSON.stringify(Grupos);
    """
    grupos_str = driver.execute_script(script)

    # Analisar a string JSON para obter o objeto Python
    grupos = json.loads(grupos_str)

    # Inicializar uma lista para armazenar as tuplas (grupo, última data)
    resultados = []

    # Iterar sobre os grupos e datas
    for grupo, datas in grupos.items():
        datas_formatadas = [re.sub(r'(\d{2})\/(\d{2})\/(\d{4})', r'\1/\2/\3', data) for data in datas]
        # Converter as datas formatadas para objetos de data
        datas_obj = [datetime.strptime(data, '%d/%m/%Y') for data in datas_formatadas]
        # Encontrar a última data
        ultima_data_grupo = max(datas_obj)

        # Converter a última data de volta para string se necessário
        ultima_data_grupo_str = ultima_data_grupo.strftime('%d/%m/%Y')

        # Adicionar a tupla (grupo, última data) à lista de resultados
        resultados.append((grupo, ultima_data_grupo_str))
        
    # --------------- tratamento data scrape --------------- #    
    # Contexto: Os dados são disponibilizados todas as seg, qua e sex, o scrape será rodado as ter, qui e seg, sendo que a seg pegará os dados da sexta anterior
    # data atual
    hoje = datetime.now()
    # Verifica se hoje é segunda-feira (weekday() retorna 0 para segunda-feira)
    if hoje.weekday() == 0:
        # Se hoje for segunda-feira, ajusta a data para a última sexta-feira
        data_scrape = hoje - timedelta(days=hoje.weekday() + 3)
    else:
        # Se não for segunda-feira, mantém a data como está (ontem)
        data_scrape = hoje - timedelta(days=1)
        
    # Formata a data como uma string
    data_scrape = data_scrape.strftime('%d/%m/%Y')
    # lista que vai receber os dados
    dados_tabela = []

    # lista que vai receber os erros
    erros = []
    for i in resultados:
        if i[1] == data_scrape:
            # Conectar ao banco de dados
            connection = sqlite3.connect("DB_PRECOS_CEAGESP.db")
            # cursor
            cursor = connection.cursor()
            # Criar uma tabela 
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cotacoes_atacado (
                    Data DATE,
                    Categoria text,
                    Produto text,
                    Classificação text,
                    Uni_Peso text,
                    Preco_Menor decimal(18,2),
                    Preco_Comun decimal(18,2),
                    Preco_Maior decimal(18,2),
                    Quilo text
                )
            """
            )
            # força a espera
            driver.implicitly_wait(3)
            # Reencontrar o elemento select antes de cada interação
            form_cot_grupo = driver.find_element(By.NAME, 'cot_grupo')
            select = Select(form_cot_grupo)
            select.select_by_value(i[0])
            # desativando o elemento 'readonly'
            driver.execute_script("document.getElementsByName('cot_data')[0].removeAttribute('readonly');")
            # seleciona o campo de data
            campo_data = driver.find_element(By.NAME, 'cot_data')
            # limpa o campo de data para receber a data nova
            campo_data.clear()
            # força a espera
            driver.implicitly_wait(3)
            # seta a data do scrape
            campo_data.send_keys(data_scrape)
            # executa a pesquisa
            driver.find_element(By.CLASS_NAME, 'd_block.btn.btn-success').click()
            # força a espera
            driver.implicitly_wait(3)
            # Localizar a tabela pelo nome da classe
            tabela = driver.find_element(By.CLASS_NAME, 'contacao_lista')
            # Iterar sobre as linhas da tabela
            linhas = tabela.find_elements(By.TAG_NAME, 'tr')[2:]

            for linha in linhas:
                celulas = linha.find_elements(By.TAG_NAME, 'td')
                dados_linha = [celula.text for celula in celulas]
                dados_linha.insert(0,data_scrape)
                dados_linha.insert(1, i[0])
                dados_tabela.append(dados_linha)
        else:
            erro = f"{i[0]}, Base não atualizada na data de hoje"
            erros.append(erro)
            print(erros)
            continue
        # Criar um DataFrame do pandas
        df = pd.DataFrame(dados_tabela, columns=['Data','Categoria', 'Produto', 'Classificação', 'Uni_Peso', 'Preco_Menor', 'Preco_Comun', 'Preco_Maior', 'Quilo'])
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df.to_sql('cotacoes_atacado', connection, index=False, if_exists='append')
        query_format_date = '''
        UPDATE cotacoes_atacado
        SET Data = strftime('%Y-%m-%d', Data)
        '''
        query_remove_duplicatas = '''
        DELETE FROM cotacoes_atacado
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM cotacoes_atacado
            GROUP BY Data, Categoria, Produto, Classificação, Uni_Peso,
                    Preco_Menor, Preco_Comun, Preco_Maior, Quilo
        )
        '''
        connection.execute(query_format_date)
        connection.execute(query_remove_duplicatas)
        # Commit para salvar as alterações
        connection.commit()
        # Fechar a conexão
        connection.close()

    driver.quit()  

    # configuração do e-mail
    msg = MIMEMultipart()
    msg['From'] = email_address
    msg['To'] = 'EMAIL QUE IRA RECEBER'
    msg['Subject'] = f'ATUALIZAÇÃO BANCO DE DADOS DAS COTAÇÕES CEAGESP'
    erros_tratados = [i[:-37] for i in erros]
    # Corpo do e-mail
    if len(erros) == 0:
        corpo_email = f"""
        <p><strong>O Banco de dados das COTAÇÕES CEAGESP foi atualizado 100% ✅</strong></p>
        <br>
        <p><strong><em>Att.</em></strong></p>
        <p><em>Raila Deivid</em></p>
        <p><em>Analista de Dados</em></p>
        """
    else:
        corpo_email = f"""
        <p><strong>O Banco de dados das COTAÇÕES CEAGESP não foi atualizado completamente.</strong>.</p>
        <p><strong>Os grupos: {', '.join(erros_tratados)}. Não tiveram dados atualizados na data {data_scrape}.</strong></p>
        <br>
        <p><strong><em>Att.</em></strong></p>
        <p><em>Raila Deivid</em></p>
        <p><em>Analista de Dados</em></p>
        """
        
    msg.attach(MIMEText(corpo_email, 'html'))

    # Conectar ao servidor SMTP e enviar o e-mail
    
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(email_address, email_password)
    server.sendmail(email_address, msg['To'], msg.as_string())
    server.quit()

# --------------------------------------------- Tratamento de erros gerais do codigo --------------------------------------------- #
except Exception as e:
    # configuração do e-mail
    msg = MIMEMultipart()
    msg['From'] = email_address
    msg['To'] = 'EMAIL QUE IRÁ RECEBER'
    msg['Subject'] = f'>>> ERROS NA EXECUÇÃO DO SCRAPE <<<'

    # Corpo do e-mail
    corpo_email = f"""
    <p><strong>Erro na execução do Scrape!</strong></p>
    <p><strong>Erro:</strong> {e}.</p>
    <br>
    <p><strong><em>Att.</em></strong></p>
    <p><em>Raila Deivid</em></p>
    <p><em>Analista de Dados</em></p>
    """

    msg.attach(MIMEText(corpo_email, 'html'))

    # Conectar ao servidor SMTP e enviar o e-mail
    
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(email_address, email_password)
    server.sendmail(email_address, msg['To'], msg.as_string())
    server.quit()
    driver.quit()
