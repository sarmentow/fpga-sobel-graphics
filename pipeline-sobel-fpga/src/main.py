import serial
import serial.tools.list_ports
import time
import threading
import sys

def list_serial_ports():
    """Lists serial port names available on the system."""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("Nenhuma porta serial encontrada.")
        return []
    
    print("Portas Seriais Disponíveis:")
    for port, desc, hwid in ports:
        print(f" - {port}: {desc} [{hwid}]")
    return [p.device for p in ports]

def listen_to_port(ser, stop_event):
    """
    Runs in a separate thread to listen for incoming data.
    """
    print(f"--- Escuta iniciada na porta {ser.port} ---")
    
    while not stop_event.is_set():
        try:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                
                for byte in data:
                    print(f"\n[RX RECEBIDO] Dec: {byte} | Hex: {hex(byte)} | Bin: {format(byte, '08b')}")
                
                print(">> Digite um número decimal (0-255): ", end="", flush=True)

        except serial.SerialException as e:
            print(f"\n[Erro de Leitura] {e}")
            stop_event.set()
            break
        except Exception as e:
            print(f"\n[Erro na Thread] {e}")
            break

def start_transceiver(port_name, baud_rate):
    """
    Opens the UART port in 8N1 mode.
    Starts a thread for reading and keeps the main thread for writing.
    """
    try:
        ser = serial.Serial(
            port=port_name,
            baudrate=baud_rate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )

        if ser.is_open:
            print(f"\nConectado em {port_name} a {baud_rate} baud (8N1).")
            print("NOTA: Modo Full-Duplex (Envio e Recebimento simultâneos).")
            print("-" * 60)

            stop_event = threading.Event()
            read_thread = threading.Thread(target=listen_to_port, args=(ser, stop_event))
            read_thread.daemon = True 
            read_thread.start()

            print("Digite 'EXIT' para sair.")
            
            while True:
                try:
                    user_input = input(">> Digite um número decimal (0-255): ")
                    
                    if user_input.strip().upper() == 'EXIT':
                        print("Encerrando...")
                        stop_event.set() 
                        break
                    
                    try:
                        val = int(eval(user_input))
                        
                        if 0 <= val <= 255:
                            ser.write(bytes([val]))
                            ser.flush() 
                        else:
                            print(f"ERRO: Valor {val} fora do limite de 1 byte (0-255).")
                            
                    except ValueError:
                        print("Entrada inválida. Digite um número inteiro.")
                        
                except KeyboardInterrupt:
                    print("\nInterrupção de Teclado detectada.")
                    stop_event.set()
                    break

            print("Aguardando thread de leitura finalizar...")
            read_thread.join(timeout=2)
            ser.close()
            print("Conexão fechada.")

    except serial.SerialException as e:
        print(f"Erro ao abrir porta serial: {e}")

if __name__ == "__main__":
    available_ports = list_serial_ports()
    
    if available_ports:
        target_port = available_ports[0] 
        target_baud = 115200 

        print(f"\n--- Transceptor UART (Threaded 8N1) ---")

        start_transceiver(target_port, target_baud)
    else:
        print("\nConecte o dispositivo e tente novamente.")