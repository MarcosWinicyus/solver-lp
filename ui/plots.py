from itertools import combinations
from typing import List, Tuple, Optional
from ui.lang import t

import numpy as np
import plotly.graph_objects as go


def _get_hyperplanes(c, A, b):
    """
    Normaliza e prepara os hiperplanos para processamento.
    Retorna coeficientes normalizados para Ax <= b e x >= 0.
    """
    # Adicionar restrições de não-negatividade: -x <= 0 -> x >= 0
    # Formato scipy/math geral: Ax <= b
    # Nossas restrições: A_in x <= b_in
    # Não-negatividade: -I x <= 0
    
    n_vars = len(c)
    A_all = np.array(A)
    b_all = np.array(b)
    
    # Adicionar limites x >= 0 (que é -x <= 0)
    for i in range(n_vars):
        row = np.zeros(n_vars)
        row[i] = -1
        A_all = np.vstack([A_all, row])
        b_all = np.append(b_all, 0)
        
    return A_all, b_all

def find_vertices(A_all, b_all, n_vars):
    """
    Encontra vértices da região factível testando interseções.
    Funciona para n_vars = 2 ou 3.
    """
    vertices = []
    n_constraints = len(b_all)
    
    # Combinar n_vars restrições para achar intersecção
    # C(n_constraints, n_vars)
    for indices in combinations(range(n_constraints), n_vars):
        try:
            A_sub = A_all[list(indices)]
            b_sub = b_all[list(indices)]
            
            # Resolver sistema linear A_sub * x = b_sub
            if np.linalg.det(A_sub) != 0:
                x = np.linalg.solve(A_sub, b_sub)
                
                # Verificar se satisfaz TODAS as outras restrições
                # Tolerância numérica é crucial
                if np.all(np.dot(A_all, x) <= b_all + 1e-6):
                    # Filtrar duplicatas
                    if not any(np.allclose(x, v) for v in vertices):
                        vertices.append(x)
        except np.linalg.LinAlgError:
            continue
            
    return np.array(vertices)

def ordered_polygon_2d(vertices):
    """Ordena vértices 2D angularmente para plotagem correta."""
    if len(vertices) < 3:
        return vertices
    
    # Centroide
    center = vertices.mean(axis=0)
    angles = np.arctan2(vertices[:, 1] - center[1], vertices[:, 0] - center[0])
    sort_order = np.argsort(angles)
    return vertices[sort_order]


def feasible_region_2d(c: List[float], A: List[List[float]], b: List[float], optimal_solution: Optional[List[float]] = None):
    if len(c) != 2:
        return None

    A_all, b_all = _get_hyperplanes(c, A, b)
    vertices = find_vertices(A_all, b_all, 2)
    
    if len(vertices) < 3:
        return None
        
    vertices = ordered_polygon_2d(vertices)
    
    x_plot = np.append(vertices[:, 0], vertices[0, 0])
    y_plot = np.append(vertices[:, 1], vertices[0, 1])

    fig = go.Figure()

    # Preenchimento
    fig.add_trace(go.Scatter(
        x=x_plot, y=y_plot, fill="toself", 
        mode="lines+markers", name=t("tableau.results.feasible_region"),
        line=dict(color='rgba(0, 100, 255, 0.8)', width=2),
        fillcolor='rgba(0, 100, 255, 0.2)',
        marker=dict(size=8, color='blue')
    ))

    # Restrições
    x_min, x_max = np.min(x_plot) - 1, np.max(x_plot) + 1
    y_min, y_max = np.min(y_plot) - 1, np.max(y_plot) + 1
    x_range = np.linspace(x_min, x_max, 100)
    colors = ["red", "green", "orange", "purple", "brown"]
    
    for idx, (a, rhs) in enumerate(zip(A, b)):
        if abs(a[1]) > 1e-6:
            y_line = (rhs - a[0] * x_range) / a[1]
            mask = (y_line >= y_min) & (y_line <= y_max)
            if np.any(mask):
                 fig.add_trace(go.Scatter(
                    x=x_range[mask], y=y_line[mask], mode="lines",
                    name=f"R{idx+1}: {a[0]}x₁ + {a[1]}x₂ ≤ {rhs}",
                    line=dict(color=colors[idx % len(colors)], dash='dash')
                 ))
        elif abs(a[0]) > 1e-6:
            x_val = rhs / a[0]
            if x_min <= x_val <= x_max:
                fig.add_trace(go.Scatter(
                    x=[x_val, x_val], y=[y_min, y_max], mode="lines",
                    name=f"R{idx+1}: {a[0]}x₁ ≤ {rhs}",
                    line=dict(color=colors[idx % len(colors)], dash='dash')
                ))

    # Gradiente (Seta com Annotation)
    center = vertices.mean(axis=0)
    scale = max(x_max - x_min, y_max - y_min) * 0.2
    norm_c = np.linalg.norm(c)
    dx = c[0] * scale / norm_c if norm_c > 0 else 0
    dy = c[1] * scale / norm_c if norm_c > 0 else 0
    
    fig.add_annotation(
        x=center[0] + dx, y=center[1] + dy,
        ax=center[0], ay=center[1],
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=2, arrowsize=1.5, arrowwidth=2,
        arrowcolor="#00CCFF",
        text="Grad Z", font=dict(color="#00CCFF")
    )

    # Ponto Ótimo
    if optimal_solution and len(optimal_solution) >= 2:
        fig.add_trace(go.Scatter(
            x=[optimal_solution[0]], y=[optimal_solution[1]],
            mode="markers", name="Solução Ótima",
            marker=dict(symbol="star", size=20, color="gold", line=dict(color="white", width=1))
        ))

    fig.update_layout(
        xaxis_title="x₁", yaxis_title="x₂",
        showlegend=True, template="plotly_white", height=600
    )
    return fig

def feasible_region_3d(c: List[float], A: List[List[float]], b: List[float], optimal_solution: Optional[List[float]] = None):
    if len(c) != 3:
        return None

    A_all, b_all = _get_hyperplanes(c, A, b)
    vertices = find_vertices(A_all, b_all, 3)
    
    if len(vertices) == 0:
        return None

    fig = go.Figure()
    
    x, y, z = vertices.T
    
    # Mesh 3D com gradiente baseado no valor da FO (frio→quente)
    # Calcular Z = c·x para cada vértice
    c_np = np.array(c)
    z_values = np.array([np.dot(c_np, v) for v in vertices])
    
    if len(vertices) >= 4:
        fig.add_trace(go.Mesh3d(
            x=x, y=y, z=z,
            alphahull=0,
            intensity=z_values,  # Colorir baseado no valor de Z (FO)
            colorscale=[[0, '#0d47a1'], [0.3, '#1976d2'], [0.5, '#4fc3f7'], [0.7, '#ffb74d'], [0.9, '#ff8f00'], [0.95, '#ff6f00'], [1, '#d50000']],  # Vermelho só no ponto mais quente
            opacity=0.7,
            name=t("tableau.results.feasible_region"),
            flatshading=True,
            showscale=True,
            colorbar=dict(title="Z", len=0.5),
            lighting=dict(ambient=0.4, diffuse=0.5, roughness=0.1, specular=1.0, fresnel=1.0)
        ))
    
    # Vértices (Brancos para contraste em Dark Mode)
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(size=4, color='white', opacity=0.9, line=dict(color='black', width=0.5)),
        name='Vértices'
    ))

    # Gradiente Z (Linha + Cone Pequeno) - Azul
    center = vertices.mean(axis=0) if len(vertices) > 0 else np.zeros(3)
    scale = (np.max(vertices) - np.min(vertices)) * 0.3 if len(vertices) > 0 else 1.0
    uvw = np.array(c)
    norm_c = np.linalg.norm(uvw)
    if norm_c > 0:
        uvw = uvw / norm_c * scale
    
    end_point = center + uvw
    
    # Linha da seta
    fig.add_trace(go.Scatter3d(
        x=[center[0], end_point[0]], 
        y=[center[1], end_point[1]], 
        z=[center[2], end_point[2]],
        mode='lines',
        line=dict(color='#00CCFF', width=6),
        name='Gradiente Z'
    ))
    
    # Ponta da seta (Cone pequeno)
    fig.add_trace(go.Cone(
        x=[end_point[0]], y=[end_point[1]], z=[end_point[2]],
        u=[uvw[0]], v=[uvw[1]], w=[uvw[2]],
        showscale=False,
        sizemode="absolute",
        sizeref=0.5, # Bem menor e fixo
        anchor="tip",
        colorscale=[[0, '#00CCFF'], [1, '#00CCFF']],
        hoverinfo="skip"
    ))

    # Ponto Ótimo
    if optimal_solution and len(optimal_solution) >= 3:
        fig.add_trace(go.Scatter3d(
            x=[optimal_solution[0]], y=[optimal_solution[1]], z=[optimal_solution[2]],
            mode="markers", name="Solução Ótima",
            marker=dict(symbol="diamond", size=10, color="gold", line=dict(color="white", width=2))
        ))

    fig.update_layout(
        scene=dict(xaxis_title='x₁', yaxis_title='x₂', zaxis_title='x₃'),
        height=700
    )
    return fig
