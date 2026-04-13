import time
from dotenv import load_dotenv
from loguru import logger

from src.broker.mt5_manager import MT5Manager
from src.brain.hmm_model import MarketRegimeDetector
from src.safety.risk_manager import SafetyManager
from src.allocation.position_sizer import AllocationManager

load_dotenv()

def main():
    logger.info("=== Memulai XAUUSD Trading Bot (HMM Architecture) ===")
    
    # 1. Inisialisasi Broker (MT5)
    broker = MT5Manager()
    if not broker.connect():
        logger.error("Gagal terhubung ke MT5. Keluar dari program.")
        return
        
    # Dapatkan saldo awal untuk Circuit Breaker
    account_info = broker.get_account_info()
    if not account_info:
        logger.error("Gagal mengambil info akun. Keluar dari program.")
        broker.disconnect()
        return
        
    initial_balance = account_info['balance']
    logger.info(f"Saldo Awal Hari Ini: ${initial_balance:.2f}")
    
    # 2. Inisialisasi Komponen Lainnya
    brain = MarketRegimeDetector(n_components=4)
    safety = SafetyManager(daily_loss_limit_pct=0.02, default_sl_pips=50, default_tp_pips=100)
    allocation = AllocationManager(base_lot=0.02, min_lot=0.01)
    
    symbol = "XAUUSD"
    
    # 3. Training Awal HMM
    logger.info("Mengambil 1000 bar data historis untuk training HMM...")
    df_train = broker.get_historical_data(symbol=symbol, num_bars=1000)
    
    if df_train is not None:
        brain.train(df_train)
    else:
        logger.error("Gagal mengambil data training. Keluar dari program.")
        broker.disconnect()
        return
        
    logger.info("Bot masuk ke mode pemantauan (Monitoring Mode)...")
    
    try:
        while True:
            logger.info("--- Memulai siklus pengecekan baru ---")
            
            # A. Cek Circuit Breaker
            acc_info = broker.get_account_info()
            if acc_info:
                current_equity = acc_info['equity']
                if safety.check_circuit_breaker(initial_balance, current_equity):
                    logger.warning("Circuit Breaker aktif! Menghentikan trading hari ini.")
                    break # Keluar dari loop utama karena batas rugi harian tercapai
            
            # B. Tarik data harga terbaru (cukup 50 bar terakhir untuk prediksi)
            logger.info("Menarik data harga terbaru...")
            df_latest = broker.get_historical_data(symbol=symbol, num_bars=50)
            
            if df_latest is not None:
                # C. Deteksi Regime
                regime = brain.predict_regime(df_latest)
                
                # D. Tentukan Lot Size berdasarkan Regime
                lot_size = allocation.calculate_lot_size(regime)
                
                # E. Eksekusi Trading
                if lot_size > 0:
                    current_close = df_latest['close'].iloc[-1]
                    
                    if regime == "Bullish":
                        logger.info("Sinyal BUY terdeteksi!")
                        sl, tp = safety.calculate_sl_tp(current_close, "BUY")
                        broker.execute_trade(symbol, "BUY", lot_size, sl, tp)
                        
                    elif regime == "Bearish":
                        logger.info("Sinyal SELL terdeteksi!")
                        sl, tp = safety.calculate_sl_tp(current_close, "SELL")
                        broker.execute_trade(symbol, "SELL", lot_size, sl, tp)
                        
                    else:
                        logger.info(f"Regime {regime}, tidak ada sinyal trading yang kuat. Menunggu...")
                else:
                    logger.info("Lot size 0 (mungkin karena Volatile). Menunggu...")
            
            # Tunggu 1 menit sebelum cek lagi
            logger.info("Siklus selesai. Menunggu 60 detik...")
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Bot dihentikan secara manual oleh pengguna (Ctrl+C).")
    except Exception as e:
        logger.error(f"Terjadi error tak terduga: {e}")
    finally:
        broker.disconnect()
        logger.info("=== Bot Berhenti ===")

if __name__ == "__main__":
    main()
