"""Model adapter for converting between database and API models"""
from app.models.database import DeepSkyObject, ObservationalInfo
from app.models.target import DeepSkyTarget

class ModelAdapter:
    """Adapter to convert DeepSkyObject to DeepSkyTarget"""

    def to_target(self, obj: DeepSkyObject) -> DeepSkyTarget:
        """
        Convert database model to API model

        Maps fields:
        - type: GALAXY -> galaxy, NEBULA -> emission-nebula, etc.
        - size: size_major (or average of major/minor)
        - difficulty: EASY -> 1, MODERATE -> 2, DIFFICULT -> 3
        - magnitude: None -> 99.0 (very faint)
        - name_en: fallback to name if not available
        """
        # Calculate size (use major axis, or average if both exist)
        size = self._calculate_size(obj.size_major, obj.size_minor)

        # Map magnitude (default to very faint if missing)
        magnitude = obj.magnitude if obj.magnitude is not None else 99.0

        # Map difficulty from observational info
        difficulty = 3  # Default to DIFFICULT
        if obj.observational_info:
            difficulty = self._map_difficulty(obj.observational_info.difficulty)

        # Extract English name from aliases or use name
        name_en = obj.name
        # Try to find an English alias (prefer multi-word names over catalog numbers)
        for alias in obj.aliases:
            # Skip catalog designations (M, NGC, IC, etc.)
            if alias[0].isalpha() and not any(alias.startswith(prefix) for prefix in ['M', 'NGC', 'IC', 'PGC']):
                # Prefer multi-word names (likely English names)
                if ' ' in alias:
                    name_en = alias
                    break
        # If no multi-word English name found, use the original name

        return DeepSkyTarget(
            id=obj.id,
            name=obj.name,
            name_en=name_en,
            type=self._normalize_type(obj.type),
            ra=obj.ra,
            dec=obj.dec,
            magnitude=magnitude,
            size=size,
            constellation=obj.constellation or "Unknown",
            difficulty=difficulty,
            description=self._generate_description(obj),
            optimal_season=self._infer_seasons(obj.observational_info),
            optimal_fov=self._calculate_optimal_fov(size),
            tags=self._generate_tags(obj)
        )

    def _calculate_size(self, major: float = None, minor: float = None) -> float:
        """Calculate size from major/minor axes"""
        if major is None and minor is None:
            return 10.0  # Default size
        if major is not None and minor is not None:
            return (major + minor) / 2  # Average both axes
        return major or minor or 10.0

    def _normalize_type(self, db_type: str) -> str:
        """Normalize database type to API type enum"""
        type_map = {
            "GALAXY": "galaxy",
            "NEBULA": "emission-nebula",
            "CLUSTER": "cluster",
            "PLANETARY": "planetary-nebula",
            "STAR": "cluster"  # Treat stars as clusters for now
        }
        return type_map.get(db_type, "galaxy")  # Default to galaxy

    def _map_difficulty(self, difficulty: str = None) -> int:
        """Map difficulty string to integer (1-5)"""
        diff_map = {
            "EASY": 1,
            "MODERATE": 2,
            "DIFFICULT": 3
        }
        return diff_map.get(difficulty, 3)

    def _generate_description(self, obj: DeepSkyObject) -> str:
        """Generate description from object data"""
        desc = f"{obj.name} is a {obj.type.lower()}"
        if obj.constellation:
            desc += f" in {obj.constellation}"
        if obj.observational_info and obj.observational_info.notes:
            desc += f". {obj.observational_info.notes}"
        return desc

    def _infer_seasons(self, obs_info: ObservationalInfo = None) -> list:
        """Infer optimal seasons from best_month"""
        if not obs_info or not obs_info.best_month:
            return ["October", "November", "December"]  # Default

        month = obs_info.best_month
        # Map month to optimal season
        season_map = {
            1: ["December", "January", "February"],
            2: ["December", "January", "February"],
            3: ["February", "March", "April"],
            4: ["March", "April", "May"],
            5: ["April", "May", "June"],
            6: ["May", "June", "July"],
            7: ["June", "July", "August"],
            8: ["July", "August", "September"],
            9: ["August", "September", "October"],
            10: ["September", "October", "November"],
            11: ["October", "November", "December"],
            12: ["November", "December", "January"]
        }
        return season_map.get(month, ["October", "November", "December"])

    def _calculate_optimal_fov(self, size: float) -> dict:
        """Calculate optimal FOV based on object size"""
        # FOV should be 2-5x the object size
        min_fov = max(50, int(size * 2))
        max_fov = max(100, int(size * 5))
        return {"min": min_fov, "max": max_fov}

    def _generate_tags(self, obj: DeepSkyObject) -> list:
        """Generate tags from object properties"""
        tags = []

        # Type-based tags
        type_tags = {
            "GALAXY": ["galaxy"],
            "NEBULA": ["nebula", "emission"],
            "CLUSTER": ["cluster"],
            "PLANETARY": ["planetary-nebula"]
        }
        tags.extend(type_tags.get(obj.type, []))

        # Size-based tags
        if obj.size_major:
            if obj.size_major > 100:
                tags.append("large")
            elif obj.size_major < 10:
                tags.append("small")

        # Brightness-based tags
        if obj.magnitude:
            if obj.magnitude < 6:
                tags.append("bright")
                tags.append("naked-eye")
            elif obj.magnitude < 10:
                tags.append("moderate")

        # Difficulty tags
        if obj.observational_info:
            if obj.observational_info.difficulty == "EASY":
                tags.append("beginner-friendly")

        return tags
