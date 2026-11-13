import os
import re
from pathlib import Path
from typing import Optional, List, Tuple

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "rbac_model.conf"
POLICY_PATH = BASE_DIR / "policy.csv"


class Role:
    VISITEUR = "Visiteur"
    CANDIDAT = "Candidat"
    ENSEIGNANT = "Enseignant"
    ADMINISTRATEUR = "Administrateur"

    @classmethod
    def normalize(cls, role: Optional[str]) -> str:
        if not role:
            return cls.VISITEUR
        r = role.strip().lower()
        if r in ("v", "visiteur"):
            return cls.VISITEUR
        if r in ("c", "candidat"):
            return cls.CANDIDAT
        if r in ("e", "enseignant"):
            return cls.ENSEIGNANT
        if r in ("a", "administrateur", "admin"):
            return cls.ADMINISTRATEUR
        return role.capitalize()


class RBACEnforcer:
    """
    Gestionnaire RBAC pour SmartCampus AI.
    Supporte les rôles en clair : Visiteur, Candidat, Enseignant, Administrateur.
    Supporte Casbin natif si installé, avec un moteur de secours intégré
    conforme à la spécification (g(r.sub, p.sub) && keyMatch2 && regexMatch).
    """
    def __init__(self, model_path: Path = MODEL_PATH, policy_path: Path = POLICY_PATH):
        self.model_path = model_path
        self.policy_path = policy_path
        self._casbin_enforcer = None
        self._rules: List[Tuple[str, str, str]] = []
        self._role_hierarchy = {
            Role.CANDIDAT: [Role.VISITEUR],
            Role.ENSEIGNANT: [],
            Role.ADMINISTRATEUR: [Role.ENSEIGNANT, Role.CANDIDAT, Role.VISITEUR],
            Role.VISITEUR: []
        }

        # Tentative d'initialiser Casbin officiel si la lib est présente
        try:
            import casbin
            if model_path.exists() and policy_path.exists():
                self._casbin_enforcer = casbin.Enforcer(str(model_path), str(policy_path))
        except Exception:
            self._casbin_enforcer = None

        # Chargement des règles pour le fallback
        self._load_fallback_policies()

    def _load_fallback_policies(self):
        if not self.policy_path.exists():
            return
        with open(self.policy_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if parts[0] == "p" and len(parts) >= 4:
                    self._rules.append((Role.normalize(parts[1]), parts[2], parts[3]))
                elif parts[0] == "g" and len(parts) >= 3:
                    role_child = Role.normalize(parts[1])
                    role_parent = Role.normalize(parts[2])
                    self._role_hierarchy.setdefault(role_child, []).append(role_parent)

    def _has_role(self, user_role: str, target_role: str) -> bool:
        u_norm = Role.normalize(user_role)
        t_norm = Role.normalize(target_role)
        if u_norm == t_norm:
            return True
        for parent in self._role_hierarchy.get(u_norm, []):
            if self._has_role(parent, t_norm):
                return True
        return False

    def _match_path(self, pattern: str, path: str) -> bool:
        regex_pattern = "^" + pattern.replace("*", ".*").replace(":id", "[^/]+").replace(":msgId", "[^/]+") + "$"
        return bool(re.match(regex_pattern, path))

    def _match_action(self, pattern: str, act: str) -> bool:
        return bool(re.match(f"^({pattern})$", act, re.IGNORECASE))

    def enforce(self, sub_role: str, obj_path: str, act: str) -> bool:
        """
        Vérifie si le rôle (Visiteur, Candidat, Enseignant, Administrateur)
        a le droit d'effectuer act (GET, POST, etc.) sur obj_path (/api/v1/...).
        """
        norm_sub = Role.normalize(sub_role)
        if norm_sub == Role.ADMINISTRATEUR:
            return True  # L'administrateur unifié a accès universel

        if self._casbin_enforcer:
            try:
                # Teste avec le rôle en clair ou normalisé
                if self._casbin_enforcer.enforce(norm_sub, obj_path, act):
                    return True
                if self._casbin_enforcer.enforce(sub_role, obj_path, act):
                    return True
            except Exception:
                pass

        # Fallback intégré
        for rule_sub, rule_obj, rule_act in self._rules:
            if self._has_role(norm_sub, rule_sub):
                if self._match_path(rule_obj, obj_path) and self._match_action(rule_act, act):
                    return True
        return False


enforcer = RBACEnforcer()
