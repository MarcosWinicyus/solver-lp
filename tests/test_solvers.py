"""
Testes unitários para os solvers (SimplexSolver e BranchBoundSolver).
Cobre cenários de variáveis reais, inteiras, binárias e mistas.
"""

import math
import pytest

from core.simplex_solver import SimplexSolver
from core.branch_bound_solver import BranchBoundSolver


# ============================================================
# 1. LP Puro (Todas variáveis Reais) — Simplex
# ============================================================
class TestSimplexPureLP:
    """Testa o SimplexSolver com variáveis contínuas (reais)."""

    def test_mix_producao(self):
        """Mix de Produção: Max 100x1 + 150x2, s.a. 2x1+3x2<=120, x1+0.5x2<=50"""
        solver = SimplexSolver()
        c = [100.0, 150.0]
        A = [[2.0, 3.0], [1.0, 0.5]]
        b = [120.0, 50.0]
        solver.solve(c, A, b, maximize=True)

        assert solver.optimal
        sol, z = solver.get_solution()
        assert z == pytest.approx(6000.0, abs=1.0)

    def test_minimizacao_dieta(self):
        """Problema da Dieta (Min): Min 2x1 + 3x2, s.a. 4x1+2x2>=20, 2x1+5x2>=30"""
        solver = SimplexSolver()
        c = [2.0, 3.0]
        A = [[-4.0, -2.0], [-2.0, -5.0]]
        b = [-20.0, -30.0]
        solver.solve(c, A, b, maximize=False)

        assert solver.optimal
        sol, z = solver.get_solution()
        assert sol is not None
        # Verificar que a solução respeita as restrições
        assert 4 * sol[0] + 2 * sol[1] >= 20.0 - 1e-6
        assert 2 * sol[0] + 5 * sol[1] >= 30.0 - 1e-6

    def test_poliedro_3d(self):
        """Poliedro Distorcido (3 variáveis): Max x1+x2+x3"""
        solver = SimplexSolver()
        c = [1.0, 1.0, 1.0]
        A = [
            [1.0, 1.0, 1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 2.0, 0.0],
            [0.0, 2.0, 1.0],
        ]
        b = [10.0, 6.0, 6.0, 6.0, 12.0, 12.0]
        solver.solve(c, A, b, maximize=True)

        assert solver.optimal
        sol, z = solver.get_solution()
        assert z > 0  # Deve ter valor positivo


# ============================================================
# 2. Inteiro Puro — Branch & Bound
# ============================================================
class TestBranchBoundPureInteger:
    """Testa o BranchBoundSolver com todas variáveis inteiras."""

    def test_corte_estoque(self):
        """Corte de Estoque: Max 5x1+8x2, x1+x2<=6, 5x1+9x2<=45, x1,x2 inteiros"""
        solver = BranchBoundSolver()
        c = [5.0, 8.0]
        A = [[1.0, 1.0], [5.0, 9.0]]
        b = [6.0, 45.0]
        solver.solve(c, A, b, integer_vars=[0, 1])

        assert solver.finished
        assert solver.best_solution is not None
        x1, x2 = solver.best_solution[0], solver.best_solution[1]
        # Verificar integralidade
        assert abs(x1 - round(x1)) < 1e-6
        assert abs(x2 - round(x2)) < 1e-6
        # Verificar factibilidade
        assert x1 + x2 <= 6.0 + 1e-6
        assert 5 * x1 + 9 * x2 <= 45.0 + 1e-6

    def test_mochila(self):
        """Mochila: Max 10x1+15x2+20x3+25x4, 2x1+4x2+6x3+9x4<=15"""
        solver = BranchBoundSolver()
        c = [10.0, 15.0, 20.0, 25.0]
        A = [[2.0, 4.0, 6.0, 9.0]]
        b = [15.0]
        solver.solve(c, A, b, integer_vars=[0, 1, 2, 3])

        assert solver.finished
        assert solver.best_solution is not None
        # Todas devem ser inteiras
        for i in range(4):
            assert abs(solver.best_solution[i] - round(solver.best_solution[i])) < 1e-6
        # Restrição de peso
        peso = sum(
            solver.best_solution[i] * [2, 4, 6, 9][i] for i in range(4)
        )
        assert peso <= 15.0 + 1e-6


# ============================================================
# 3. Binário — Branch & Bound
# ============================================================
class TestBranchBoundBinary:
    """Testa B&B com variáveis binárias (0 ou 1)."""

    def test_selecao_projetos(self):
        """Seleção de Projetos: Max 8x1+11x2+6x3+4x4, 
        5x1+7x2+4x3+3x4<=14, x1+x2<=1, xi in {0,1}"""
        solver = BranchBoundSolver()
        c = [8.0, 11.0, 6.0, 4.0]
        A = [
            [5.0, 7.0, 4.0, 3.0],  # Orçamento
            [1.0, 1.0, 0.0, 0.0],  # Equipe A max 1
            # Upper bounds para variáveis binárias
            [1.0, 0.0, 0.0, 0.0],  # x1 <= 1
            [0.0, 1.0, 0.0, 0.0],  # x2 <= 1
            [0.0, 0.0, 1.0, 0.0],  # x3 <= 1
            [0.0, 0.0, 0.0, 1.0],  # x4 <= 1
        ]
        b = [14.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        solver.solve(c, A, b, integer_vars=[0, 1, 2, 3])

        assert solver.finished
        assert solver.best_solution is not None
        # Todas devem ser 0 ou 1
        for i in range(4):
            val = solver.best_solution[i]
            assert abs(val) < 1e-6 or abs(val - 1.0) < 1e-6, f"x{i+1}={val} não é binário"
        # Verificar orçamento
        custo = sum(solver.best_solution[i] * [5, 7, 4, 3][i] for i in range(4))
        assert custo <= 14.0 + 1e-6


# ============================================================
# 4. Misto (Inteiro + Real) — Branch & Bound
# ============================================================
class TestBranchBoundMixed:
    """Testa B&B com variáveis mistas (inteiras + reais)."""

    def test_logistica_mista(self):
        """Logística Mista: Max 10x1+20x2+5x3
        x1+2x2+0.5x3<=10, 3x1+x2+x3<=15
        x1,x2 inteiros, x3 real"""
        solver = BranchBoundSolver()
        c = [10.0, 20.0, 5.0]
        A = [
            [1.0, 2.0, 0.5],
            [3.0, 1.0, 1.0],
        ]
        b = [10.0, 15.0]
        # Apenas x1 e x2 são inteiras, x3 é real
        solver.solve(c, A, b, integer_vars=[0, 1])

        assert solver.finished
        assert solver.best_solution is not None
        x1, x2, x3 = (
            solver.best_solution[0],
            solver.best_solution[1],
            solver.best_solution[2],
        )
        # x1 e x2 devem ser inteiros
        assert abs(x1 - round(x1)) < 1e-6, f"x1={x1} deveria ser inteiro"
        assert abs(x2 - round(x2)) < 1e-6, f"x2={x2} deveria ser inteiro"
        # x3 pode ser fracionário — sem restrição de integralidade
        # Verificar factibilidade
        assert x1 + 2 * x2 + 0.5 * x3 <= 10.0 + 1e-6
        assert 3 * x1 + x2 + x3 <= 15.0 + 1e-6

    def test_misto_todas_reais_sem_branch(self):
        """Se int_vars=[], B&B deve encontrar a solução LP sem branching."""
        solver = BranchBoundSolver()
        c = [3.0, 5.0]
        A = [[1.0, 0.0], [0.0, 2.0], [3.0, 2.0]]
        b = [4.0, 12.0, 18.0]
        solver.solve(c, A, b, integer_vars=[])

        assert solver.finished
        assert solver.best_solution is not None
        # Sem branching, deve terminar na raiz
        assert len(solver.nodes) == 1, "Sem variáveis inteiras, não deveria ter branching"


# ============================================================
# 5. Problemas da Biblioteca — Validação completa
# ============================================================
class TestLibraryProblems:
    """Valida que todos os problemas da biblioteca produzem soluções válidas."""

    def _solve_problem(self, c, A, b, maximize, int_vars):
        """Helper: resolve um problema usando o solver apropriado."""
        if int_vars:
            solver = BranchBoundSolver()
            # Converter para <= se necessário
            A_conv, b_conv = [], []
            for row, rhs in zip(A, b):
                A_conv.append(row)
                b_conv.append(rhs)
            
            # Para maximização, B&B já lida internamente
            final_c = list(c)
            if not maximize:
                final_c = [-x for x in c]
            
            solver.solve(final_c, A_conv, b_conv, integer_vars=int_vars)
            return solver.finished, solver.best_solution, solver.best_value
        else:
            solver = SimplexSolver()
            solver.solve(c, A, b, maximize=maximize)
            if solver.optimal:
                sol, z = solver.get_solution()
                return True, sol, z
            return False, None, None

    def test_mix_producao(self):
        ok, sol, z = self._solve_problem(
            [100.0, 150.0], [[2.0, 3.0], [1.0, 0.5]], [120.0, 50.0],
            maximize=True, int_vars=[]
        )
        assert ok and sol is not None

    def test_dieta(self):
        ok, sol, z = self._solve_problem(
            [2.0, 3.0], [[-4.0, -2.0], [-2.0, -5.0]], [-20.0, -30.0],
            maximize=False, int_vars=[]
        )
        assert ok and sol is not None

    def test_mochila(self):
        ok, sol, z = self._solve_problem(
            [10.0, 15.0, 20.0, 25.0], [[2.0, 4.0, 6.0, 9.0]], [15.0],
            maximize=True, int_vars=[0, 1, 2, 3]
        )
        assert ok and sol is not None

    def test_corte_estoque(self):
        ok, sol, z = self._solve_problem(
            [5.0, 8.0], [[1.0, 1.0], [5.0, 9.0]], [6.0, 45.0],
            maximize=True, int_vars=[0, 1]
        )
        assert ok and sol is not None

    def test_poliedro_3d(self):
        ok, sol, z = self._solve_problem(
            [1.0, 1.0, 1.0],
            [[1, 1, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 2, 0], [0, 2, 1]],
            [10.0, 6.0, 6.0, 6.0, 12.0, 12.0],
            maximize=True, int_vars=[]
        )
        assert ok and sol is not None

    def test_selecao_projetos_binario(self):
        ok, sol, z = self._solve_problem(
            [8.0, 11.0, 6.0, 4.0],
            [
                [5.0, 7.0, 4.0, 3.0],
                [1.0, 1.0, 0.0, 0.0],
            ],
            [14.0, 1.0],
            maximize=True, int_vars=[0, 1, 2, 3]
        )
        assert ok and sol is not None

    def test_logistica_mista(self):
        ok, sol, z = self._solve_problem(
            [10.0, 20.0, 5.0],
            [[1.0, 2.0, 0.5], [3.0, 1.0, 1.0]],
            [10.0, 15.0],
            maximize=True, int_vars=[0, 1]
        )
        assert ok and sol is not None
