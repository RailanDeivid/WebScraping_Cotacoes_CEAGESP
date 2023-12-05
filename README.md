# Automatização de Extração de Dados da CEAGESP

## Introdução

Neste projeto, apresento uma solução desenvolvida para automatizar a extração de dados do site de cotações de preços de entrepostos da CEAGESP. Essa tarefa manual, que envolvia a obtenção da média de preços de venda no atacado, era realizada às segundas, quartas e sextas-feiras, exigindo intervenção manual constante.

Diante dessa rotina repetitiva, decidi criar uma solução automatizada, utilizando a biblioteca Selenium para interagir com o site e coletar dados de forma eficiente, eliminando a necessidade de intervenção manual constante.

## Objetivo

O objetivo principal deste processo é obter as cotações de preços de entrepostos, possibilitando análises futuras sobre os preços no atacado. Optei por utilizar a biblioteca Selenium devido à minha familiaridade com ela, que permite interagir facilmente com elementos HTML, preencher formulários e navegar por páginas da web.

Além disso, escolhi o banco de dados SQLite para armazenar os dados coletados. O SQLite é um sistema de gerenciamento de banco de dados relacional embutido, não requer um servidor separado e oferece suporte à maioria dos comandos SQL padrão, permitindo a criação, consulta e modificação de dados.

Script Python: [Created_DB_CEAGESP](https://github.com/RailanDeivid/WebScraping_Cotacoes_CEAGESP/blob/main/Script/Created_DB_CEAGESP.py)

Banco de dados SQLite: [DB_PRECOS_CEAGESP](https://github.com/RailanDeivid/WebScraping_Cotacoes_CEAGESP/tree/main/Banco%20SQLite)

#### No meu blog do Midium explico o passo a passo desse processo: 
[Web Scraping Cotações do CEAGESP e Armazenamento em Banco de Dados SQLite com Python.](https://medium.com/@railandeivid/web-scraping-cotações-do-ceagesp-e-armazenamento-em-banco-de-dados-sqlite-com-python-348b003d3e61)
