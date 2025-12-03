"""
Multi-Criteria Decision Making (MCDM) Engine

Implements TOPSIS and WSM algorithms for recovery action selection.
Based on research paper: "AI-Driven Self-Healing Cloud Systems" (Arora et al., 2024)

Algorithms:
1. TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
2. WSM (Weighted Sum Model)
3. Entropy-weighted criteria (objective weight calculation)
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class CriteriaType(Enum):
    """Criteria optimization direction."""
    BENEFIT = "benefit"  # Higher is better (e.g., success_rate)
    COST = "cost"       # Lower is better (e.g., execution_time, cost)


@dataclass
class DecisionCriteria:
    """
    Decision criteria for MCDM.

    Attributes:
        name: Criteria name
        weight: Importance weight (0-1, sum to 1)
        type: BENEFIT or COST
        description: Criteria description
    """
    name: str
    weight: float
    type: CriteriaType
    description: str = ""

    def __post_init__(self):
        """Validate criteria."""
        if not 0 <= self.weight <= 1:
            raise ValueError(f"Weight must be between 0 and 1, got {self.weight}")


@dataclass
class RecoveryAction:
    """
    Recovery action with criteria values.

    Attributes:
        action_id: Unique action identifier
        name: Action name
        description: Action description
        criteria_values: Dict mapping criteria name to value
        metadata: Optional metadata
    """
    action_id: str
    name: str
    description: str
    criteria_values: Dict[str, float]
    metadata: Optional[Dict] = None

    def get_value(self, criteria_name: str) -> float:
        """Get criteria value."""
        if criteria_name not in self.criteria_values:
            raise ValueError(f"Criteria '{criteria_name}' not found in action {self.action_id}")
        return self.criteria_values[criteria_name]


class MCDMEngine:
    """
    Multi-Criteria Decision Making Engine.

    Supports:
    - TOPSIS: Best for complex decisions with conflicting criteria
    - WSM: Simple weighted sum, fast computation
    - Entropy weighting: Objective weight calculation from data
    """

    def __init__(
        self,
        criteria: List[DecisionCriteria],
        method: str = "topsis"
    ):
        """
        Initialize MCDM engine.

        Args:
            criteria: List of decision criteria
            method: "topsis" or "wsm"
        """
        self.criteria = {c.name: c for c in criteria}
        self.method = method.lower()

        if self.method not in ["topsis", "wsm"]:
            raise ValueError(f"Unsupported method: {method}. Use 'topsis' or 'wsm'")

        # Validate weights sum to 1
        total_weight = sum(c.weight for c in criteria)
        if not math.isclose(total_weight, 1.0, rel_tol=1e-5):
            raise ValueError(f"Criteria weights must sum to 1, got {total_weight}")

        logger.info(
            "mcdm_engine_initialized",
            method=self.method,
            criteria_count=len(criteria),
            criteria=[c.name for c in criteria]
        )

    def select_best_action(
        self,
        actions: List[RecoveryAction]
    ) -> Tuple[RecoveryAction, float, Dict[str, float]]:
        """
        Select best recovery action using MCDM.

        Args:
            actions: List of candidate recovery actions

        Returns:
            Tuple of (best_action, score, all_scores)
        """
        if not actions:
            raise ValueError("No actions provided")

        if len(actions) == 1:
            return actions[0], 1.0, {actions[0].action_id: 1.0}

        # Validate all actions have required criteria
        for action in actions:
            for criteria_name in self.criteria.keys():
                if criteria_name not in action.criteria_values:
                    raise ValueError(
                        f"Action {action.action_id} missing criteria '{criteria_name}'"
                    )

        # Select method
        if self.method == "topsis":
            scores = self._topsis(actions)
        else:  # wsm
            scores = self._wsm(actions)

        # Find best action
        best_action_id = max(scores, key=scores.get)
        best_action = next(a for a in actions if a.action_id == best_action_id)
        best_score = scores[best_action_id]

        logger.info(
            "best_action_selected",
            method=self.method,
            action_id=best_action_id,
            action_name=best_action.name,
            score=round(best_score, 4),
            total_actions=len(actions)
        )

        return best_action, best_score, scores

    def _topsis(self, actions: List[RecoveryAction]) -> Dict[str, float]:
        """
        TOPSIS algorithm implementation.

        Steps:
        1. Normalize decision matrix
        2. Calculate weighted normalized matrix
        3. Determine ideal best and worst solutions
        4. Calculate distances to ideal solutions
        5. Calculate relative closeness to ideal solution

        Args:
            actions: List of recovery actions

        Returns:
            Dict mapping action_id to TOPSIS score (0-1, higher is better)
        """
        n_actions = len(actions)
        criteria_names = list(self.criteria.keys())

        # Step 1: Build decision matrix
        matrix = []
        for action in actions:
            row = [action.get_value(name) for name in criteria_names]
            matrix.append(row)

        # Step 2: Normalize decision matrix (vector normalization)
        normalized = []
        for j, criteria_name in enumerate(criteria_names):
            # Calculate column sum of squares
            col_sum_sq = sum(matrix[i][j] ** 2 for i in range(n_actions))
            col_norm = math.sqrt(col_sum_sq) if col_sum_sq > 0 else 1.0

            # Normalize column
            for i in range(n_actions):
                if i >= len(normalized):
                    normalized.append([])
                normalized[i].append(matrix[i][j] / col_norm)

        # Step 3: Apply weights
        weighted = []
        for i in range(n_actions):
            row = []
            for j, criteria_name in enumerate(criteria_names):
                weight = self.criteria[criteria_name].weight
                row.append(normalized[i][j] * weight)
            weighted.append(row)

        # Step 4: Determine ideal best and worst solutions
        ideal_best = []
        ideal_worst = []

        for j, criteria_name in enumerate(criteria_names):
            col_values = [weighted[i][j] for i in range(n_actions)]
            criteria_type = self.criteria[criteria_name].type

            if criteria_type == CriteriaType.BENEFIT:
                # For benefit criteria, max is best
                ideal_best.append(max(col_values))
                ideal_worst.append(min(col_values))
            else:  # COST
                # For cost criteria, min is best
                ideal_best.append(min(col_values))
                ideal_worst.append(max(col_values))

        # Step 5: Calculate distances
        distances_best = []
        distances_worst = []

        for i in range(n_actions):
            # Euclidean distance to ideal best
            dist_best = math.sqrt(
                sum((weighted[i][j] - ideal_best[j]) ** 2 for j in range(len(criteria_names)))
            )
            distances_best.append(dist_best)

            # Euclidean distance to ideal worst
            dist_worst = math.sqrt(
                sum((weighted[i][j] - ideal_worst[j]) ** 2 for j in range(len(criteria_names)))
            )
            distances_worst.append(dist_worst)

        # Step 6: Calculate relative closeness
        scores = {}
        for i, action in enumerate(actions):
            # Avoid division by zero
            denominator = distances_best[i] + distances_worst[i]
            if denominator == 0:
                score = 0.5
            else:
                score = distances_worst[i] / denominator

            scores[action.action_id] = score

        return scores

    def _wsm(self, actions: List[RecoveryAction]) -> Dict[str, float]:
        """
        Weighted Sum Model (WSM) implementation.

        Simple additive weighting:
        Score = Σ(weight_i * normalized_value_i)

        Args:
            actions: List of recovery actions

        Returns:
            Dict mapping action_id to WSM score (0-1, higher is better)
        """
        criteria_names = list(self.criteria.keys())

        # Step 1: Find min/max for normalization
        min_values = {}
        max_values = {}

        for criteria_name in criteria_names:
            values = [action.get_value(criteria_name) for action in actions]
            min_values[criteria_name] = min(values)
            max_values[criteria_name] = max(values)

        # Step 2: Calculate weighted scores
        scores = {}

        for action in actions:
            total_score = 0.0

            for criteria_name in criteria_names:
                value = action.get_value(criteria_name)
                criteria = self.criteria[criteria_name]

                # Normalize to [0, 1]
                min_val = min_values[criteria_name]
                max_val = max_values[criteria_name]

                if max_val == min_val:
                    normalized = 0.5  # All same, neutral
                else:
                    if criteria.type == CriteriaType.BENEFIT:
                        # Higher is better
                        normalized = (value - min_val) / (max_val - min_val)
                    else:  # COST
                        # Lower is better (invert)
                        normalized = (max_val - value) / (max_val - min_val)

                # Apply weight
                total_score += criteria.weight * normalized

            scores[action.action_id] = total_score

        return scores

    def calculate_entropy_weights(
        self,
        actions: List[RecoveryAction]
    ) -> Dict[str, float]:
        """
        Calculate objective weights using entropy method.

        Higher entropy = less information = lower weight
        Lower entropy = more information = higher weight

        Args:
            actions: Historical actions for weight calculation

        Returns:
            Dict mapping criteria name to entropy-based weight
        """
        if len(actions) < 2:
            # Not enough data, use equal weights
            n_criteria = len(self.criteria)
            return {name: 1.0 / n_criteria for name in self.criteria.keys()}

        n_actions = len(actions)
        criteria_names = list(self.criteria.keys())

        # Step 1: Normalize decision matrix
        normalized = {}
        for criteria_name in criteria_names:
            values = [action.get_value(criteria_name) for action in actions]
            total = sum(values)

            if total == 0:
                # All zeros, use equal distribution
                normalized[criteria_name] = [1.0 / n_actions] * n_actions
            else:
                normalized[criteria_name] = [v / total for v in values]

        # Step 2: Calculate entropy
        k = 1.0 / math.log(n_actions) if n_actions > 1 else 1.0
        entropy = {}

        for criteria_name in criteria_names:
            e = 0.0
            for p in normalized[criteria_name]:
                if p > 0:
                    e += p * math.log(p)
            entropy[criteria_name] = -k * e

        # Step 3: Calculate diversity (1 - entropy)
        diversity = {name: 1 - entropy[name] for name in criteria_names}

        # Step 4: Calculate weights
        total_diversity = sum(diversity.values())
        if total_diversity == 0:
            # All same diversity, use equal weights
            n = len(criteria_names)
            weights = {name: 1.0 / n for name in criteria_names}
        else:
            weights = {
                name: diversity[name] / total_diversity
                for name in criteria_names
            }

        logger.info(
            "entropy_weights_calculated",
            weights=weights,
            actions_analyzed=n_actions
        )

        return weights

    def explain_decision(
        self,
        action: RecoveryAction,
        score: float,
        all_scores: Dict[str, float],
        all_actions: List[RecoveryAction]
    ) -> Dict[str, any]:
        """
        Generate explanation for decision.

        Args:
            action: Selected action
            score: Action score
            all_scores: All action scores
            all_actions: All candidate actions

        Returns:
            Explanation dictionary
        """
        # Rank actions by score
        ranked = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)

        # Calculate criteria contributions
        criteria_contributions = {}
        for criteria_name, criteria in self.criteria.items():
            value = action.get_value(criteria_name)
            criteria_contributions[criteria_name] = {
                "value": value,
                "weight": criteria.weight,
                "type": criteria.type.value,
                "description": criteria.description
            }

        return {
            "selected_action": {
                "action_id": action.action_id,
                "name": action.name,
                "description": action.description,
                "score": round(score, 4)
            },
            "method": self.method,
            "ranking": [
                {
                    "rank": i + 1,
                    "action_id": action_id,
                    "score": round(score, 4)
                }
                for i, (action_id, score) in enumerate(ranked)
            ],
            "criteria_contributions": criteria_contributions,
            "total_candidates": len(all_actions)
        }

    def get_stats(self) -> Dict[str, any]:
        """Get engine statistics."""
        return {
            "method": self.method,
            "criteria": [
                {
                    "name": c.name,
                    "weight": c.weight,
                    "type": c.type.value,
                    "description": c.description
                }
                for c in self.criteria.values()
            ]
        }
