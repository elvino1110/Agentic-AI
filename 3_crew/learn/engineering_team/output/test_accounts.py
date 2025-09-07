```
import unittest
from unittest.mock import patch
from accounts import Account, get_share_price

class TestAccount(unittest.TestCase):
    def setUp(self):
        self.account = Account(user_id='user123', initial_deposit=10000.0)

    def test_account_creation(self):
        self.assertEqual(self.account.user_id, 'user123')
        self.assertEqual(self.account.initial_deposit, 10000.0)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(self.account.transactions, [])

    def test_deposit_funds(self):
        self.account.deposit_funds(2000.0)
        self.assertEqual(self.account.balance, 12000.0)

    def test_withdraw_funds_success(self):
        self.assertTrue(self.account.withdraw_funds(500.0))
        self.assertEqual(self.account.balance, 9500.0)

    def test_withdraw_funds_failure(self):
        self.assertFalse(self.account.withdraw_funds(20000.0))
        self.assertEqual(self.account.balance, 10000.0)

    @patch('accounts.get_share_price', return_value=150.0)
    def test_buy_shares_success(self, mock_get_share_price):
        self.assertTrue(self.account.buy_shares('AAPL', 10))
        self.assertEqual(self.account.balance, 8500.0)
        self.assertEqual(self.account.holdings['AAPL'], 10)

    @patch('accounts.get_share_price', return_value=150.0)
    def test_buy_shares_failure(self, mock_get_share_price):
        self.assertFalse(self.account.buy_shares('AAPL', 100))
        self.assertEqual(self.account.balance, 10000.0)

    @patch('accounts.get_share_price', return_value=150.0)
    def test_sell_shares_success(self, mock_get_share_price):
        self.account.buy_shares('AAPL', 10)
        self.assertTrue(self.account.sell_shares('AAPL', 5))
        self.assertEqual(self.account.balance, 9250.0)
        self.assertEqual(self.account.holdings['AAPL'], 5)

    def test_sell_shares_failure(self):
        self.assertFalse(self.account.sell_shares('AAPL', 10))
        self.assertEqual(self.account.balance, 10000.0)

    @patch('accounts.get_share_price', side_effect=lambda symbol: {'AAPL': 150.0, 'TSLA': 700.0, 'GOOGL': 2800.0}.get(symbol, 0.0))
    def test_get_portfolio_value(self, mock_get_share_price):
        self.account.buy_shares('AAPL', 10)
        self.assertEqual(self.account.get_portfolio_value(), 10000.0)

    @patch('accounts.get_share_price', side_effect=lambda symbol: {'AAPL': 150.0, 'TSLA': 700.0, 'GOOGL': 2800.0}.get(symbol, 0.0))
    def test_get_profit_or_loss(self, mock_get_share_price):
        self.account.buy_shares('AAPL', 10)
        self.assertEqual(self.account.get_profit_or_loss(), 0.0)

    def test_get_holdings(self):
        self.assertEqual(self.account.get_holdings(), {})

    def test_get_transaction_history(self):
        self.account.deposit_funds(500.0)
        transactions = self.account.get_transaction_history()
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['type'], 'deposit')

if __name__ == '__main__':
    unittest.main()
```