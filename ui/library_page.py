import streamlit as st
from typing import Dict, List, Any
from ui.lang import t

def library_page():
    st.markdown(f"<h1 style='text-align: center;'>{t('library.title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"""
    <p style='text-align: center; color: #666;'>
    {t('library.subtitle')}
    </p>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # 1. Carregar textos traduzidos
    problems_text = t("library.problems")
    if isinstance(problems_text, str): # Fallback caso falhe
        problems_text = []
    
    # 2. Definir dados funcionais (invariables)
    # A ordem DEVE corresponder à lista em ui/lang.py
    problems_data_only = [
        # Mix de Produção
        {
            "target_page": "simplex",
            "data": {
                "c": [100.0, 150.0],
                "A": [[2.0, 3.0], [1.0, 0.5]],
                "b": [120.0, 50.0],
                "maximize": True,
                "int_vars": [],
                "var_types": ["real", "real"]
            } 
        },
        # Problema da Dieta
        {
            "target_page": "simplex",
            "data": {
                "c": [2.0, 3.0],
                "A": [[-4.0, -2.0], [-2.0, -5.0]], # Convertido para <= (multiplicado por -1)
                "b": [-20.0, -30.0],
                "maximize": False, # Minimizar
                "int_vars": [],
                "var_types": ["real", "real"]
            }
        },
        # Problema da Mochila
        {
            "target_page": "bab",
            "data": {
                "c": [10.0, 15.0, 20.0, 25.0],
                "A": [[2.0, 4.0, 6.0, 9.0]],
                "b": [15.0],
                "maximize": True,
                "int_vars": [0, 1, 2, 3],
                "var_types": ["integer", "integer", "integer", "integer"]
            }
        },
        # Corte de Estoque
        {
            "target_page": "bab",
            "data": {
                "c": [5.0, 8.0],
                "A": [[1.0, 1.0], [5.0, 9.0]],
                "b": [6.0, 45.0],
                "maximize": True,
                "int_vars": [0, 1],
                "var_types": ["integer", "integer"]
            }
        },
        # Poliedro Distorcido
        {
            "target_page": "simplex",
            "data": {
                "c": [1.0, 1.0, 1.0],
                "A": [
                    [1.0, 1.0, 1.0],  # Teto inclinado
                    [1.0, 0.0, 0.0],  # Parede X
                    [0.0, 1.0, 0.0],  # Parede Y
                    [0.0, 0.0, 1.0],  # Parede Z
                    [1.0, 2.0, 0.0],  # Corte diagonal XY
                    [0.0, 2.0, 1.0]   # Corte diagonal YZ
                ],
                "b": [10.0, 6.0, 6.0, 6.0, 12.0, 12.0],
                "maximize": True,
                "int_vars": [],
                "var_types": ["real", "real", "real"]
            }
        },
        # Seleção de Projetos (Binário)
        {
            "target_page": "bab",
            "data": {
                "c": [8.0, 11.0, 6.0, 4.0],
                "A": [
                    [5.0, 7.0, 4.0, 3.0],   # Orçamento
                    [1.0, 1.0, 0.0, 0.0],    # Equipe A max 1 projeto
                ],
                "b": [14.0, 1.0],
                "maximize": True,
                "int_vars": [0, 1, 2, 3],
                "var_types": ["binary", "binary", "binary", "binary"]
            }
        },
        # Logística Mista (Inteiro + Real)
        {
            "target_page": "bab",
            "data": {
                "c": [10.0, 20.0, 5.0],
                "A": [
                    [1.0, 2.0, 0.5],   # Recurso A
                    [3.0, 1.0, 1.0],   # Recurso B
                ],
                "b": [10.0, 15.0],
                "maximize": True,
                "int_vars": [0, 1],
                "var_types": ["integer", "integer", "real"]
            }
        },
        # Planejamento de Produção com Restrição de Igualdade (Dualidade com var livre)
        {
            "target_page": "duality",
            "data": {
                "c": [5.0, 4.0],
                "A": [
                    [6.0, 4.0],    # Matéria-prima (≤)
                    [1.0, 2.0],    # Horas de trabalho (≤)
                    [1.0, 1.0],    # Demanda exata (=) → gera variável livre no dual
                ],
                "b": [24.0, 6.0, 5.0],
                "maximize": True,
                "int_vars": [],
                "var_types": ["real", "real"],
                "constraint_types": ["≤", "≤", "="]
            }
        }
    ]

    # 3. Mesclar Textos + Dados
    problems = []
    # Garantir que temos textos suficientes, senão usar placeholder ou truncar
    count = min(len(problems_text), len(problems_data_only))
    
    for i in range(count):
        p_txt = problems_text[i]
        p_dat = problems_data_only[i]
        
        # Merge
        merged = {
            "title": p_txt["title"],
            "category": p_txt["category"],
            "description": p_txt["desc"],
            "target_page": p_dat["target_page"],
            "data": p_dat["data"]
        }
        problems.append(merged)

    # CSS para alinhar verticalmente o botão com o expander
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] {
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Renderização dos Cards
    for i, prob in enumerate(problems):
        col_main, col_btn = st.columns([0.85, 0.15])
        
        with col_main:
            with st.expander(f"{prob['title']} — {prob['category']}"):
                
                c_text, c_math = st.columns(2)
                
                with c_text:
                    st.markdown(t("library.description"))
                    st.markdown(prob['description'])
                
                with c_math:
                    st.markdown(t("library.math_model"))
                    
                    # Dados do problema
                    d = prob['data']
                    c = d['c']
                    A = d['A']
                    b = d['b']
                    is_max = d['maximize']
                    
                    # Construção do LaTeX
                    # Função Objetivo
                    obj_str = " + ".join([f"{val}x_{j+1}" for j, val in enumerate(c)])
                    lbl_opt = 'Max' if is_max else 'Min'
                    st.latex(f"{lbl_opt} \ Z = {obj_str}")
                    
                    # Restrições
                    st.markdown(t("library.subject_to"))
                    for r_idx, row in enumerate(A):
                        lhs = " + ".join([f"{val}x_{j+1}" for j, val in enumerate(row)])
                        rhs = b[r_idx]
                        st.latex(f"{lhs} \le {rhs}")
                    
                    st.latex("x_j \ge 0")

        with col_btn:
            if st.button(t("library.btn_load"), key=f"btn_prob_{i}", help=f"{t('library.btn_load')}: {prob['title']}"):
                load_problem_and_redirect(prob)


def load_problem_and_redirect(problem: Dict[str, Any]):
    """Carrega os dados na sessão e redireciona."""
    
    # Salvar dados no formato esperado pelas páginas
    st.session_state["problem"] = problem["data"]
    
    # Agendar redirecionamento para a próxima execução (evita erro de widget instanciado)
    st.session_state["pending_redirect"] = problem["target_page"]
    
    msg = t("library.toast_loaded").format(problem['title'])
    st.toast(msg, icon="✅")
    st.rerun()
