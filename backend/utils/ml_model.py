from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import Dict, Tuple, Optional

from config import settings
from utils.logger import logger
from utils.preprocess import preprocessor

class MLModel:
    """Machine learning model for priority prediction"""

    FEATURE_NAMES = preprocessor.get_feature_names()

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = None
        self.best_params = None
        self.model_type = "random_forest"

    def prepare_features(self, df: pd.DataFrame, fit_scaler: bool = True) -> np.ndarray:
        """Extract and scale features from dataframe"""
        logger.info("Preparing features for ML")

        # Ensure all required feature columns exist
        missing_features = set(self.FEATURE_NAMES) - set(df.columns)
        if missing_features:
            raise ValueError(f"Missing features: {missing_features}")

        X = df[self.FEATURE_NAMES].values

        if fit_scaler:
            X_scaled = self.scaler.fit_transform(X)
            logger.info(f"Fitted scaler. Shape: {X_scaled.shape}")
        else:
            X_scaled = self.scaler.transform(X)

        return X_scaled

    def train(self, df: pd.DataFrame, model_type: str = "random_forest", tune_hyperparams: bool = False):
        """Train ML model on provided data"""
        logger.info(f"Training {model_type} model")
        self.model_type = model_type

        # Prepare features and labels
        X = self.prepare_features(df, fit_scaler=True)
        y = df['is_urgent'].values

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y,
            test_size=settings.test_size,
            random_state=settings.random_state,
            stratify=y
        )

        logger.info(f"Train size: {len(X_train)}, Val size: {len(X_val)}")
        logger.info(f"Class distribution - Train: {np.bincount(y_train)}, Val: {np.bincount(y_val)}")

        # Select model
        if model_type == "logistic_regression":
            model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=settings.random_state)
            param_grid = {'C': [0.1, 1, 10]} if tune_hyperparams else None

        elif model_type == "random_forest":
            model = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                class_weight='balanced',
                random_state=settings.random_state,
                n_jobs=-1
            )
            param_grid = {
                'n_estimators': [100, 200],
                'max_depth': [5, 10, 15]
            } if tune_hyperparams else None

        elif model_type == "gradient_boosting":
            model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                random_state=settings.random_state
            )
            param_grid = {
                'n_estimators': [100, 150],
                'learning_rate': [0.05, 0.1]
            } if tune_hyperparams else None

        elif model_type == "svm":
            model = SVC(probability=True, class_weight='balanced', random_state=settings.random_state)
            param_grid = {'C': [1, 10], 'kernel': ['rbf', 'linear']} if tune_hyperparams else None

        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Hyperparameter tuning if requested
        if tune_hyperparams and param_grid:
            logger.info("Starting hyperparameter tuning")
            grid_search = GridSearchCV(
                model, param_grid,
                cv=3,
                scoring='f1',
                n_jobs=-1,
                verbose=1
            )
            grid_search.fit(X_train, y_train)
            model = grid_search.best_estimator_
            self.best_params = grid_search.best_params_
            logger.info(f"Best params: {self.best_params}")
        else:
            model.fit(X_train, y_train)

        self.model = model

        # Evaluate
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)

        train_metrics = self._compute_metrics(y_train, train_pred)
        val_metrics = self._compute_metrics(y_val, val_pred)

        logger.info(f"Training metrics: {train_metrics}")
        logger.info(f"Validation metrics: {val_metrics}")

        # Feature importance
        if hasattr(model, 'feature_importances_'):
            self.feature_importance = dict(zip(self.FEATURE_NAMES, model.feature_importances_))
            logger.info(f"Top features: {sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]}")

        return {
            'train_metrics': train_metrics,
            'val_metrics': val_metrics,
            'feature_importance': self.feature_importance,
            'best_params': self.best_params
        }

    def predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions on new data"""
        if self.model is None:
            raise RuntimeError("Model not trained. Call train() first.")

        X = self.prepare_features(df, fit_scaler=False)
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)[:, 1]  # Probability of urgent class

        return predictions, probabilities

    def predict_single(self, features: Dict) -> Tuple[str, float]:
        """Predict priority for a single ticket"""
        # Convert features dict to array
        feature_vector = np.array([features.get(f, 0) for f in self.FEATURE_NAMES]).reshape(1, -1)
        X_scaled = self.scaler.transform(feature_vector)
        pred = self.model.predict(X_scaled)[0]
        prob = self.model.predict_proba(X_scaled)[0, 1]

        label = 'urgent' if pred == 1 else 'normal'
        return label, float(prob)

    def _compute_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """Compute classification metrics"""
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0)
        }

    def evaluate(self, df: pd.DataFrame) -> Dict:
        """Full evaluation on dataset"""
        logger.info("Running full evaluation")

        X = self.prepare_features(df, fit_scaler=False)
        y = df['is_urgent'].values
        y_pred = self.model.predict(X)

        # Compute all metrics
        metrics = self._compute_metrics(y, y_pred)

        # Confusion matrix
        cm = confusion_matrix(y, y_pred)
        metrics['confusion_matrix'] = cm.tolist()

        # Classification report
        report = classification_report(y, y_pred, output_dict=True, zero_division=0)
        metrics['classification_report'] = report

        logger.info(f"Evaluation results: {metrics}")
        return metrics

    def save(self, path: str = None):
        """Save model and scaler to disk"""
        save_path = Path(path) if path else Path(settings.ml_model_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.FEATURE_NAMES,
            'model_type': self.model_type,
            'feature_importance': self.feature_importance,
            'best_params': self.best_params
        }, save_path)
        logger.info(f"Model saved to {save_path}")

    def load(self, path: str = None):
        """Load model from disk"""
        load_path = Path(path) if path else Path(settings.ml_model_path)

        if not load_path.exists():
            raise FileNotFoundError(f"Model file not found: {load_path}")

        data = joblib.load(load_path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.FEATURE_NAMES = data['feature_names']
        self.model_type = data.get('model_type', 'unknown')
        self.feature_importance = data.get('feature_importance')
        self.best_params = data.get('best_params')

        logger.info(f"Model loaded from {load_path}")
        return self

    def get_feature_importance(self) -> Optional[Dict]:
        """Return feature importance if available"""
        return self.feature_importance

# Global ML model instance
ml_model = MLModel()
