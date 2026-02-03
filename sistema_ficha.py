import tkinter as tk
from tkinter import messagebox
import csv
import os
import fitz  # PyMuPDF
from datetime import datetime

# --- CONFIGURAÇÕES ---
ARQUIVO_CONTADOR = "contador.txt"
ARQUIVO_DB = "atendimentos.csv"
ARQUIVO_MODELO = "FICHA.pdf"  # O PDF original deve estar na mesma pasta
NUMERO_INICIAL = 901

# --- MAPEAMENTO DE COORDENADAS (X, Y) ---
# Ajuste esses números se o texto sair fora do lugar no PDF.
# X = Horizontal (maior vai pra direita)
# Y = Vertical (maior vai pra baixo)
COORDENADAS = {
    "reg": (480, 55),       # Reg. No [cite: 4]
    "data_hora": (480, 85), # Data/Hora [cite: 7, 8]
    "nome": (65, 175),      # Nome [cite: 16]
    "nasc": (380, 175),     # Data Nascimento [cite: 17]
    "idade": (400, 155),    # Idade [cite: 14]
    "queixa": (40, 360),    # Queixa Principal [cite: 35]
    
    # Sinais Vitais [cite: 44-47]
    "pa": (60, 460),        # PA
    "fc": (130, 460),       # FC (coloquei no campo bpb)
    "temp": (240, 460),     # Temp
    "sat": (360, 480),      # Saturação (ajustado visualmente)
    
    "diag": (40, 580),      # Hipótese Diagnóstica [cite: 58]
    "conduta": (40, 640)    # Plano Terapêutico/Conduta [cite: 62]
}

class FichaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Atendimento - CEMEC")
        self.root.geometry("650x600")

        self.reg_atual = self.carregar_proximo_registro()

        # Cabeçalho
        frame_header = tk.Frame(root, bg="#ddd", pady=10)
        frame_header.pack(fill="x")
        tk.Label(frame_header, text="PREENCHIMENTO DE FICHA - CEMEC", bg="#ddd", font=("Arial", 12, "bold")).pack()
        self.lbl_reg = tk.Label(frame_header, text=f"Reg. Nº: {self.reg_atual}", bg="#ddd", fg="red", font=("Arial", 14, "bold"))
        self.lbl_reg.pack()

        # Formulário
        frame_form = tk.Frame(root, padx=20, pady=10)
        frame_form.pack(fill="both", expand=True)

        self.criar_label(frame_form, "Nome do Paciente:", 0, 0)
        self.entry_nome = tk.Entry(frame_form, width=60)
        self.entry_nome.grid(row=0, column=1, columnspan=3, sticky="w", pady=5)

        self.criar_label(frame_form, "Data Nasc. (dd/mm/aaaa):", 1, 0)
        self.entry_nasc = tk.Entry(frame_form, width=20)
        self.entry_nasc.grid(row=1, column=1, sticky="w", pady=5)
        self.entry_nasc.bind("<FocusOut>", self.calcular_idade_evento)

        self.criar_label(frame_form, "Idade:", 1, 2)
        self.entry_idade = tk.Entry(frame_form, width=10, bg="#f0f0f0")
        self.entry_idade.grid(row=1, column=3, sticky="w", pady=5)
        
        self.criar_label(frame_form, "Queixa Principal:", 2, 0)
        self.entry_queixa = tk.Entry(frame_form, width=60)
        self.entry_queixa.grid(row=2, column=1, columnspan=3, sticky="w", pady=5)

        # Sinais Vitais
        frame_vitais = tk.LabelFrame(frame_form, text="Sinais Vitais", padx=10, pady=5)
        frame_vitais.grid(row=3, column=0, columnspan=4, pady=10, sticky="ew")
        
        tk.Label(frame_vitais, text="PA:").pack(side="left")
        self.entry_pa = tk.Entry(frame_vitais, width=8)
        self.entry_pa.pack(side="left", padx=5)

        tk.Label(frame_vitais, text="FC:").pack(side="left")
        self.entry_fc = tk.Entry(frame_vitais, width=8)
        self.entry_fc.pack(side="left", padx=5)

        tk.Label(frame_vitais, text="Temp:").pack(side="left")
        self.entry_temp = tk.Entry(frame_vitais, width=8)
        self.entry_temp.pack(side="left", padx=5)

        tk.Label(frame_vitais, text="Sat O2:").pack(side="left")
        self.entry_sat = tk.Entry(frame_vitais, width=8)
        self.entry_sat.pack(side="left", padx=5)

        self.criar_label(frame_form, "Diagnóstico:", 4, 0)
        self.entry_diag = tk.Entry(frame_form, width=60)
        self.entry_diag.grid(row=4, column=1, columnspan=3, sticky="w", pady=5)

        self.criar_label(frame_form, "Conduta:", 5, 0)
        self.entry_conduta = tk.Entry(frame_form, width=60)
        self.entry_conduta.grid(row=5, column=1, columnspan=3, sticky="w", pady=5)

        # Botões
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        
        btn_salvar = tk.Button(btn_frame, text="SALVAR E IMPRIMIR FICHA", bg="#2980b9", fg="white", font=("Arial", 10, "bold"), command=self.processar)
        btn_salvar.pack(ipadx=20)

    def criar_label(self, parent, text, r, c):
        tk.Label(parent, text=text, font=("Arial", 10)).grid(row=r, column=c, sticky="e", padx=5)

    def calcular_idade_evento(self, event):
        data_str = self.entry_nasc.get()
        if len(data_str) >= 8:
            idade = self.calcular_idade(data_str)
            self.entry_idade.delete(0, tk.END)
            self.entry_idade.insert(0, str(idade))

    def calcular_idade(self, data_nasc_str):
        try:
            d_nasc = datetime.strptime(data_nasc_str, "%d/%m/%Y")
            hoje = datetime.now()
            return hoje.year - d_nasc.year - ((hoje.month, hoje.day) < (d_nasc.month, d_nasc.day))
        except:
            return ""

    def carregar_proximo_registro(self):
        if not os.path.exists(ARQUIVO_CONTADOR): return NUMERO_INICIAL
        try:
            with open(ARQUIVO_CONTADOR, "r") as f: return int(f.read().strip()) + 1
        except: return NUMERO_INICIAL

    def processar(self):
        # 1. Coletar Dados
        dados = {
            "reg": str(self.reg_atual),
            "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "nome": self.entry_nome.get(),
            "nasc": self.entry_nasc.get(),
            "idade": self.entry_idade.get(),
            "queixa": self.entry_queixa.get(),
            "pa": self.entry_pa.get(),
            "fc": self.entry_fc.get(),
            "temp": self.entry_temp.get(),
            "sat": self.entry_sat.get(),
            "diag": self.entry_diag.get(),
            "conduta": self.entry_conduta.get()
        }

        if not dados["nome"]:
            messagebox.showwarning("Erro", "Nome é obrigatório!")
            return

        # 2. Salvar no Excel (CSV)
        self.salvar_csv(dados)

        # 3. Gerar PDF Preenchido
        caminho_pdf = self.gerar_pdf(dados)

        if caminho_pdf:
            # 4. Abrir PDF para Impressão
            try:
                os.startfile(caminho_pdf) # Comando Windows para abrir o arquivo
            except AttributeError:
                # Caso esteja em Linux/Mac (opcional)
                import subprocess
                subprocess.call(['xdg-open', caminho_pdf])

            # 5. Atualizar Contador e Limpar
            self.atualizar_contador()
            self.limpar_campos()

    def salvar_csv(self, dados):
        existe = os.path.exists(ARQUIVO_DB)
        with open(ARQUIVO_DB, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            if not existe: writer.writerow(dados.keys())
            writer.writerow(dados.values())

    def gerar_pdf(self, dados):
        if not os.path.exists(ARQUIVO_MODELO):
            messagebox.showerror("Erro", f"Arquivo '{ARQUIVO_MODELO}' não encontrado na pasta!")
            return None

        try:
            doc = fitz.open(ARQUIVO_MODELO)
            pagina = doc[0] # Pega a primeira página [cite: 1-58]

            # Insere os textos nas coordenadas mapeadas
            for chave, texto in dados.items():
                if chave in COORDENADAS and texto:
                    x, y = COORDENADAS[chave]
                    # Insere texto (cor preta, tamanho 10)
                    pagina.insert_text((x, y), str(texto), fontsize=10, color=(0, 0, 0))

            nome_arquivo_saida = f"Ficha_{dados['reg']}.pdf"
            doc.save(nome_arquivo_saida)
            return nome_arquivo_saida
        except Exception as e:
            messagebox.showerror("Erro PDF", f"Erro ao gerar PDF: {e}")
            return None

    def atualizar_contador(self):
        with open(ARQUIVO_CONTADOR, "w") as f: f.write(str(self.reg_atual))
        self.reg_atual += 1
        self.lbl_reg.config(text=f"Reg. Nº: {self.reg_atual}")

    def limpar_campos(self):
        for entry in [self.entry_nome, self.entry_nasc, self.entry_idade, self.entry_queixa,
                      self.entry_pa, self.entry_fc, self.entry_temp, self.entry_sat, 
                      self.entry_diag, self.entry_conduta]:
            entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = FichaApp(root)
    root.mainloop()
