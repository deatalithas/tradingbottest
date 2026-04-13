from loguru import logger

class SafetyManager:
    """
    Komponen Safety: Menjaga akun dari kerugian fatal.
    """
    def __init__(self, daily_loss_limit_pct=0.02, default_sl_pips=50, default_tp_pips=100):
        # Batas kerugian harian (default 2%)
        self.daily_loss_limit_pct = daily_loss_limit_pct 
        self.default_sl_pips = default_sl_pips
        self.default_tp_pips = default_tp_pips
        self.circuit_breaker_active = False
        
    def check_circuit_breaker(self, initial_balance, current_equity):
        """
        Mengecek apakah kerugian hari ini sudah menyentuh batas maksimal (Circuit Breaker).
        """
        # Jika sudah terpicu sebelumnya, biarkan tetap aktif (bot berhenti)
        if self.circuit_breaker_active:
            return True 
            
        # Hitung persentase kerugian (drawdown)
        drawdown_pct = (initial_balance - current_equity) / initial_balance
        
        if drawdown_pct >= self.daily_loss_limit_pct:
            self.circuit_breaker_active = True
            logger.critical(f"[Safety] CIRCUIT BREAKER TRIGGERED! Drawdown mencapai {drawdown_pct*100:.2f}%. Bot dihentikan.")
            return True
            
        return False
        
    def calculate_sl_tp(self, entry_price, order_type, sl_pips=None, tp_pips=None):
        """
        Menghitung harga pasti untuk Hard Stop Loss dan Take Profit.
        WAJIB dipanggil sebelum mengirim order ke broker.
        """
        sl_pips = sl_pips if sl_pips else self.default_sl_pips
        tp_pips = tp_pips if tp_pips else self.default_tp_pips
        
        # Penyesuaian pip XAUUSD (Biasanya 1 pip = 0.1 USD pergerakan harga di MT5)
        pip_value = 0.1 
        
        if order_type == "BUY":
            sl_price = entry_price - (sl_pips * pip_value)
            tp_price = entry_price + (tp_pips * pip_value)
        elif order_type == "SELL":
            sl_price = entry_price + (sl_pips * pip_value)
            tp_price = entry_price - (tp_pips * pip_value)
        else:
            raise ValueError("Order type harus 'BUY' atau 'SELL'")
            
        # Format ke 2 angka desimal (standar harga XAUUSD)
        return round(sl_price, 2), round(tp_price, 2)
