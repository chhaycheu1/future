from datetime import datetime

class RiskManager:
    def __init__(self, config, db_manager):
        self.risk_per_trade = config.RISK_PER_TRADE
        self.position_size_usdt = getattr(config, 'POSITION_SIZE_USDT', 0)
        self.leverage = getattr(config, 'LEVERAGE', 5)
        self.sl_multiplier = config.STOP_LOSS_ATR_MULTIPLIER
        self.tp_rr = config.TAKE_PROFIT_RR
        self.db_manager = db_manager

    def calculate_position_size(self, account_balance, entry_price, stop_loss):
        """
        Calculates position size.
        If POSITION_SIZE_USDT > 0: Uses fixed USDT amount * leverage / entry_price
        Else: Uses risk percentage and stop loss distance
        """
        if account_balance <= 0 or entry_price <= 0:
            return 0
        
        # Fixed USDT amount mode
        if self.position_size_usdt > 0:
            # Position size in coins = (USDT amount * leverage) / entry price
            position_size = (self.position_size_usdt * self.leverage) / entry_price
            return position_size
        
        # Percentage-based risk mode
        risk_amount = account_balance * self.risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 0
            
        position_size = risk_amount / price_diff
        return position_size

    def can_open_trade(self, account_balance):
        """
        Always returns True as per user request to remove daily limits.
        """
        if account_balance <= 0:
            return False
        return True
