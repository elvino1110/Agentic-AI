```python
import gradio as gr
from accounts import Account, get_share_price

# Initialize the account for the demo
account = Account(user_id='user_demo', initial_deposit=10000.0)

def create_account(user_id, initial_deposit):
    global account
    account = Account(user_id=user_id, initial_deposit=initial_deposit)
    return f"Account created with ID: {user_id} and initial deposit: ${initial_deposit}"

def make_deposit(amount):
    account.deposit_funds(amount)
    return f"${amount} deposited successfully. Current balance: ${account.balance}"

def make_withdrawal(amount):
    if account.withdraw_funds(amount):
        return f"${amount} withdrawn successfully. Current balance: ${account.balance}"
    return f"Insufficient funds. Withdrawal of ${amount} failed."

def buy_shares(symbol, quantity):
    if account.buy_shares(symbol, quantity):
        return f"Bought {quantity} shares of {symbol} at ${get_share_price(symbol)} each."
    return f"Failed to buy shares. Not enough balance."

def sell_shares(symbol, quantity):
    if account.sell_shares(symbol, quantity):
        return f"Sold {quantity} shares of {symbol} at ${get_share_price(symbol)} each."
    return f"Failed to sell shares. Not enough holdings."

def view_portfolio_value():
    portfolio_value = account.get_portfolio_value()
    profit_loss = account.get_profit_or_loss()
    return f"Portfolio Value: ${portfolio_value}, Profit/Loss: ${profit_loss}"

def view_holdings():
    holdings = account.get_holdings()
    return f"Holdings: {holdings}"

def view_transactions():
    transactions = account.get_transaction_history()
    return f"Transactions: {transactions}"

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("### Trading Account Management")
    
    with gr.Tab("Account"):
        with gr.Row():
            create_input_user_id = gr.Textbox(label="User ID")
            create_input_initial_deposit = gr.Number(label="Initial Deposit", value=10000.0)
            create_btn = gr.Button("Create Account")
            create_output = gr.Textbox(label="Output")
        create_btn.click(fn=create_account, inputs=[create_input_user_id, create_input_initial_deposit], outputs=create_output)
    
    with gr.Tab("Deposit/Withdraw"):
        with gr.Row():
            deposit_input = gr.Number(label="Deposit Amount")
            deposit_btn = gr.Button("Deposit")
            deposit_output = gr.Textbox(label="Output")
        
        with gr.Row():
            withdraw_input = gr.Number(label="Withdrawal Amount")
            withdraw_btn = gr.Button("Withdraw")
            withdraw_output = gr.Textbox(label="Output")
        
        deposit_btn.click(fn=make_deposit, inputs=[deposit_input], outputs=deposit_output)
        withdraw_btn.click(fn=make_withdrawal, inputs=[withdraw_input], outputs=withdraw_output)
    
    with gr.Tab("Trade"):
        with gr.Row():
            symbol_input = gr.Textbox(label="Symbol", placeholder="AAPL, TSLA, GOOGL")
            quantity_input = gr.Number(label="Quantity")
        
        with gr.Row():
            buy_btn = gr.Button("Buy")
            buy_output = gr.Textbox(label="Output")
            sell_btn = gr.Button("Sell")
            sell_output = gr.Textbox(label="Output")
        
        buy_btn.click(fn=buy_shares, inputs=[symbol_input, quantity_input], outputs=buy_output)
        sell_btn.click(fn=sell_shares, inputs=[symbol_input, quantity_input], outputs=sell_output)
    
    with gr.Tab("Report"):
        portfolio_btn = gr.Button("Portfolio Value")
        portfolio_output = gr.Textbox(label="Portfolio Value and Profit/Loss")
        
        holdings_btn = gr.Button("Holdings")
        holdings_output = gr.Textbox(label="Current Holdings")
        
        transactions_btn = gr.Button("Transactions")
        transactions_output = gr.Textbox(label="Transaction History")
        
        portfolio_btn.click(fn=view_portfolio_value, outputs=portfolio_output)
        holdings_btn.click(fn=view_holdings, outputs=holdings_output)
        transactions_btn.click(fn=view_transactions, outputs=transactions_output)

if __name__ == "__main__":
    demo.launch()
```