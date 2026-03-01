from typing import List

import streamlit as st
import pandas as pd

from core.simplex_solver import SimplexSolver
from .helpers import number_emojis, render_md_bold
from ui.lang import t

def sensitivity_ui():
    st.markdown(f"<h1 style='text-align: center;'>{t('sensitivity.title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center;'>
        {render_md_bold(t('sensitivity.subtitle'))}
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Carregar estado anterior (se existir) para preencher defaults
    saved = st.session_state.get("problem", {})
    sv_c, sv_A, sv_b = saved.get("c", []), saved.get("A", []), saved.get("b", [])

    # --- Configuração do Layout (Similar ao Simplex) ---
    col_counts = st.columns(3)
    with col_counts[0]:
        n_vars = st.number_input(t("simplex.n_vars"), 2, 10, max(len(sv_c), 2), help=t("simplex.vars_help"))
    with col_counts[1]:
        n_cons = st.number_input(t("simplex.n_cons"), 1, 10, max(len(sv_A), 1), help=t("simplex.cons_help"))
    
    with col_counts[2]:
        maximize = st.selectbox(
            t("simplex.obj_type"), 
            (t("simplex.maximize"), t("simplex.minimize")), 
            index=0 if saved.get("maximize", True) else 1
        )

    is_max = (maximize == t("simplex.maximize"))
    
    # --- Inputs ---
    
    st.markdown(t("sensitivity.func_obj"))
    obj_cols = st.columns(n_vars)
    c: List[float] = []
    for i in range(n_vars):
        default = sv_c[i] if i < len(sv_c) else 10.0
        with obj_cols[i]:
            c.append(st.number_input(f"**x{i+1}**", value=default, key=f"sen_c_{i}", help=f"{t('simplex.coef_help')} x{i+1}"))

    # Restrições em Expander
    with st.expander(t("simplex.constraints"), expanded=True):
        A: List[List[float]] = []
        b: List[float] = []
        senses: List[str] = []
        
        for r in range(n_cons):
            st.markdown(f"**{t('common.restriction')} - {number_emojis[r+1]}:**")
            cols = st.columns(n_vars + 2)
            row = []
            
            for i in range(n_vars):
                default = sv_A[r][i] if r < len(sv_A) and i < len(sv_A[r]) else 1.0
                with cols[i]:
                    row.append(st.number_input(f"**x{i+1}**", value=default, key=f"sen_a_{r}_{i}", help=f"{t('simplex.coef_help')} x{i+1}"))
            
            with cols[n_vars]:
                sense = st.selectbox(t("simplex.type_label"), ["≤", "=", "≥"], key=f"sen_sense_{r}", help=t("simplex.type_label"))
            
            with cols[n_vars+1]:
                rhs_default = sv_b[r] if r < len(sv_b) else 10.0
                rhs = st.number_input(t("simplex.rhs_label"), value=rhs_default, key=f"sen_b_{r}", help=t("simplex.rhs_label"))
            
            A.append(row)
            b.append(rhs)
            senses.append(sense)

    # Botão de Análise
    if st.button(t("sensitivity.btn_analyze"), type="primary", width="stretch"):
        # Conversão Simples para Standard (<=)
        A_conv, b_conv = [], []
        for row, rhs, sn in zip(A, b, senses):
            if sn == "≤":
                A_conv.append(row)
                b_conv.append(rhs)
            elif sn == "≥":
                A_conv.append([-x for x in row])
                b_conv.append(-rhs)
            else: # =
                A_conv.append(row)
                b_conv.append(rhs)
                A_conv.append([-x for x in row])
                b_conv.append(-rhs)

        try:
            solver = SimplexSolver()
            solver.solve(c, A_conv, b_conv, maximize=is_max)
            
            if not solver.optimal:
                st.error(t("sensitivity.error_optimal"))
                return

            analysis = solver.get_sensitivity_analysis()
            
            st.divider()
            st.success(t("sensitivity.success_gen"))
            
            # --- Exibição dos Resultados ---
            
            # 1. Tabela de Coeficientes da Função Objetivo
            st.subheader(t("sensitivity.results.obj_coefs"))
            st.markdown(t("sensitivity.results.obj_desc"))
            
            obj_data = []
            for item in analysis["objective"]:
                obj_data.append({
                    t("sensitivity.table.var"): item["var"],
                    t("sensitivity.table.current"): f"{item['current_cost']:.2f}",
                    t("sensitivity.table.min"): f"{item['min']:.2f}" if isinstance(item['min'], (int, float)) else item['min'],
                    t("sensitivity.table.max"): f"{item['max']:.2f}" if isinstance(item['max'], (int, float)) else item['max'],
                    t("sensitivity.table.status"): item["status"]
                })
            st.dataframe(pd.DataFrame(obj_data), width="stretch", hide_index=True)

            st.write("")
            
            # 2. Tabela de RHS (Shadow Prices)
            st.subheader(t("sensitivity.results.rhs_sens"))
            st.markdown(t("sensitivity.results.rhs_desc"))
            
            rhs_data = []
            for item in analysis["rhs"]:
                rhs_data.append({
                    t("sensitivity.table.restriction"): f"R{item['id']} ({item['type']})",
                    t("sensitivity.table.current"): f"{item['current_value']:.2f}",
                    t("sensitivity.table.shadow_price"): f"{item['shadow_price']:.4f}",
                    t("sensitivity.table.min"): f"{item['min']:.2f}" if isinstance(item['min'], (int, float)) else item['min'],
                    t("sensitivity.table.max"): f"{item['max']:.2f}" if isinstance(item['max'], (int, float)) else item['max']
                })
            
            st.dataframe(pd.DataFrame(rhs_data), width="stretch", hide_index=True)
            
            # Dica visual
            st.info(t("sensitivity.tip"))

        except Exception as e:
            st.error(f"{t('bab.messages.error')} {e}")
            st.exception(e)
