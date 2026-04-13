import os
import pandas as pd
import MetaTrader5 as mt5
from loguru import logger

class MT5Manager:
    """
    Komponen Broker: Jembatan antara kode Python dan terminal MT5.
    """
    def __init__(self):
        # Mengambil kredensial dari environment variables (.env)
        # Pastikan MT5_LOGIN dikonversi ke integer
        self.login = int(os.getenv("MT5_LOGIN", 0)) if os.getenv("MT5_LOGIN") else 0
        self.password = os.getenv("MT5_PASSWORD", "")
        self.server = os.getenv("MT5_SERVER", "")
        
    def connect(self):
        """Inisialisasi koneksi ke terminal MT5."""
        logger.info("Connecting to MetaTrader 5...")
        
        # Initialize MT5 dengan kredensial
        if not mt5.initialize(login=self.login, server=self.server, password=self.password):
            logger.error(f"MT5 initialization failed. Error code: {mt5.last_error()}")
            return False
            
        logger.info(f"Successfully connected to MT5 (Account: {self.login}).")
        return True
        
    def disconnect(self):
        """Menutup koneksi ke MT5."""
        mt5.shutdown()
        logger.info("Disconnected from MT5.")
        
    def get_historical_data(self, symbol="XAUUSD", timeframe=mt5.TIMEFRAME_M15, num_bars=1000):
        """
        Menarik data historis (OHLCV) dari MT5.
        
        :param symbol: Pair mata uang/komoditas (default: XAUUSD)
        :param timeframe: Timeframe MT5 (default: M15)
        :param num_bars: Jumlah bar yang ditarik (default: 1000)
        :return: Pandas DataFrame berisi data historis
        """
        logger.info(f"Fetching {num_bars} bars for {symbol}...")
        
        # Menarik data dari posisi saat ini (0) ke belakang sebanyak num_bars
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_bars)
        
        if rates is None:
            logger.error(f"Failed to fetch data for {symbol}. Error code: {mt5.last_error()}")
            return None
            
        # Konversi array ke Pandas DataFrame
        df = pd.DataFrame(rates)
        
        # Konversi kolom waktu dari detik (Unix timestamp) ke format datetime
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Set kolom time sebagai index DataFrame
        df.set_index('time', inplace=True)
        
        return df

    def get_account_info(self):
        """Mengambil informasi akun (balance, equity, dll)."""
        account_info = mt5.account_info()
        if account_info is None:
            logger.error(f"Failed to get account info. Error code: {mt5.last_error()}")
            return None
        return account_info._asdict()

    def execute_trade(self, symbol, order_type, lot, sl, tp):
        """
        Mengeksekusi order BUY atau SELL ke MT5.
        """
        # Dapatkan harga tick terbaru (ask/bid)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"Failed to get tick for {symbol}. Error: {mt5.last_error()}")
            return None
            
        action_type = mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL
        price = tick.ask if order_type == "BUY" else tick.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lot),
            "type": action_type,
            "price": price,
            "sl": float(sl),
            "tp": float(tp),
            "deviation": 20,
            "magic": 101010, # ID unik untuk bot ini
            "comment": "HMM Bot Order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        logger.info(f"Sending {order_type} order for {symbol} | Lot: {lot} | SL: {sl} | TP: {tp}")
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed! Code: {result.retcode}, Comment: {result.comment}")
            return None
            
        logger.success(f"Order {order_type} executed successfully! Ticket: {result.order}")
        return result
