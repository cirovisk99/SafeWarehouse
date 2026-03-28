"""
SafeWarehouse — Coletor de dados Serial → CSV
Lê os dados enviados pelo Arduino Mega e salva em arquivo .csv automaticamente.

Uso:
    pip install pyserial
    python coletor_serial.py

Pressione Ctrl+C para encerrar a coleta.
"""

import serial
import serial.tools.list_ports
import csv
import time
from datetime import datetime

# ─── Configuração ─────────────────────────────────────────────────────────────
BAUD_RATE   = 115200
CSV_FILE    = "dados_safewarehouse.csv"

# ─── Detecta porta do Arduino automaticamente ─────────s────────────────────────
def encontrar_porta_arduino():
    portas = serial.tools.list_ports.comports()
    for porta in portas:
        if any(kw in porta.description for kw in ("Arduino", "CH340", "USB Serial", "ttyUSB", "ttyACM")):
            return porta.device
    # Se não encontrar automaticamente, lista as disponíveis
    if portas:
        print("Portas disponíveis:")
        for i, p in enumerate(portas):
            print(f"  [{i}] {p.device} — {p.description}")
        idx = int(input("Digite o número da porta do Arduino: "))
        return portas[idx].device
    raise RuntimeError("Nenhuma porta serial encontrada. Verifique a conexão USB.")

# ─── Coleta principal ─────────────────────────────────────────────────────────
def main():
    porta = encontrar_porta_arduino()
    print(f"Conectando em {porta} ({BAUD_RATE} baud)...")

    with serial.Serial(porta, BAUD_RATE, timeout=5) as ser, \
         open(CSV_FILE, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)
        cabecalho_escrito = False

        # Se o arquivo está vazio, aguarda o cabeçalho do Arduino
        f.seek(0, 2)  # vai para o fim
        arquivo_vazio = (f.tell() == 0)

        print(f"Salvando em '{CSV_FILE}'. Pressione Ctrl+C para parar.\n")

        while True:
            try:
                linha = ser.readline().decode("utf-8", errors="ignore").strip()
            except serial.SerialException as e:
                print(f"Erro na porta serial: {e}")
                break

            if not linha:
                continue

            # Cabeçalho enviado pelo Arduino
            if linha == "temp,umidade,distancia,estado":
                if arquivo_vazio and not cabecalho_escrito:
                    writer.writerow(["timestamp", "temp", "umidade", "distancia", "estado"])
                    cabecalho_escrito = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Cabeçalho recebido.")
                continue

            # Linha de dados: "24.0,40,100,SEGURO"
            partes = linha.split(",")
            if len(partes) == 4:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([timestamp] + partes)
                f.flush()  # garante gravação imediata
                print(f"[{timestamp}] {linha}")
            else:
                # Mensagem de debug do Arduino — apenas exibe, não salva
                print(f"[info] {linha}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nColeta encerrada. Arquivo salvo.")
    except RuntimeError as e:
        print(f"Erro: {e}")
