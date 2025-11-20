# Модуль 2: Движок резолюций для логики предикатов
# Реализует алгоритм резолюций с унификацией для поиска противоречия

import re
from typing import List, Dict, Tuple, Optional


# Клауза (дизъюнкция литералов)
class Clause:
    def __init__(self, literals: List[str]):
        self.literals = literals
        self.normalized = self._normalize()
    
    # Нормализация литералов в формат (is_negated, predicate, args)
    def _normalize(self) -> List[Tuple[bool, str, List[str]]]:
        normalized = []
        for lit in self.literals:
            is_negated = lit.startswith('¬')
            lit_clean = lit.lstrip('¬').strip()
            
            # Парсим предикат и аргументы: Предикат(арг1, арг2) или Предикат(арг1)
            match = re.match(r'(\w+)\((.*?)\)', lit_clean)
            if match:
                pred_name = match.group(1)
                args_str = match.group(2)
                args = [arg.strip() for arg in args_str.split(',')] if args_str else []
                normalized.append((is_negated, pred_name, args))
            else:
                # Если не удалось распарсить, сохраняем как есть
                normalized.append((is_negated, lit_clean, []))
        
        return normalized
    
    def __repr__(self) -> str:
        return ' ∨ '.join(self.literals)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Clause):
            return False
        return set(self.literals) == set(other.literals)
    
    def __hash__(self) -> int:
        return hash(tuple(sorted(self.literals)))


# Подстановка переменных
class Substitution:
    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping
    
    # Применение подстановки к терму
    def apply(self, term: str) -> str:
        if term in self.mapping:
            return self.mapping[term]
        return term
    
    # Композиция подстановок
    def compose(self, other: 'Substitution') -> 'Substitution':
        new_mapping = {}
        # Применяем other к значениям self
        for var, value in self.mapping.items():
            new_mapping[var] = other.apply(value)
        # Добавляем подстановки из other, которых нет в self
        for var, value in other.mapping.items():
            if var not in new_mapping:
                new_mapping[var] = value
        return Substitution(new_mapping)
    
    def __repr__(self) -> str:
        if not self.mapping:
            return "{}"
        return "{" + ", ".join(f"{k}/{v}" for k, v in self.mapping.items()) + "}"


# Унификация двух термов (списков аргументов)
def unify(term1: List[str], term2: List[str], subst: Optional[Substitution] = None) -> Optional[Substitution]:
    if subst is None:
        subst = Substitution({})
    
    if len(term1) != len(term2):
        return None
    
    if not term1:
        return subst
    
    t1, t2 = term1[0], term2[0]
    
    # Если термы одинаковы, продолжаем
    if t1 == t2:
        return unify(term1[1:], term2[1:], subst)
    
    # Если t1 - переменная (простая эвристика: одна буква или x, y, z)
    if _is_variable(t1):
        if t1 in subst.mapping:
            return unify([subst.mapping[t1]] + term1[1:], term2, subst)
        # Проверка на вхождение переменной
        if t2 in subst.mapping.values() or (not _is_variable(t2) and t2 in [s.apply(t1) for s in [subst]]):
            # Упрощенная проверка - в реальности нужна более сложная
            pass
        new_subst = Substitution({t1: t2})
        return unify(term1[1:], term2[1:], subst.compose(new_subst))
    
    # Если t2 - переменная
    if _is_variable(t2):
        return unify(term2, term1, subst)
    
    # Оба - константы, но разные
    return None


# Проверка, является ли терм переменной (простая эвристика: одна буква x, y, z)
def _is_variable(term: str) -> bool:
    return len(term) == 1 and term.islower() and term.isalpha()


# Резолюция двух клауз
def resolve(clause1: Clause, clause2: Clause) -> List[Tuple[Clause, Substitution, str, str]]:
    results = []
    
    for neg1, pred1, args1 in clause1.normalized:
        for neg2, pred2, args2 in clause2.normalized:
            # Ищем комплементарные литералы (один отрицательный, другой нет, одинаковые предикаты)
            if neg1 != neg2 and pred1 == pred2:
                # Пытаемся унифицировать аргументы
                subst = unify(args1, args2)
                if subst is not None:
                    # Создаем новую клаузу без комплементарных литералов
                    new_literals = []
                    
                    # Применяем подстановку и добавляем литералы из clause1 (кроме текущего)
                    for n, p, a in clause1.normalized:
                        if (n, p, a) != (neg1, pred1, args1):
                            applied_args = [subst.apply(arg) for arg in a]
                            if applied_args:
                                lit = ('¬' if n else '') + f"{p}({', '.join(applied_args)})"
                            else:
                                lit = ('¬' if n else '') + p
                            new_literals.append(lit)
                    
                    # Применяем подстановку и добавляем литералы из clause2 (кроме текущего)
                    for n, p, a in clause2.normalized:
                        if (n, p, a) != (neg2, pred2, args2):
                            applied_args = [subst.apply(arg) for arg in a]
                            if applied_args:
                                lit = ('¬' if n else '') + f"{p}({', '.join(applied_args)})"
                            else:
                                lit = ('¬' if n else '') + p
                            new_literals.append(lit)
                    
                    # Удаляем дубликаты
                    new_literals = list(dict.fromkeys(new_literals))
                    
                    if new_literals:
                        new_clause = Clause(new_literals)
                        lit1_str = ('¬' if neg1 else '') + f"{pred1}({', '.join(args1)})"
                        lit2_str = ('¬' if neg2 else '') + f"{pred2}({', '.join(args2)})"
                        results.append((new_clause, subst, lit1_str, lit2_str))
                    else:
                        # Пустая клауза - противоречие найдено!
                        empty_clause = Clause([])
                        lit1_str = ('¬' if neg1 else '') + f"{pred1}({', '.join(args1)})"
                        lit2_str = ('¬' if neg2 else '') + f"{pred2}({', '.join(args2)})"
                        results.append((empty_clause, subst, lit1_str, lit2_str))
    
    return results


# Выполнение алгоритма резолюций для поиска противоречия
def resolution_proof(clauses: List[str]) -> Tuple[bool, List[str]]:
    clause_objects = []
    for clause_str in clauses:
        # Разделяем по ∨ (с учетом пробелов)
        literals = [lit.strip() for lit in re.split(r'\s*∨\s*', clause_str.strip())]
        clause_objects.append(Clause(literals))
    
    log = []
    log.append(f"Начальные клаузы: {len(clause_objects)}")
    
    clause_ids: Dict[Clause, int] = {}
    next_clause_id = 1

    def get_clause_id(clause: Clause) -> int:
        nonlocal next_clause_id
        if clause not in clause_ids:
            clause_ids[clause] = next_clause_id
            next_clause_id += 1
        return clause_ids[clause]

    def clause_to_str(clause: Clause) -> str:
        return str(clause) if clause.literals else "Пустая клауза (⊥)"

    def format_clause(clause: Clause) -> str:
        clause_id = get_clause_id(clause)
        return f"[#{clause_id}] {clause_to_str(clause)}"

    for clause in clause_objects:
        log.append(f"  {format_clause(clause)}")
    
    # Множество всех клауз (для отслеживания уже выведенных)
    all_clauses = set(clause_objects)
    new_clauses = set(clause_objects)
    step_num = 1
    
    max_iterations = 100  # Защита от бесконечного цикла
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        current_new = list(new_clauses)
        new_clauses = set()
        
        # Создаем копию списка всех клауз для итерации (чтобы избежать изменения set во время итерации)
        all_clauses_list = list(all_clauses)
        
        # Пробуем резолвить каждую пару клауз
        for clause1 in all_clauses_list:
            for clause2 in current_new:
                if clause1 == clause2:
                    continue
                
                resolutions = resolve(clause1, clause2)
                
                for new_clause, subst, lit1, lit2 in resolutions:
                    # Проверяем, не пустая ли клауза (противоречие!)
                    if not new_clause.literals:
                        log.append(f"\nШаг {step_num}: Противоречие найдено!")
                        log.append(f"  Клауза 1: {format_clause(clause1)}")
                        log.append(f"  Клауза 2: {format_clause(clause2)}")
                        log.append(f"  Унификация {subst} в литералах '{lit1}' и '{lit2}'")
                        log.append(f"  Результат: {format_clause(new_clause)} (противоречие)")
                        return True, log
                    
                    # Если новая клауза еще не была выведена
                    if new_clause not in all_clauses:
                        all_clauses.add(new_clause)
                        new_clauses.add(new_clause)
                        log.append(f"\nШаг {step_num}: Резолюция")
                        log.append(f"  Клауза 1: {format_clause(clause1)}")
                        log.append(f"  Клауза 2: {format_clause(clause2)}")
                        log.append(f"  Унификация {subst} в литералах '{lit1}' и '{lit2}'")
                        log.append(f"  Результат: {format_clause(new_clause)}")
                        step_num += 1
        
        # Если новых клауз не выведено, противоречия нет
        if not new_clauses:
            log.append(f"\nНе удалось найти противоречие после {step_num-1} шагов.")
            log.append(f"Всего выведено клауз: {len(all_clauses)}")
            return False, log
    
    log.append(f"\nДостигнут лимит итераций ({max_iterations}). Противоречие не найдено.")
    return False, log

