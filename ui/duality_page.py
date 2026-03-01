
import streamlit as st
import numpy as np
import pandas as pd
from ui.library_page import load_problem_and_redirect
from ui.lang import t

def duality_ui():
    st.markdown(f"<h1 style='text-align: center;'>{t('duality.title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center;'>
        {t('duality.subtitle')}<br>
        {t('duality.theorem')}
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Configuração do Primal ---
    st.subheader(t("duality.primal_def"))

    # Carregar estado ou usar defaults
    saved = st.session_state.get("problem", {})
    sv_c, sv_A, sv_b = saved.get("c", []), saved.get("A", []), saved.get("b", [])
    
    col_counts = st.columns(3)
    with col_counts[0]:
        n_vars = st.number_input(t("simplex.n_vars"), 2, 10, max(len(sv_c), 2), help=t("simplex.vars_help"))
    with col_counts[1]:
        n_constr = st.number_input(t("simplex.n_cons"), 1, 10, max(len(sv_A), 2), help=t("simplex.cons_help"))
    
    with col_counts[2]:
        maximize = st.selectbox(
            t("simplex.obj_type"),
            (t("simplex.maximize"), t("simplex.minimize")),
            index=0 if saved.get("maximize", True) else 1,
            help=t("simplex.obj_help")
        )
    is_max = (maximize == t("simplex.maximize"))

    st.markdown(f"#### {t('simplex.obj_func')} ($Z$)")
    cols_c = st.columns(n_vars)
    c = []
    for i in range(n_vars):
        with cols_c[i]:
            val_def = sv_c[i] if i < len(sv_c) else 1.0
            val = st.number_input(f"**x{i+1}**", value=val_def, key=f"p_c_{i}")
            c.append(val)

    st.markdown(f"#### {t('simplex.constraints')}")
    A = []
    b = []
    senses = []
    
    for r in range(n_constr):
        st.markdown(f"**{t('common.restriction')} {r+1}:**")
        cols = st.columns(n_vars + 2)
        row = []
        for j in range(n_vars):
            with cols[j]:
                val_def = sv_A[r][j] if r < len(sv_A) and j < len(sv_A[r]) else 1.0
                val = st.number_input(f"**x{j+1}**", value=val_def, key=f"p_a_{r}_{j}", help=f"{t('simplex.coef_help')} x{j+1}")
                row.append(val)
        
        with cols[n_vars]:
            sense = st.selectbox(t("simplex.type_label"), ["≤", "=", "≥"], index=0, key=f"p_sense_{r}")
            senses.append(sense)
            
        with cols[n_vars+1]:
            val_b_def = sv_b[r] if r < len(sv_b) else 10.0
            val_b = st.number_input(t("simplex.rhs_label"), value=val_b_def, key=f"p_b_{r}")
            b.append(val_b)
        A.append(row)

    # --- Conversão ---
    if st.button(t("duality.btn_convert"), type="primary"):
        # Lógica de processamento
        n_vars_dual = n_constr
        n_constr_dual = n_vars
        
        A_np = np.array(A)
        b_np = np.array(b)
        c_np = np.array(c)
        
        A_dual = A_np.T.tolist()
        c_dual = b_np.tolist() 
        b_dual = c_np.tolist()
        
        dual_is_max = not is_max
        objective_name = "Min" if not dual_is_max else "Max"
        
        dual_sense_default = "≥" if is_max else "≤"
        
        dual_vars_domain = []
        for s in senses:
            if is_max:
                if s == "≤": domain = "≥ 0"
                elif s == "≥": domain = "≤ 0"
                else: domain = "Livre"
            else:
                if s == "≥": domain = "≥ 0"
                elif s == "≤": domain = "≤ 0"
                else: domain = "Livre"
            dual_vars_domain.append(domain)
            
        # Salvar no session state para persistencia
        st.session_state["dual_result"] = {
            "n_vars_dual": n_vars_dual,
            "n_constr_dual": n_constr_dual,
            "c_dual": c_dual,
            "A_dual": A_dual,
            "b_dual": b_dual,
            "is_max": is_max,
            "dual_is_max": dual_is_max,
            "objective_name": objective_name,
            "dual_sense_default": dual_sense_default,
            "dual_vars_domain": dual_vars_domain,
            "c_original": c,
            "A_original": A,
            "b_original": b,
            "senses_original": senses
        }

    # --- Exibição do Resultado (Persistente) ---
    if "dual_result" in st.session_state:
        res = st.session_state["dual_result"]
        
        st.divider()
        st.subheader(t("duality.result_title"))
        
        col_primal, col_dual = st.columns(2)
        
        with col_primal:
            st.markdown(f"##### {t('duality.primal')}")
            lbl_primal = 'Max' if res['is_max'] else 'Min'
            st.latex(f"{lbl_primal} \ Z = " + " + ".join([f"{val}x_{i+1}" for i, val in enumerate(res['c_original'])]))
            
            st.markdown(t("library.subject_to"))
            for i in range(len(res["A_original"])):
                lhs = " + ".join([f"{res['A_original'][i][j]}x_{j+1}" for j in range(len(res['c_original']))])
                st.latex(f"{lhs} \ {res['senses_original'][i]} \ {res['b_original'][i]}")
            st.latex("x_j \ge 0")
            
            st.divider()
            st.markdown(t("duality.solve_label"))
            
            primal_problem_data = {
                "c": res['c_original'],
                "A": res['A_original'], 
                "b": res['b_original'],
                "maximize": res['is_max'],
                "int_vars": [],
                "constraint_types": res['senses_original']
            }
            
            if st.button(t("duality.btn_solve_simplex"), type="primary", key="btn_solve_primal_simplex"):
                load_problem_and_redirect({
                    "title": "Problema Primal",
                    "target_page": "simplex",
                    "data": primal_problem_data
                })
                
        with col_dual:
            st.markdown(f"##### {t('duality.dual')}")
            desig = res['dual_sense_default']
            
            lbl_dual = 'Max' if res['dual_is_max'] else 'Min'
            st.latex(f"{lbl_dual} \ W = " + " + ".join([f"{val}y_{i+1}" for i, val in enumerate(res['c_dual'])]))
            
            st.markdown(t("library.subject_to"))
            for i in range(res["n_constr_dual"]):
                lhs = " + ".join([f"{res['A_dual'][i][j]}y_{j+1}" for j in range(res["n_vars_dual"])])
                st.latex(f"{lhs} \ {desig} \ {res['b_dual'][i]}")
            
            st.markdown(t("duality.domain"))
            for i, dom in enumerate(res['dual_vars_domain']):
                st.markdown(f"$y_{i+1}$: {dom}")
            
            st.divider()
            st.markdown(t("duality.solve_label"))
            
            # Preparar dados para solver
            dual_problem_data = {
                "c": res['c_dual'],
                "A": res['A_dual'], 
                "b": res['b_dual'],
                "maximize": res['dual_is_max'],
                "int_vars": [],
                "constraint_types": [res['dual_sense_default']] * res["n_constr_dual"]
            }
            
            if st.button(t("duality.btn_solve_simplex"), type="primary", key="btn_solve_dual_simplex"):
                load_problem_and_redirect({
                    "title": "Problema Dual", # This title is internal
                    "target_page": "simplex",
                    "data": dual_problem_data
                })
