import sqlite3
from datetime import datetime
import pandas as pd
import os

# Caminho absoluto para evitar erro de pasta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "../data/estacionamento.db")


def conectar():
    return sqlite3.connect(DB_NAME)


def inicializar_banco():
    # Garante que a pasta data existe
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS veiculos
                   (
                       placa
                       TEXT
                       PRIMARY
                       KEY,
                       proprietario
                       TEXT,
                       tipo
                       TEXT,
                       categoria
                       TEXT,
                       status
                       TEXT,
                       observacao
                       TEXT
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS acessos
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       placa
                       TEXT,
                       data_entrada
                       DATE,
                       hora_entrada
                       TIME,
                       hora_saida
                       TIME,
                       FOREIGN
                       KEY
                   (
                       placa
                   ) REFERENCES veiculos
                   (
                       placa
                   )
                       )
                   ''')

    conn.commit()
    conn.close()


def cadastrar_veiculo(placa, proprietario, tipo, categoria, status="AUTORIZADO"):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO veiculos (placa, proprietario, tipo, categoria, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (placa.upper(), proprietario, tipo, categoria, status))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False
    finally:
        conn.close()


def buscar_veiculo(placa):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM veiculos WHERE placa = ?", (placa.upper(),))
    veiculo = cursor.fetchone()
    conn.close()
    return veiculo


def registrar_entrada(placa):
    conn = conectar()
    cursor = conn.cursor()
    agora = datetime.now()
    data_atual = agora.strftime("%Y-%m-%d")
    hora_atual = agora.strftime("%H:%M:%S")

    # Verifica se já está dentro
    cursor.execute('''
                   SELECT id
                   FROM acessos
                   WHERE placa = ?
                     AND data_entrada = ?
                     AND hora_saida IS NULL
                   ''', (placa.upper(), data_atual))

    if cursor.fetchone():
        conn.close()
        return False, "Veículo já está no campus"

    cursor.execute('''
                   INSERT INTO acessos (placa, data_entrada, hora_entrada)
                   VALUES (?, ?, ?)
                   ''', (placa.upper(), data_atual, hora_atual))

    conn.commit()
    conn.close()
    return True, f"Entrada: {hora_atual}"


def registrar_saida(placa):
    conn = conectar()
    cursor = conn.cursor()
    agora = datetime.now()
    data_atual = agora.strftime("%Y-%m-%d")
    hora_atual = agora.strftime("%H:%M:%S")

    cursor.execute('''
                   SELECT id, hora_entrada
                   FROM acessos
                   WHERE placa = ?
                     AND data_entrada = ?
                     AND hora_saida IS NULL
                   ''', (placa.upper(), data_atual))

    registro = cursor.fetchone()

    if registro:
        registro_id, hora_entrada_str = registro
        cursor.execute('''
                       UPDATE acessos
                       SET hora_saida = ?
                       WHERE id = ?
                       ''', (hora_atual, registro_id))
        conn.commit()
        conn.close()

        fmt = '%H:%M:%S'
        t_entrada = datetime.strptime(hora_entrada_str, fmt)
        t_saida = datetime.strptime(hora_atual, fmt)
        permanencia = t_saida - t_entrada

        return True, f"Permanência: {permanencia}"
    else:
        conn.close()
        return False, "Nenhuma entrada aberta"


def exportar_relatorio():
    """Gera um Excel com o histórico de acessos (Requisito 5)"""
    conn = conectar()
    try:
        query = """
                SELECT a.id, a.placa, v.proprietario, v.categoria, a.data_entrada, a.hora_entrada, a.hora_saida
                FROM acessos a
                         LEFT JOIN veiculos v ON a.placa = v.placa
                ORDER BY a.data_entrada DESC, a.hora_entrada DESC \
                """
        df = pd.read_sql_query(query, conn)

        filename = f"../relatorio_acessos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        # Salva em CSV para não depender de libs de Excel pesadas
        df.to_csv(filename, index=False, sep=';', encoding='utf-8-sig')
        return True, filename
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


if __name__ == "__main__":
    inicializar_banco()