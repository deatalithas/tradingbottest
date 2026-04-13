import numpy as np
import pandas as pd
from hmmlearn import hmm
from sklearn.preprocessing import StandardScaler
from loguru import logger
import warnings

# Mengabaikan warning deprecation dari hmmlearn agar log tetap bersih
warnings.filterwarnings("ignore")

class MarketRegimeDetector:
    """
    Komponen Brain: Menggunakan Hidden Markov Models (HMM) 
    untuk mendeteksi regime market (Bullish, Bearish, Volatile, Neutral).
    """
    def __init__(self, n_components=4):
        self.n_components = n_components
        # Inisialisasi model Gaussian HMM
        self.model = hmm.GaussianHMM(
            n_components=self.n_components, 
            covariance_type="full", 
            n_iter=100, 
            random_state=42
        )
        self.scaler = StandardScaler()
        self.state_map = {}
        self.is_trained = False
        
    def _prepare_features(self, df):
        """
        Mengekstrak fitur dari data OHLCV untuk dipelajari oleh HMM.
        Kita menggunakan Log Returns dan Volatility.
        """
        data = df.copy()
        
        # 1. Hitung Log Returns (Perubahan harga persentase)
        data['Returns'] = np.log(data['close'] / data['close'].shift(1))
        
        # 2. Hitung Volatility (Standar deviasi dari return selama 14 bar terakhir)
        data['Volatility'] = data['Returns'].rolling(window=14).std()
        
        # Buang baris yang memiliki nilai NaN (biasanya di awal data karena rolling window)
        data.dropna(inplace=True)
        
        # Ambil hanya kolom fitur yang dibutuhkan
        features = data[['Returns', 'Volatility']].values
        return features, data

    def _map_states(self, features_scaled, data):
        """
        HMM hanya menghasilkan angka state (0, 1, 2, 3).
        Fungsi ini melabeli angka tersebut menjadi bahasa manusia (Bullish, Bearish, dll)
        berdasarkan rata-rata return dan volatilitas di masing-masing state.
        """
        hidden_states = self.model.predict(features_scaled)
        data['State'] = hidden_states
        
        state_stats = []
        for i in range(self.n_components):
            state_data = data[data['State'] == i]
            if len(state_data) == 0:
                continue
            
            state_stats.append({
                'state': i,
                'return': state_data['Returns'].mean(),
                'volatility': state_data['Volatility'].mean()
            })
            
        # Urutkan state berdasarkan volatilitas (dari rendah ke tinggi)
        state_stats.sort(key=lambda x: x['volatility'])
        
        # State dengan volatilitas paling tinggi kita anggap "Volatile (Bahaya)"
        self.state_map[state_stats[-1]['state']] = "Volatile (Bahaya)"
        
        # Sisa state kita urutkan berdasarkan return (dari minus ke plus)
        remaining_states = state_stats[:-1]
        remaining_states.sort(key=lambda x: x['return'])
        
        if len(remaining_states) == 3:
            self.state_map[remaining_states[0]['state']] = "Bearish"
            self.state_map[remaining_states[1]['state']] = "Neutral"
            self.state_map[remaining_states[2]['state']] = "Bullish"
        else:
            # Fallback jika komponen kurang dari 4
            for stat in remaining_states:
                self.state_map[stat['state']] = "Neutral"

    def train(self, df):
        """Melatih model HMM menggunakan data historis."""
        logger.info("Training HMM Model...")
        features, data = self._prepare_features(df)
        
        if len(features) == 0:
            logger.error("Not enough data to train HMM.")
            return False
            
        # Normalisasi data (Z-score scaling) agar HMM lebih mudah belajar
        features_scaled = self.scaler.fit_transform(features)
        
        # Latih model
        self.model.fit(features_scaled)
        self.is_trained = True
        
        # Beri nama pada masing-masing state
        self._map_states(features_scaled, data)
        
        logger.info(f"HMM Model trained successfully. State mapping: {self.state_map}")
        return True
        
    def predict_regime(self, df):
        """Memprediksi regime market saat ini berdasarkan data terbaru."""
        if not self.is_trained:
            logger.warning("Model is not trained yet! Call train() first.")
            return "Unknown"
            
        features, _ = self._prepare_features(df)
        if len(features) == 0:
            return "Unknown"
            
        features_scaled = self.scaler.transform(features)
        
        # Prediksi seluruh sequence data
        hidden_states = self.model.predict(features_scaled)
        
        # Ambil state paling terakhir (kondisi market saat ini)
        current_state = hidden_states[-1] 
        regime_name = self.state_map.get(current_state, "Unknown")
        
        logger.info(f"Current Market Regime detected as: {regime_name}")
        return regime_name
