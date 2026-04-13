from loguru import logger

class AllocationManager:
    """
    Komponen Allocation: Menentukan ukuran lot berdasarkan 
    regime market dari HMM.
    """
    def __init__(self, base_lot=0.02, min_lot=0.01):
        # Base lot diset 0.02 agar saat dipotong 50% masih 0.01 (batas minimal MT5)
        self.base_lot = base_lot
        self.min_lot = min_lot
        
    def calculate_lot_size(self, regime):
        """
        Menghitung ukuran lot berdasarkan regime dari HMM.
        """
        if regime in ["Bullish", "Bearish", "Neutral"]:
            lot = self.base_lot
            logger.info(f"[Allocation] Regime {regime}: Menggunakan lot standar ({lot})")
            
        elif "Volatile" in regime:
            # Potong lot jadi 50% saat volatile (bahaya)
            lot = self.base_lot * 0.5
            
            # Pastikan lot tidak di bawah minimum lot MT5 (biasanya 0.01)
            if lot < self.min_lot:
                logger.warning(f"[Allocation] Regime {regime}: Lot diskon ({lot}) di bawah minimum MT5. Trading dihentikan (Lot=0).")
                lot = 0.0
            else:
                logger.warning(f"[Allocation] Regime {regime}: Bahaya! Mengurangi lot 50% menjadi ({lot})")
        else:
            lot = 0.0
            logger.error(f"[Allocation] Regime tidak dikenal ({regime}): Trading dihentikan.")
            
        # Format ke 2 angka desimal sesuai standar MT5
        return round(lot, 2)
