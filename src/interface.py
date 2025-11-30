import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import database_manager
from reconhecimento import DetectorPlaca


class GuaritaApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("1100x600")

        # Inicializa Banco
        database_manager.inicializar_banco()

        # --- Layout Principal ---
        # Frame Esquerdo (Vídeo)
        self.left_frame = tk.Frame(window, width=640, height=480, bg="black")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.video_label = tk.Label(self.left_frame)
        self.video_label.pack(expand=True)

        # Frame Direito (Controles)
        self.right_frame = tk.Frame(window, width=400, bg="#f0f0f0")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.criar_painel_controle()

        # --- Sistema de Visão ---
        self.detector = DetectorPlaca()
        self.delay = 15
        self.ultimo_registro_tempo = 0
        self.placa_atual = None

        # Inicia Loop de Vídeo
        self.update()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def criar_painel_controle(self):
        pad = 10

        # Título
        lbl_titulo = tk.Label(self.right_frame, text="Controle de Acesso IFSULDEMINAS", font=("Arial", 16, "bold"),
                              bg="#f0f0f0")
        lbl_titulo.pack(pady=20)

        # -- Área de Status da Leitura --
        self.frame_status = tk.LabelFrame(self.right_frame, text="Veículo Detectado", font=("Arial", 12), bg="#f0f0f0")
        self.frame_status.pack(fill="x", padx=pad, pady=pad)

        self.lbl_placa = tk.Label(self.frame_status, text="---", font=("Arial", 24, "bold"), fg="blue", bg="#f0f0f0")
        self.lbl_placa.pack()

        self.lbl_info = tk.Label(self.frame_status, text="Aguardando veículo...", font=("Arial", 10), bg="#f0f0f0")
        self.lbl_info.pack(pady=5)

        # -- Área de Cadastro / Edição (Requisitos 2 e 3) --
        self.frame_cadastro = tk.LabelFrame(self.right_frame, text="Gerenciar Veículo", font=("Arial", 12),
                                            bg="#f0f0f0")
        self.frame_cadastro.pack(fill="x", padx=pad, pady=pad)

        tk.Label(self.frame_cadastro, text="Proprietário:", bg="#f0f0f0").pack(anchor="w")
        self.entry_proprietario = tk.Entry(self.frame_cadastro)
        self.entry_proprietario.pack(fill="x", padx=5)

        tk.Label(self.frame_cadastro, text="Categoria:", bg="#f0f0f0").pack(anchor="w")
        self.combo_categoria = ttk.Combobox(self.frame_cadastro, values=["VISITANTE", "PARTICULAR", "OFICIAL"])
        self.combo_categoria.pack(fill="x", padx=5)

        tk.Label(self.frame_cadastro, text="Status:", bg="#f0f0f0").pack(anchor="w")
        self.combo_status = ttk.Combobox(self.frame_cadastro, values=["AUTORIZADO", "BLOQUEADO", "SUSPEITO"])
        self.combo_status.pack(fill="x", padx=5)

        btn_salvar = tk.Button(self.frame_cadastro, text="Salvar / Atualizar", command=self.salvar_veiculo,
                               bg="#4CAF50", fg="white")
        btn_salvar.pack(fill="x", pady=10, padx=5)

        # -- Área de Logs --
        self.txt_log = tk.Text(self.right_frame, height=10, width=40)
        self.txt_log.pack(padx=pad, pady=pad)

        # -- Botão Relatório (Requisito 5) --
        btn_relatorio = tk.Button(self.right_frame, text="Gerar Relatório de Acessos", command=self.gerar_relatorio)
        btn_relatorio.pack(side=tk.BOTTOM, pady=20)

    def log(self, mensagem):
        self.txt_log.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {mensagem}\n")
        self.txt_log.see(tk.END)

    def salvar_veiculo(self):
        placa = self.lbl_placa.cget("text")
        if placa == "---" or len(placa) < 7:
            messagebox.showwarning("Aviso", "Nenhuma placa detectada para salvar.")
            return

        prop = self.entry_proprietario.get()
        cat = self.combo_categoria.get()
        status = self.combo_status.get()

        if database_manager.cadastrar_veiculo(placa, prop, "CARRO", cat, status):
            messagebox.showinfo("Sucesso", f"Veículo {placa} atualizado!")
            self.log(f"Cadastro atualizado: {placa}")
        else:
            messagebox.showerror("Erro", "Falha ao salvar no banco.")

    def gerar_relatorio(self):
        sucesso, msg = database_manager.exportar_relatorio()
        if sucesso:
            messagebox.showinfo("Relatório", f"Relatório salvo em:\n{msg}")
        else:
            messagebox.showerror("Erro", msg)

    def processar_logica_negocio(self, placa):
        # Evita flood de processamento (só processa a cada 5s a mesma placa)
        if placa == self.placa_atual and (time.time() - self.ultimo_registro_tempo < 5):
            return

        self.placa_atual = placa
        self.ultimo_registro_tempo = time.time()

        self.lbl_placa.config(text=placa)

        # Consulta Banco
        veiculo = database_manager.buscar_veiculo(placa)

        if veiculo:
            # Preenche o formulário automaticamente
            self.entry_proprietario.delete(0, tk.END)
            self.entry_proprietario.insert(0, veiculo[1] if veiculo[1] else "")
            self.combo_categoria.set(veiculo[3] if veiculo[3] else "VISITANTE")
            self.combo_status.set(veiculo[4] if veiculo[4] else "AUTORIZADO")

            status = veiculo[4]
            self.lbl_info.config(text=f"Status: {status}", fg="red" if status == "BLOQUEADO" else "green")

            # Alertas (Requisito 7)
            if status == "BLOQUEADO":
                self.log(f"ALERTA: VEÍCULO BLOQUEADO {placa}")
                # messagebox.showwarning("ALERTA DE SEGURANÇA", f"Veículo {placa} está BLOQUEADO!")
            else:
                # Tenta Entrada
                sucesso, msg = database_manager.registrar_entrada(placa)
                if not sucesso:
                    # Se não entrou, tenta Saída
                    sucesso_saida, msg_saida = database_manager.registrar_saida(placa)
                    self.log(f"{placa}: {msg_saida}")

                    # Alerta Tempo (Requisito 6 - Exemplo simples: alerta se > 10 seg só pra testar)
                    if "Permanência" in msg_saida:
                        pass  # Aqui poderia checar se o tempo foi muito longo
                else:
                    self.log(f"{placa}: {msg}")
        else:
            self.lbl_info.config(text="Veículo Não Cadastrado", fg="orange")
            self.log(f"Novo visitante: {placa}")
            # Limpa form para cadastro novo
            self.entry_proprietario.delete(0, tk.END)
            self.combo_categoria.set("VISITANTE")
            self.combo_status.set("AUTORIZADO")

    def update(self):
        # 1. Pega frame da classe de reconhecimento
        frame = self.detector.ler_frame()

        if frame is not None:
            # 2. Processa (OCR)
            frame_processado, texto, _ = self.detector.processar(frame)

            # 3. Lógica de Interface
            if texto:
                self.processar_logica_negocio(texto)

            # 4. Converte para mostrar no Tkinter
            cv2image = cv2.cvtColor(frame_processado, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)

            # Ajusta tamanho para caber no frame
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.window.after(self.delay, self.update)

    def on_closing(self):
        self.detector.liberar()
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = GuaritaApp(root, "Sistema Guarita IFSULDEMINAS")
    root.mainloop()