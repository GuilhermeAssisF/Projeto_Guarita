import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import time
import database_manager
from reconhecimento import DetectorPlaca


class GuaritaApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("1100x650")

        # Inicializa Banco
        database_manager.inicializar_banco()

        # --- Sistema de Visão (Carrega IA) ---
        self.detector = DetectorPlaca()
        self.camera_ativa = False

        # --- Configuração das Abas ---
        self.notebook = ttk.Notebook(window)
        self.notebook.pack(fill='both', expand=True)

        # Aba 1: Monitoramento (Câmera)
        self.tab_monitor = tk.Frame(self.notebook, bg="#202020")
        self.notebook.add(self.tab_monitor, text="📹 Monitoramento Automático")
        self.setup_monitoramento()

        # Aba 2: Cadastro Manual (Sem Câmera)
        self.tab_manual = tk.Frame(self.notebook)
        self.notebook.add(self.tab_manual, text="📝 Cadastro Manual & Frotas")
        self.setup_cadastro_manual()

        # Evento de troca de aba
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # Variáveis de Estado
        self.delay = 15
        self.ultimo_registro_tempo = 0
        self.placa_atual = None

        # Inicia loop
        self.update_camera()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ================= ABA 1: MONITORAMENTO =================
    def setup_monitoramento(self):
        # Frame Esquerdo (Vídeo)
        self.vid_frame = tk.Frame(self.tab_monitor, width=700, height=500, bg="black")
        self.vid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.video_label = tk.Label(self.vid_frame, bg="black", text="Câmera Desativada", fg="white")
        self.video_label.pack(expand=True)

        # Frame Direito (Controles Rápidos)
        self.ctrl_frame = tk.Frame(self.tab_monitor, width=350, bg="#f0f0f0")
        self.ctrl_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Status
        tk.Label(self.ctrl_frame, text="Status em Tempo Real", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)

        self.lbl_placa = tk.Label(self.ctrl_frame, text="---", font=("Arial", 30, "bold"), fg="blue", bg="#f0f0f0")
        self.lbl_placa.pack(pady=5)

        self.lbl_info = tk.Label(self.ctrl_frame, text="Aguardando veículo...", font=("Arial", 11), bg="#f0f0f0")
        self.lbl_info.pack(pady=5)

        # Log Rápido
        tk.Label(self.ctrl_frame, text="Últimos Eventos:", bg="#f0f0f0", anchor="w").pack(fill="x", padx=10)
        self.txt_log = tk.Text(self.ctrl_frame, height=15, width=35)
        self.txt_log.pack(padx=10, pady=5)

        # Botão Relatório
        btn_relatorio = tk.Button(self.ctrl_frame, text="📄 Gerar Relatório de Acessos",
                                  command=self.gerar_relatorio, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        btn_relatorio.pack(side=tk.BOTTOM, fill="x", padx=10, pady=20)

    # ================= ABA 2: CADASTRO MANUAL =================
    def setup_cadastro_manual(self):
        # Frame Superior: Formulário
        form_frame = tk.LabelFrame(self.tab_manual, text="Dados do Veículo", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Grid layout para o form
        tk.Label(form_frame, text="Placa:").grid(row=0, column=0, sticky="w")
        self.ent_man_placa = tk.Entry(form_frame, width=15)
        self.ent_man_placa.grid(row=0, column=1, sticky="w", padx=5)

        tk.Label(form_frame, text="Proprietário:").grid(row=0, column=2, sticky="w")
        self.ent_man_prop = tk.Entry(form_frame, width=30)
        self.ent_man_prop.grid(row=0, column=3, sticky="w", padx=5)

        tk.Label(form_frame, text="Categoria:").grid(row=1, column=0, sticky="w", pady=5)
        self.cb_man_cat = ttk.Combobox(form_frame, values=["VISITANTE", "PARTICULAR", "OFICIAL"], width=12)
        self.cb_man_cat.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(form_frame, text="Status:").grid(row=1, column=2, sticky="w")
        self.cb_man_status = ttk.Combobox(form_frame, values=["AUTORIZADO", "BLOQUEADO", "SUSPEITO"], width=27)
        self.cb_man_status.grid(row=1, column=3, sticky="w", padx=5)

        # Botões de Ação
        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=0, column=4, rowspan=2, padx=20)

        btn_salvar = tk.Button(btn_frame, text="💾 Salvar", command=self.salvar_manual, bg="#4CAF50", fg="white",
                               width=15)
        btn_salvar.pack(pady=2)

        # Botão Excluir (Adicionado)
        btn_excluir = tk.Button(btn_frame, text="🗑️ Excluir", command=self.excluir_manual, bg="#F44336", fg="white",
                                width=15)
        btn_excluir.pack(pady=2)

        # Frame Inferior: Tabela de Veículos
        table_frame = tk.LabelFrame(self.tab_manual, text="Veículos Cadastrados", padx=10, pady=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview (Tabela)
        cols = ("Placa", "Proprietário", "Categoria", "Status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        self.tree.pack(fill="both", expand=True, side=tk.LEFT)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Botão de Atualizar Lista
        btn_refresh = tk.Button(self.tab_manual, text="🔄 Atualizar Lista", command=self.atualizar_tabela)
        btn_refresh.pack(pady=5)

        # Duplo clique na tabela preenche o formulário
        self.tree.bind("<Double-1>", self.on_tabela_click)

    # ================= LÓGICA DE CONTROLE =================
    def on_tab_change(self, event):
        """Gerencia a câmera ao trocar de abas"""
        tab_id = self.notebook.index(self.notebook.select())

        if tab_id == 0:  # Aba Monitoramento
            print("Entrando em Monitoramento: Ligando Câmera...")
            self.detector.conectar_camera()
            self.camera_ativa = True
        else:  # Aba Manual
            print("Entrando em Cadastro Manual: Desligando Câmera...")
            self.detector.desconectar_camera()
            self.camera_ativa = False
            self.video_label.config(image='', text="Câmera Pausada (Economia de Energia)", bg="#101010")
            self.atualizar_tabela()

    def update_camera(self):
        """Loop principal de atualização da interface da câmera"""
        if self.camera_ativa:
            frame = self.detector.ler_frame()

            if frame is not None:
                # Processamento OCR
                frame_processado, texto, _ = self.detector.processar(frame)

                # Atualiza Interface com a Imagem
                cv2image = cv2.cvtColor(frame_processado, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

                # Lógica de Negócio
                if texto:
                    self.processar_logica_monitor(texto)
            else:
                self.video_label.config(text="Câmera Conectada - Aguardando Imagem...")

        # Chama a si mesmo novamente em X ms
        self.window.after(self.delay, self.update_camera)

    def processar_logica_monitor(self, placa):
        # Evita spam
        if placa == self.placa_atual and (time.time() - self.ultimo_registro_tempo < 5):
            return

        self.placa_atual = placa
        self.ultimo_registro_tempo = time.time()
        self.lbl_placa.config(text=placa)

        veiculo = database_manager.buscar_veiculo(placa)

        if veiculo:
            status = veiculo[4]
            self.lbl_info.config(text=f"Status: {status}", fg="red" if status == "BLOQUEADO" else "green")

            if status == "BLOQUEADO":
                self.log(f"🚨 ALERTA: VEÍCULO BLOQUEADO {placa}")
                messagebox.showwarning("SEGURANÇA", f"Veículo {placa} BLOQUEADO tentou acessar!")
            else:
                sucesso, msg = database_manager.registrar_entrada(placa)
                if not sucesso:
                    sucesso_saida, msg_saida = database_manager.registrar_saida(placa)
                    self.log(f"⬅️ Saída {placa}: {msg_saida}")
                else:
                    self.log(f"➡️ Entrada {placa}: {msg}")
        else:
            self.lbl_info.config(text="Não Cadastrado", fg="orange")
            self.log(f"⚠️ Visitante desconhecido: {placa}")

    # ================= LÓGICA MANUAL =================
    def salvar_manual(self):
        placa = self.ent_man_placa.get().upper()
        prop = self.ent_man_prop.get()
        cat = self.cb_man_cat.get()
        status = self.cb_man_status.get()

        if len(placa) < 7:
            messagebox.showerror("Erro", "Placa inválida.")
            return

        if database_manager.cadastrar_veiculo(placa, prop, "CARRO", cat, status):
            messagebox.showinfo("Sucesso", f"Veículo {placa} salvo!")
            self.atualizar_tabela()
            # Limpar campos
            self.ent_man_placa.delete(0, tk.END)
            self.ent_man_prop.delete(0, tk.END)
        else:
            messagebox.showerror("Erro", "Falha ao salvar no banco.")

    def excluir_manual(self):
        """Função para excluir veículo selecionado"""
        placa = self.ent_man_placa.get().upper()

        if not placa:
            messagebox.showwarning("Aviso", "Selecione um veículo na tabela ou digite a placa para excluir.")
            return

        # Confirmação de segurança
        resposta = messagebox.askyesno("Confirmar Exclusão",
                                       f"Tem certeza que deseja apagar o veículo {placa}?\nIsso removerá também o histórico de acessos dele.")

        if resposta:
            if database_manager.excluir_veiculo(placa):
                messagebox.showinfo("Sucesso", f"Veículo {placa} removido.")
                self.atualizar_tabela()
                # Limpa os campos
                self.ent_man_placa.delete(0, tk.END)
                self.ent_man_prop.delete(0, tk.END)
            else:
                messagebox.showerror("Erro", "Falha ao excluir. Verifique se a placa está correta.")

    def atualizar_tabela(self):
        # Limpa tabela
        for i in self.tree.get_children():
            self.tree.delete(i)

        dados = database_manager.listar_todos_veiculos()
        for row in dados:
            self.tree.insert("", tk.END, values=row)

    def on_tabela_click(self, event):
        selected = self.tree.focus()
        values = self.tree.item(selected, 'values')
        if values:
            self.ent_man_placa.delete(0, tk.END)
            self.ent_man_placa.insert(0, values[0])
            self.ent_man_prop.delete(0, tk.END)
            self.ent_man_prop.insert(0, values[1])
            self.cb_man_cat.set(values[2])
            self.cb_man_status.set(values[3])

    # ================= UTILITÁRIOS =================
    def log(self, mensagem):
        self.txt_log.insert(tk.END, f"{time.strftime('%H:%M')} - {mensagem}\n")
        self.txt_log.see(tk.END)

    def gerar_relatorio(self):
        sucesso, msg = database_manager.exportar_relatorio()
        if sucesso:
            messagebox.showinfo("Relatório", f"Salvo em:\n{msg}")
        else:
            messagebox.showerror("Erro", msg)

    def on_closing(self):
        self.detector.desconectar_camera()
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    # Tenta definir um ícone se houver (opcional)
    # root.iconbitmap('icone.ico')
    app = GuaritaApp(root, "Sistema Guarita IFSULDEMINAS v2.0")
    root.mainloop()