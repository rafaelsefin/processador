import pandas as pd
import re
import os
import json
import streamlit as st

def processar_extrato_investimentos(input_file):
    base_dir = os.path.dirname(os.path.abspath(input_file))
    output_folder = os.path.join(base_dir, "extrato_tratado")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with open(input_file, "r", encoding="latin-1") as file:
        lines = file.readlines()

    data_dia_a_dia = {
        "Fundo": [],
        "CNPJ": [],
        "Data": [],
        "Histórico": [],
        "Valor": [],
        "Quantidade Cotas": [],
        "Valor Cota": [],
        "Saldo Cotas": []
    }

    fund_patterns = {
        "BB RF CP ABSOLUTO": r"BB RF CP ABSOLUTO - CNPJ: (\d+)",
        "BB RF REF DI TP FI": r"BB RF REF DI TP FI - CNPJ: (\d+)",
        "BB RF SOLIDEZ ABSOL": r"BB RF SOLIDEZ ABSOL - CNPJ: (\d+)"
    }

    current_fund = None
    current_cnpj = None

    for line in lines:
        for fund_name, pattern in fund_patterns.items():
            match = re.search(pattern, line)
            if match:
                current_fund = fund_name
                current_cnpj = match.group(1)
                continue

        if current_fund:
            match = re.match(r"(\d{2}/\d{2}/\d{4})\s+([A-Z ]+)\s+([\d,.]+)?\s+([\d,.]+)?\s+([\d,.]+)?\s+([\d,.]+)?\s+([\d,.]+)?", line)
            if match:
                data_dia_a_dia["Fundo"].append(current_fund)
                data_dia_a_dia["CNPJ"].append(current_cnpj)
                data_dia_a_dia["Data"].append(match.group(1))
                data_dia_a_dia["Histórico"].append(match.group(2))
                data_dia_a_dia["Valor"].append(match.group(3) if match.group(3) else "0")
                data_dia_a_dia["Quantidade Cotas"].append(match.group(4) if match.group(4) else "0")
                data_dia_a_dia["Valor Cota"].append(match.group(5) if match.group(5) else "0")
                data_dia_a_dia["Saldo Cotas"].append(match.group(6) if match.group(6) else "0")

    df_dia_a_dia = pd.DataFrame(data_dia_a_dia)
    output_excel_path = os.path.join(output_folder, "extrato_investimentos_tratado.xlsx")
    with pd.ExcelWriter(output_excel_path) as writer:
        for fund in df_dia_a_dia["Fundo"].unique():
            df_fund = df_dia_a_dia[df_dia_a_dia["Fundo"] == fund]
            sheet_name = fund[:31]
            df_fund.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return output_excel_path

def processar_extrato_conta_corrente(input_file):
    base_dir = os.path.dirname(os.path.abspath(input_file))
    output_folder = os.path.join(base_dir, "extrato_tratado")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    df = pd.read_excel(input_file, engine="openpyxl", header=2)
    df = df.dropna(how="all").reset_index(drop=True)
    df["Data balancete"] = pd.to_datetime(df["Data balancete"], dayfirst=True, errors='coerce')
    df["Data Formatada"] = df["Data balancete"].dt.strftime("%d/%m/%Y")
    df["Valor R$ "] = (
        df["Valor R$ "]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.extract(r'([-+]?[0-9]*\.?[0-9]+)')[0]
        .astype(float)
        .fillna(0)
    )

    if "OBSERVAÇÃO" not in df.columns:
        df["OBSERVAÇÃO"] = ""

    df["Cod. Historico"] = df["Cod. Historico"].astype(str).str.replace("\.0$", "", regex=True).str.strip()
    df = df[~df["Cod. Historico"].isin(["nan", "NaN", "None", "000", "999", "999.0"])]
    output_excel_path = os.path.join(output_folder, "extrato_conta_corrente_tratado.xlsx")
    df.to_excel(output_excel_path, index=False)
    return output_excel_path

st.title("Processador de Extratos Bancários")
input_file_investimentos = st.file_uploader("Faça o upload do extrato de investimentos (TXT)", type=["txt"], key="investimentos")
input_file_conta_corrente = st.file_uploader("Faça o upload do extrato da conta corrente (XLSX)", type=["xlsx"], key="conta_corrente")

if st.button("Iniciar Conversão"):
    if input_file_investimentos:
        temp_path = f"temp_{input_file_investimentos.name}"
        with open(temp_path, "wb") as f:
            f.write(input_file_investimentos.getbuffer())
        excel_path = processar_extrato_investimentos(temp_path)
        st.success(f"Processamento concluído! Arquivo salvo em: {excel_path}")
    
    if input_file_conta_corrente:
        temp_path = f"temp_{input_file_conta_corrente.name}"
        with open(temp_path, "wb") as f:
            f.write(input_file_conta_corrente.getbuffer())
        excel_path = processar_extrato_conta_corrente(temp_path)
        st.success(f"Processamento concluído! Arquivo salvo em: {excel_path}")
