import streamlit as st
import pandas as pd
from typing import List

from .helpers import number_emojis, render_md_bold
from ui.lang import t

def standard_form_ui():
    st.markdown(f"<h1 style='text-align: center;'>{t('standard.title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center;'>
        {render_md_bold(t('standard.subtitle'))}
        <br>
        {render_md_bold(t('standard.subtitle_details'))}
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Configuração Inicial ---
    # Carregar estado ou usar defaults
    saved = st.session_state.get("problem", {})
    sv_c, sv_A, sv_b = saved.get("c", []), saved.get("A", []), saved.get("b", [])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        n_vars = st.number_input(t("simplex.n_vars"), 2, 10, max(len(sv_c), 2), help=t("simplex.vars_help"))
    with col2:
        n_cons = st.number_input(t("simplex.n_cons"), 1, 10, max(len(sv_A), 1), help=t("simplex.cons_help"))
    with col3:
        obj_type = st.selectbox(
            t("simplex.obj_type"), 
            [t("simplex.maximize"), t("simplex.minimize")]
        )

    # --- Inputs ---
    st.markdown(t("sensitivity.func_obj"))
    
    # Variable type options
    type_options = [t("simplex.var_real"), t("simplex.var_integer"), t("simplex.var_binary")]
    saved_var_types = saved.get("var_types", [])
    vt_map = {"real": 0, "integer": 1, "binary": 2}
    
    cols_obj = st.columns(n_vars)
    c = []
    var_types = []
    for i in range(n_vars):
        val = sv_c[i] if i < len(sv_c) else 0.0
        with cols_obj[i]:
            # Default type from saved
            default_type_idx = vt_map.get(saved_var_types[i], 0) if i < len(saved_var_types) else 0
            vtype = st.selectbox(
                f"{t('simplex.var_type')} x{i+1}",
                type_options,
                index=default_type_idx,
                key=f"std_vtype_{i}",
                label_visibility="collapsed"
            )
            var_types.append(vtype)
            
            if vtype == t("simplex.var_binary"):
                c.append(st.number_input(f"**x{i+1}**", min_value=0.0, max_value=1.0, value=min(max(val, 0.0), 1.0), step=1.0, key=f"std_c_{i}", help=f"{t('simplex.coef_help')} x{i+1}"))
            elif vtype == t("simplex.var_integer"):
                c.append(st.number_input(f"**x{i+1}**", value=float(round(val)), step=1.0, key=f"std_c_{i}", help=f"{t('simplex.coef_help')} x{i+1}"))
            else:
                c.append(st.number_input(f"**x{i+1}**", value=val, key=f"std_c_{i}", help=f"{t('simplex.coef_help')} x{i+1}"))

    # Inputs de Restrições
    A = []
    b = []
    senses = []
    
    with st.expander(t("simplex.constraints"), expanded=True):
        for r in range(n_cons):
            st.markdown(f"**{t('common.restriction')} {number_emojis[r+1]}**")
            cols = st.columns(n_vars + 2)
            row = []
            
            # Coeficientes
            for i in range(n_vars):
                def_val = sv_A[r][i] if r < len(sv_A) and i < len(sv_A[r]) else 0.0
                with cols[i]:
                    row.append(st.number_input(f"**x{i+1}**", value=def_val, key=f"std_a_{r}_{i}", label_visibility="collapsed", help=f"{t('simplex.coef_help')} x{i+1}"))
            
            # Tipo
            with cols[n_vars]:
                sense = st.selectbox(t("simplex.type_label"), ["≤", "=", "≥"], key=f"std_sense_{r}", label_visibility="collapsed", help=t("simplex.type_label"))
            
            # RHS
            with cols[n_vars+1]:
                def_rhs = sv_b[r] if r < len(sv_b) else 0.0
                rhs = st.number_input(t("simplex.rhs_label"), value=def_rhs, key=f"std_b_{r}", label_visibility="collapsed", help=t("simplex.rhs_label"))
            
            A.append(row)
            b.append(rhs)
            senses.append(sense)

    st.markdown("---")

    if st.button(t("standard.btn_convert"), type="primary", width="stretch"):
        # --- Lógica de Conversão ---
        new_c = list(c)
        new_A = [row[:] for row in A]
        new_b = list(b)
        new_vars = [f"x_{{{i+1}}}" for i in range(n_vars)]
        steps = []
        conv_senses = list(senses)
        
        # Passo 1: Objetivo
        is_min = (obj_type == t("simplex.minimize"))

        if is_min:
            new_c = [-val for val in new_c]
            steps.append(t("standard.msg.min_to_max"))
        
        # Passo 1.5: Variáveis com domínio não-padrão (do Dual)
        # Processar variáveis livres (y = y⁺ - y⁻) e ≤ 0 (y' = -y)
        dual_domains = saved.get("dual_vars_domain", [])
        if dual_domains:
            # Processar da direita para esquerda para não alterar índices
            for i in range(len(dual_domains) - 1, -1, -1):
                if i >= len(new_c):
                    continue
                    
                dom = dual_domains[i]
                var_name = new_vars[i]
                
                if dom == "Livre":
                    # Variável livre: substituir y_i por y_i⁺ - y_i⁻
                    # Duplicar coluna com sinal invertido
                    pos_name = f"{var_name}^+"
                    neg_name = f"{var_name}^-"
                    
                    # Substituir nome da variável original por y⁺
                    new_vars[i] = pos_name
                    # Inserir y⁻ logo após
                    new_vars.insert(i + 1, neg_name)
                    
                    # Coeficiente na FO: c_i para y⁺, -c_i para y⁻
                    c_val = new_c[i]
                    new_c.insert(i + 1, -c_val)
                    
                    # Nas restrições: a_ij para y⁺, -a_ij para y⁻
                    for row in new_A:
                        if i < len(row):
                            row.insert(i + 1, -row[i])
                        else:
                            row.insert(i + 1, 0.0)
                    
                    steps.append(t("standard.msg.free_var").format(var_name))
                    
                elif dom == "≤ 0":
                    # Variável ≤ 0: substituir y_i por y_i' = -y_i
                    new_vars[i] = f"{var_name}'"
                    
                    # Negar coeficiente na FO
                    new_c[i] = -new_c[i]
                    
                    # Negar coluna nas restrições
                    for row in new_A:
                        if i < len(row):
                            row[i] = -row[i]
                    
                    steps.append(t("standard.msg.neg_var").format(var_name))
        
        # Passo 2: RHS Negativo
        for i in range(n_cons):
            if new_b[i] < 0:
                new_b[i] = -new_b[i]
                new_A[i] = [-val for val in new_A[i]]
                
                # Inverter desigualdade
                if conv_senses[i] == "≤":
                    conv_senses[i] = "≥"
                    steps.append(t("standard.msg.rhs_neg").format(i+1))
                elif conv_senses[i] == "≥":
                    conv_senses[i] = "≤"
                    steps.append(t("standard.msg.rhs_neg").format(i+1))
                else:
                    steps.append(t("standard.msg.rhs_neg_simple").format(i+1))

        # Passo 3: Variáveis de Folga e Excesso
        for i in range(n_cons):
            row = new_A[i]
            
            # Padding para vars já existentes
            while len(row) < len(new_vars):
                row.append(0.0)
                
            if conv_senses[i] == "≤":
                slack_name = f"s_{{{i+1}}}"
                new_vars.append(slack_name)
                
                for r_idx in range(n_cons):
                    if r_idx == i:
                        new_A[r_idx].append(1.0)
                    else:
                        if r_idx < len(new_A):
                            new_A[r_idx].append(0.0)
                
                new_c.append(0.0)
                steps.append(t("standard.msg.slack").format(i+1, slack_name))
                
            elif conv_senses[i] == "≥":
                surplus_name = f"e_{{{i+1}}}"
                new_vars.append(surplus_name)
                
                for r_idx in range(n_cons):
                    if r_idx == i:
                        new_A[r_idx].append(-1.0)
                    else:
                        new_A[r_idx].append(0.0)
                        
                new_c.append(0.0)
                steps.append(t("standard.msg.surplus").format(i+1, surplus_name))
        
        # Salvar resultado no session state para persistência
        st.session_state["std_form_result"] = {
            "new_c": new_c,
            "new_A": new_A,
            "new_b": new_b,
            "new_vars": new_vars,
            "steps": steps,
            "is_min": is_min,
            "c_original": c,
            "A_original": A,
            "b_original": b,
            "senses_original": senses,
            "obj_type": obj_type,
            "n_cons": n_cons,
        }

    # --- Exibição do Resultado (Persistente via session state) ---
    if "std_form_result" in st.session_state:
        res = st.session_state["std_form_result"]
        new_c = res["new_c"]
        new_A = res["new_A"]
        new_b = res["new_b"]
        new_vars = res["new_vars"]
        steps = res["steps"]
        is_min = res["is_min"]
        
        st.divider()
        
        if steps:
            with st.expander(t("standard.details"), expanded=False):
                for step in steps:
                    st.write(step)
        
        # --- Visualização Lado a Lado ---
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader(t("standard.original"))
            
            original_obj_str = " + ".join([f"{val}x_{{{i+1}}}" for i, val in enumerate(res["c_original"])])
            original_obj_str = original_obj_str.replace("+ -", "- ")
            obj_tag = "Max" if res["obj_type"] == t("simplex.maximize") else "Min"
            st.latex(f"\\text{{{obj_tag}}} \\ Z = {original_obj_str}")
            
            st.markdown(t("standard.subject_to"))
            orig_latex_lines = []
            for i in range(res["n_cons"]):
                lhs = " + ".join([f"{res['A_original'][i][j]}x_{{{j+1}}}" for j in range(len(res['c_original']))]).replace("+ -", "- ")
                op = "=" if res['senses_original'][i] == "=" else ("\\le" if res['senses_original'][i] == "≤" else "\\ge")
                orig_latex_lines.append(f"{lhs} {op} {res['b_original'][i]}")
            
            st.latex("\\begin{cases} " + " \\\\ ".join(orig_latex_lines) + " \\\\ x_j \\ge 0 \\end{cases}")

        with c2:
            st.subheader(t("standard.standard"))
            
            std_obj_str = " + ".join([f"{val} {var}" for val, var in zip(new_c, new_vars) if abs(val) > 1e-9])
            if not std_obj_str: std_obj_str = "0"
            std_obj_str = std_obj_str.replace("+ -", "- ")
            
            obj_label = "W" if is_min else "Z"
            st.latex(f"\\text{{Max}} \\ {obj_label} = {std_obj_str}")
            
            st.markdown(t("standard.subject_to"))
            
            std_latex_lines = []
            for i in range(res["n_cons"]):
                current_row = new_A[i]
                while len(current_row) < len(new_vars):
                    current_row.append(0.0)
                    
                lhs_parts = []
                for j, val in enumerate(current_row):
                    if abs(val) > 1e-9:
                        lhs_parts.append(f"{val} {new_vars[j]}")
                
                lhs_std = " + ".join(lhs_parts).replace("+ -", "- ")
                std_latex_lines.append(f"{lhs_std} = {new_b[i]}")
            
            st.latex("\\begin{cases} " + " \\\\ ".join(std_latex_lines) + " \\\\ x_j, s_i, e_i \\ge 0 \\end{cases}")
        
        # --- Botões de Resolução ---
        st.divider()
        st.markdown(t("duality.solve_label"))
        
        # Derive var_types as internal strings
        vt_internal = [("real" if vt == t("simplex.var_real") else "integer" if vt == t("simplex.var_integer") else "binary") for vt in var_types]
        int_var_indices = [i for i, vt in enumerate(vt_internal) if vt in ("integer", "binary")]
        
        std_problem_data = {
            "c": new_c,
            "A": new_A, 
            "b": new_b,
            "maximize": True,
            "int_vars": int_var_indices,
            "var_types": vt_internal
        }
        
        col_simplex, col_bab = st.columns(2)
        with col_simplex:
            if st.button(t("duality.btn_solve_simplex"), type="primary", key="btn_std_solve_simplex"):
                from ui.library_page import load_problem_and_redirect
                load_problem_and_redirect({
                    "title": "Forma Padrão",
                    "target_page": "simplex",
                    "data": std_problem_data
                })
        with col_bab:
            if st.button(t("duality.btn_solve_bb"), type="primary", key="btn_std_solve_bab"):
                from ui.library_page import load_problem_and_redirect
                load_problem_and_redirect({
                    "title": "Forma Padrão",
                    "target_page": "bab",
                    "data": std_problem_data
                })
        
    # --- Rodapé ---
    st.markdown("---")
    st.caption(t("standard.footer"))
