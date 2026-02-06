import pickle
from pathlib import Path
from typing import Optional

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config import get_settings
from app.logger import logger


class ModelLoader:
    """
    Singleton model loader.
    Loads ML models once and caches them in memory.

    This prevents reloading models on every request (expensive).
    """

    _instance: Optional["ModelLoader"] = None
    _model: Optional[IsolationForest] = None
    _scaler: Optional[StandardScaler] = None
    _loaded_version: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_models(self, force_reload: bool = False) -> tuple[IsolationForest, StandardScaler]:
        """
        Load model and scaler from disk (cached).

        Args:
            force_reload: Force reload even if already loaded

        Returns:
            (model, scaler) tuple
        """
        settings = get_settings()

        # Return cached if available
        if not force_reload and self._model is not None and self._scaler is not None:
            if self._loaded_version == settings.model_version:
                logger.debug(f"Using cached model {self._loaded_version}")
                return self._model, self._scaler

        # Load from disk
        model_path = settings.model_dir / f"anomaly_model_{settings.model_version}.pkl"
        scaler_path = settings.model_dir / f"scaler_{settings.model_version}.pkl"

        if not model_path.exists() or not scaler_path.exists():
            raise FileNotFoundError(
                f"Model files not found. Run: poetry run python scripts/train_model.py"
            )

        logger.info(f"Loading model {settings.model_version} from disk")

        with open(model_path, "rb") as f:
            self._model = pickle.load(f)

        with open(scaler_path, "rb") as f:
            self._scaler = pickle.load(f)

        self._loaded_version = settings.model_version
        logger.info("Models loaded successfully")

        return self._model, self._scaler

    def is_loaded(self) -> bool:
        """Check if models are loaded"""
        return self._model is not None and self._scaler is not None


# Global instance
model_loader = ModelLoader()
