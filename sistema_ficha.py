import tkinter as tk
from tkinter import messagebox
import csv
import os
from datetime import datetime

# Configuração Inicial
ARQUIVO_CONTADOR = "contador.txt"
ARQUIVO_DB = "atendimentos.csv"
NUMERO_INICIAL = 901

class FichaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Atendimento - CEMEC")
        self.root.geometry("650x550")

        # --- Lógica do Número de Registro ---
        self.reg_atual = self.carregar_proximo_registro()

        # --- Cabeçalho ---
        frame_header = tk.Frame(root, bg="#ddd", pady=10)
        frame_header.pack(fill="x")
        
        lbl_titulo = tk.Label(frame_header, text="FICHA DE ATENDIMENTO DE URGÊNCIA", bg="#ddd", font=("Arial", 12, "bold"))
        lbl_titulo.pack()

        self.lbl_reg = tk.Label(frame_header, text=f"Reg. Nº: {self.reg_atual}", bg="#ddd", fg="red", font=("Arial", 14, "bold"))
        self.lbl_reg.pack()

        # --- Formulário ---
        frame_form = tk.Frame(root, padx=20, pady=20)
        frame_form.pack(fill="both", expand=True)

        # 1. Nome
        self.criar_label(frame_form, "Nome do Paciente:", 0, 0)
        self.entry_nome = tk.Entry(frame_form, width=60)
        self.entry_nome.grid(row=0, column=1, columnspan=3, sticky="w", pady=5)

        # 2. Data de Nascimento e Idade (Lógica Nova)
        self.criar_label(frame_form, "Data Nasc. (dd/mm/aaaa):", 1, 0)
        
        self.entry_nasc = tk.Entry(frame_form, width=20)
        self.entry_nasc.grid(row=1, column=1, sticky="w", pady=5)
        # O evento FocusOut dispara quando você sai do campo (aperta Tab ou clica fora)
        self.entry_nasc.bind("<FocusOut>", self.calcular_idade_evento)

        self.criar_label(frame_form, "Idade:", 1, 2)
        self.entry_idade = tk.Entry(frame_form, width=10, bg="#f0f0f0") # Cinza para indicar automático
        self.entry_idade.grid(row=1, column=3, sticky="w", pady=5)
        
        # 3. Queixa
        self.criar_label(frame_form, "Queixa Principal:", 2, 0)
        self.entry_queixa = tk.Entry(frame_form, width=60)
        self.entry_queixa.grid(row=2, column=1, columnspan=3, sticky="w", pady=5)

        # 4. Sinais Vitais
        frame_vitais = tk.Frame(frame_form)
        frame_vitais.grid(row=3, column=0, columnspan=4, pady=15, sticky="w")
        
        tk.Label(frame_vitais, text="PA (mmHg):").pack(side="left")
        self.entry_pa = tk.Entry(frame_vitais, width=8)
        self.entry_pa.pack(side="left", padx=5)

        tk.Label(frame_vitais, text="Temp (ºC):").pack(side="left")
        self.entry_temp = tk.Entry(frame_vitais, width=8)
        self.entry_temp.pack(side="left", padx=5)

        tk.Label(frame_vitais, text="Sat O2 (%):").pack(side="left")
        self.entry_sat = tk.Entry(frame_vitais, width=8)
        self.entry_sat.pack(side="left", padx=5)

        # 5. Diagnóstico e Conduta
        self.criar_label(frame_form, "Diagnóstico / Hipótese:", 4, 0)
        self.entry_diag = tk.Entry(frame_form, width=60)
        self.entry_diag.grid(row=4, column=1, columnspan=3, sticky="w", pady=5)

        self.criar_label(frame_form, "Conduta / Destino:", 5, 0)
        self.entry_conduta = tk.Entry(frame_form, width=60)
        self.entry_conduta.grid(row=5, column=1, columnspan=3, sticky="w", pady=5)

        # Botão Salvar
        btn_salvar = tk.Button(root, text="SALVAR ATENDIMENTO", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.salvar)
        btn_salvar.pack(pady=10, ipadx=20)

    # --- Funções Auxiliares ---
    def criar_label(self, parent, text, r, c):
        label = tk.Label(parent, text=text, font=("Arial", 10))
        label.grid(row=r, column=c, sticky="e", padx=5)

    def calcular_idade_evento(self, event):
        data_str = self.entry_nasc.get()
        if len(data_str) >= 8: # Tenta calcular se tiver texto suficiente
            idade = self.calcular_idade(data_str)
            self.entry_idade.delete(0, tk.END)
            self.entry_idade.insert(0, str(idade))

    def calcular_idade(self, data_nasc_str):
        try:
            # Converte string para data
            data_nasc = datetime.strptime(data_nasc_str, "%d/%m/%Y")
            hoje = datetime.now()
            # Calcula a idade
            idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
            return idade
        except ValueError:
            return "Erro" # Retorna erro se a data estiver em formato errado

    def carregar_proximo_registro(self):
        if not os.path.exists(ARQUIVO_CONTADOR):
            return NUMERO_INICIAL
        with open(ARQUIVO_CONTADOR, "r") as f:
            try:
                ultimo = int(f.read().strip())
                return ultimo + 1
            except:
                return NUMERO_INICIAL

    def atualizar_contador(self):
        with open(ARQUIVO_CONTADOR, "w") as f:
            f.write(str(self.reg_atual))
        self.reg_atual += 1
        self.lbl_reg.config(text=f"Reg. Nº: {self.reg_atual}")

    def salvar(self):
        dados = [
            self.reg_atual,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            self.entry_nome.get(),
            self.entry_nasc.get(), # Nova coluna Data Nasc
            self.entry_idade.get(),
            self.entry_queixa.get(),
            self.entry_pa.get(),
            self.entry_temp.get(),
            self.entry_sat.get(),
            self.entry_diag.get(),
            self.entry_conduta.get()
        ]

        if not dados[2]: 
            messagebox.showwarning("Atenção", "O nome do paciente é obrigatório.")
            return

        arquivo_existe = os.path.exists(ARQUIVO_DB)
        with open(ARQUIVO_DB, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            if not arquivo_existe:
                # Cabeçalho atualizado
                writer.writerow(["Reg", "Data/Hora", "Nome", "Data Nasc", "Idade", "Queixa", "PA", "Temp", "Sat", "Diagnóstico", "Conduta"])
            writer.writerow(dados)

        self.atualizar_contador()
        self.limpar_campos()
        messagebox.showinfo("Sucesso", "Ficha salva com sucesso!")

    def limpar_campos(self):
        # Limpa todos os campos para o próximo paciente
        campos = [self.entry_nome, self.entry_nasc, self.entry_idade, self.entry_queixa, 
                  self.entry_pa, self.entry_temp, self.entry_sat, self.entry_diag, self.entry_conduta]
        for campo in campos:
            campo.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = FichaApp(root)
    root.mainloop()
