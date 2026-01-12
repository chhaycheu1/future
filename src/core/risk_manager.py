from datetime import datetime

class RiskManager:
    def __init__(self, config, db_manager):
        self.risk_per_trade = config.RISK_PER_TRADE
        self.sl_multiplier = config.STOP_LOSS_ATR_MULTIPLIER
        self.tp_rr = config.TAKE_PROFIT_RR
        self.db_manager = db_manager

    def calculate_position_size(self, account_balance, entry_price, stop_loss):
        """
        Calculates position size based on risk percentage and stop loss distance.
        Risk Amount = Account Balance * Risk %
        Position Size = Risk Amount / |Entry - SL|
        """
        if account_balance <= 0:
            return 0
        
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
