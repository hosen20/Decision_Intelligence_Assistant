import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import textstat

from utils.logger import logger

# Download NLTK resources on first run
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('sentiment/vader_lexicon')
except LookupError:
    nltk.download('punkt')
    nltk.download('vader_lexicon')

class TicketPreprocessor:
    """Preprocess customer support tweets and create priority labels"""

    # Urgency keyword lists
    URGENCY_KEYWORDS = {
        'refund', 'cancel', 'broken', 'damaged', 'defective', 'urgent', 'emergency',
        'help', 'support', 'issue', 'problem', 'error', 'fail', 'crash', 'down',
        'unavailable', 'missing', 'lost', 'stolen', 'fraud', 'scam', 'hack',
        'security', 'breach', 'leak', 'compromise', 'illegal', 'ban', 'suspend',
        'charge', 'billing', 'overcharge', 'unfair', 'wrong', 'mistake'
    }

    NEGATIVE_WORDS = {
        'terrible', 'awful', 'horrible', 'bad', 'worst', 'hate', 'disappointed',
        'frustrated', 'angry', 'mad', 'annoyed', 'upset', 'unhappy', 'sad'
    }

    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.df = None
        self.labeling_function = None

    def load_data(self, filepath: str) -> pd.DataFrame:
        """Load raw Twitter customer support data"""
        logger.info(f"Loading data from {filepath}")
        try:
            self.df = pd.read_csv(filepath, low_memory=False)
            logger.info(f"Loaded {len(self.df)} tweets")
            return self.df
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not isinstance(text, str):
            return ""

        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)

        # Remove mentions
        text = re.sub(r'@\w+', '', text)

        # Remove hashtags but keep text
        text = re.sub(r'#(\w+)', r'\1', text)

        # Remove RT indicator
        text = re.sub(r'^RT\s+', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply cleaning operations"""
        logger.info("Cleaning data")

        # Ensure text column exists
        if 'text' not in df.columns:
            # Try to find text column (different datasets may have different names)
            text_col = [col for col in df.columns if 'text' in col.lower() or 'tweet' in col.lower()]
            if text_col:
                df = df.rename(columns={text_col[0]: 'text'})
            else:
                raise ValueError("No text column found in dataset")

        # Clean text
        df['clean_text'] = df['text'].apply(self.clean_text)

        # Remove empty tweets
        df = df[df['clean_text'].str.len() > 0].copy()

        logger.info(f"Cleaned data: {len(df)} valid tweets")
        return df

    def define_labeling_function(self, rule: str = "comprehensive"):
        """Define the labeling function for priority"""
        logger.info(f"Defining labeling function: {rule}")

        if rule == "simple":
            # Simple: contains ANY urgency keyword
            def labeling_func(row):
                text_lower = row['clean_text'].lower()
                return int(any(kw in text_lower for kw in self.URGENCY_KEYWORDS))

        elif rule == "comprehensive":
            # Comprehensive: multimodal signals
            def labeling_func(row):
                text = row['clean_text']
                text_lower = text.lower()

                score = 0

                # Keyword signals
                keyword_hits = sum(1 for kw in self.URGENCY_KEYWORDS if kw in text_lower)
                score += keyword_hits * 2

                # Negative sentiment words
                neg_hits = sum(1 for w in self.NEGATIVE_WORDS if w in text_lower)
                score += neg_hits * 1

                # Punctuation signals
                exclamation_count = text.count('!')
                score += min(exclamation_count, 3)  # Cap at 3

                # ALL-CAPS words (each word in all caps adds 1)
                caps_words = len([w for w in text.split() if w.isupper() and len(w) > 2])
                score += min(caps_words, 3)

                # VADER sentiment
                sentiment = self.sia.polarity_scores(text)
                score += int(sentiment['neg'] > 0.5) * 2

                # Text length (very short or very long might indicate urgency)
                text_len = len(text)
                if text_len < 20 or text_len > 200:
                    score += 1

                # Threshold: score >= 5 => urgent
                return 1 if score >= 5 else 0

        else:
            raise ValueError(f"Unknown labeling rule: {rule}")

        self.labeling_function = labeling_func
        return labeling_func

    def apply_label(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply labeling function to create priority labels"""
        logger.info("Applying labeling function")

        if self.labeling_function is None:
            self.define_labeling_function("comprehensive")

        df['is_urgent'] = df.apply(self.labeling_function, axis=1)
        df['priority_label'] = df['is_urgent'].map({1: 'urgent', 0: 'normal'})

        urgency_rate = df['is_urgent'].mean()
        logger.info(f"Labeling complete. Urgent tweets: {urgency_rate:.2%}")

        return df

    def extract_features(self, row: pd.Series) -> Dict:
        """Extract engineered features from a tweet"""
        text = row['clean_text']

        features = {
            # Basic text stats
            'text_length': len(text),
            'word_count': len(text.split()),

            # Urgency keywords
            'urgency_keyword_count': sum(1 for kw in self.URGENCY_KEYWORDS if kw in text.lower()),
            'has_refund': int('refund' in text.lower()),
            'has_cancel': int('cancel' in text.lower()),
            'has_broken': int('broken' in text.lower() or 'damaged' in text.lower()),
            'has_help': int('help' in text.lower()),
            'has_error': int('error' in text.lower() or 'issue' in text.lower()),
            'has_urgent': int('urgent' in text.lower()),

            # Punctuation
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'all_caps_ratio': sum(1 for w in text.split() if w.isupper() and len(w) > 2) / max(len(text.split()), 1),

            # Sentiment
            'sentiment_neg': self.sia.polarity_scores(text)['neg'],
            'sentiment_neu': self.sia.polarity_scores(text)['neu'],
            'sentiment_pos': self.sia.polarity_scores(text)['pos'],
            'sentiment_compound': self.sia.polarity_scores(text)['compound'],

            # Readability
            'readability_score': textstat.flesch_reading_ease(text) if text.strip() else 50.0,

            # Time features (if timestamp available)
            'hour_of_day': 12,  # default
            'is_weekend': 0,
        }

        # Extract hour if datetime column exists
        if 'created_at' in row and pd.notna(row['created_at']):
            try:
                dt = pd.to_datetime(row['created_at'])
                features['hour_of_day'] = dt.hour
                features['is_weekend'] = int(dt.dayofweek >= 5)
            except:
                pass

        return features

    def chunk_text(self, text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]

        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            start = end - overlap  # overlap

        return chunks

    def prepare_for_retrieval(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare dataframe with features for ML and chunks for retrieval"""
        logger.info("Preparing features and chunks")

        # Extract features
        features_df = df.apply(self.extract_features, axis=1, result_type='expand')
        df = pd.concat([df, features_df], axis=1)

        # Create chunks (each tweet might produce multiple chunks)
        df['chunks'] = df['clean_text'].apply(lambda x: self.chunk_text(x))

        logger.info(f"Preparation complete. Total features: {len(features_df.columns)}")
        return df

    def get_feature_names(self) -> List[str]:
        """Get list of feature column names"""
        return [
            'text_length', 'word_count', 'urgency_keyword_count',
            'has_refund', 'has_cancel', 'has_broken', 'has_help', 'has_error', 'has_urgent',
            'exclamation_count', 'question_count', 'all_caps_ratio',
            'sentiment_neg', 'sentiment_neu', 'sentiment_pos', 'sentiment_compound',
            'readability_score', 'hour_of_day', 'is_weekend'
        ]

preprocessor = TicketPreprocessor()
