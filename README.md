# Sistema de Controle de Acesso - IFSULDEMINAS

Sistema de guarita inteligente desenvolvido em Python utilizando Visão Computacional para leitura de placas veiculares (LPR/OCR) e controle de acesso.

## 📋 Funcionalidades

* **Monitoramento Automático:** Detecção e leitura de placas via Webcam em tempo real.
* **Controle de Acesso:** Verificação automática de veículos autorizados, bloqueados ou visitantes.
* **Cadastro Manual:** Interface dedicada para cadastro de frotas e correção de dados, com desativação automática da câmera para economia de recursos.
* **Relatórios:** Exportação de histórico de acessos (entradas e saídas) em formato CSV.
* **Alertas de Segurança:** Notificação visual imediata para veículos marcados como "BLOQUEADO" ou "SUSPEITO".

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+ (Testado na versão 3.11)
* **Interface Gráfica:** Tkinter (Biblioteca nativa do Python)
* **Visão Computacional:** OpenCV (Processamento de imagem) + EasyOCR (Leitura de caracteres com Deep Learning)
* **Banco de Dados:** SQLite3 (Armazenamento local leve)
* **Manipulação de Dados:** Pandas (Geração de relatórios)

## 🚀 Como Rodar o Projeto

### 1. Pré-requisitos

Certifique-se de ter o Python instalado. Recomenda-se a versão **3.10** ou **3.11** para melhor compatibilidade com as bibliotecas de IA.

### 2. Instalação

Clone este repositório e instale as dependências listadas:

```bash
# Clone o repositório
git clone [https://github.com/SEU_USUARIO/NOME_DO_REPO.git](https://github.com/SEU_USUARIO/NOME_DO_REPO.git)

# Entre na pasta do projeto
cd NOME_DO_REPO

# Instale as bibliotecas necessárias
pip install -r requirements.txt
```

### 3. Execução

Para iniciar o sistema, execute o arquivo da interface principal dentro da pasta `src`:

```bash
cd src
python interface.py
```

## 📂 Estrutura do Projeto

```text
/
├── data/                  # Onde o banco de dados (estacionamento.db) será criado
├── src/                   # Código Fonte
│   ├── interface.py       # Arquivo principal (GUI)
│   ├── reconhecimento.py  # Lógica de Visão Computacional e OCR
│   └── database_manager.py # Gerenciamento do SQLite
├── .gitignore             # Arquivos ignorados pelo Git
├── README.md              # Documentação
└── requirements.txt       # Lista de dependências
```

## 👥 Autores
Guilherme Assis Fernandes

Camilo Andrés Coronado León

Dyogo Henrique da Silva
