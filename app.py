import streamlit as st
import sqlite3 as sql
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
import time
from yahoo_fin import stock_info as si

# DB management
conn = sql.connect('userdata.db')
c = conn.cursor()

# function create_usertable() creates a table named usertable that records the username and password for each new user if such table does not exists.
def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS usertable(username TEXT,password TEXT)')

# function add_userdata() consumes username and password and record them to the usertable.
def add_userdata(username,password):
    c.execute('INSERT INTO usertable(username,password) VALUES (?,?)', (username,password))
    conn.commit()

# function login_user() consumes username and password and return the row where both parameters match
def login_user(username,password):
    c.execute('SELECT * FROM usertable WHERE username=? AND password=?', (username,password))
    data=c.fetchall()
    return data

# function create_portfoliotable() consumes username and create a table named usernametable that stores the portfolio value, cash left, stock and shares bought from the account if such table does not exist.
def create_portfoliotable(username):
    c.execute('CREATE TABLE IF NOT EXISTS {}table(PORTFOLIO_VALUE REAL,CURRENT_CASH REAL,TICKER TEXT,SHARES REAL)'.format(username))

# function duplicates() consumes a username and ticker and return the ticker if the account with this username has bought the ticker, and none otherwise.
def duplicates(username, ticker):
    query = 'SELECT PORTFOLIO_VALUE,CURRENT_CASH,TICKER,SHARES FROM {}table'.format(username)
    df_add = pd.read_sql(query, conn)
    for m in range(1,len(df_add.index)):
        if df_add['TICKER'][m] == ticker:
            return ticker
        else: 
            return None

# function addto_portfolio() consumes username, portfolio value, current cash, ticker, and shares.
# It adds ticker and shares bought to the table with the username consumed. 
def addto_portfolio(username, portfolio_value, current_cash, ticker, shares):
    query = 'SELECT * FROM {}table'.format(username)
    addto_df = pd.read_sql(query, conn)
    # Base case: When the table is first created, an initial value need to be set.
    if ticker == None and shares == None:
        c.execute('INSERT INTO {}table(PORTFOLIO_VALUE,CURRENT_CASH,TICKER,SHARES) VALUES (?,?,?,?)'.format(username), (portfolio_value,current_cash,ticker,shares))
        conn.commit()
    # If the ticker has already been bought, then add the share to the current share value and replace the orginal share amount with the new one.
    elif ticker == duplicates(username, ticker):
        for k in range(1, len(addto_df.index)):
            if addto_df['TICKER'][k] == ticker:
                addto_df['SHARES'][k] += shares
                break
            else:
                continue
        c.execute('DROP TABLE {}table'.format(username))
        conn.commit()
        addto_df.to_sql('{}table'.format(username), con=conn)
    # Otherwise, we can confirm that the ticker is new, then insert the ticker and shares to the table with dummy values for portfolio_value and current_cash.
    else:
        c.execute('INSERT INTO {}table(PORTFOLIO_VALUE,CURRENT_CASH,TICKER,SHARES) VALUES (?,?,?,?)'.format(username), (portfolio_value,current_cash,ticker,shares))
        conn.commit()

# function sell_portfolio() consumes username, ticker, and shares.
# It either reduces the share amount of avaiable tickers. 
def sell_portfolio(username, ticker, shares):
    query = 'SELECT * FROM {}table'.format(username)
    sell_df = pd.read_sql(query, conn)
    for k in range(1, len(sell_df.index)):
        if sell_df['TICKER'][k] == ticker:
            sell_df['SHARES'][k] -= shares
            break
        else:
            continue
    c.execute('DROP TABLE {}table'.format(username))
    conn.commit()
    sell_df.to_sql('{}table'.format(username), con=conn)

# function delete_portfolio() consumes username and ticker.
# It deletes the row with the ticker in the table that is owned by the user.
def delete_portfolio(username, ticker):
    query = 'SELECT * FROM {}table'.format(username)
    delete_df = pd.read_sql(query, conn)
    delete_df = delete_df[delete_df['TICKER'] != ticker]
    c.execute('DROP TABLE {}table'.format(username))
    conn.commit()
    delete_df.to_sql('{}table'.format(username), con=conn)

# function update_portfolio_value() consumes username and current cash avaiable in the table.
def update_portfolio_value(username, cash):
    query = 'SELECT PORTFOLIO_VALUE,CURRENT_CASH,TICKER,SHARES FROM {}table'.format(username)
    df = pd.read_sql(query, conn)
    new_value = 0
    for i in range(1,len(df.index)):
        new_value += df['SHARES'][i]*float(si.get_quote_data(df['TICKER'][i])['regularMarketPrice'])
    new_value += cash
    df['PORTFOLIO_VALUE'][0] = new_value
    c.execute('DROP TABLE {}table'.format(username))
    conn.commit()
    df.to_sql('{}table'.format(username), con=conn)

# function update_current_cash() consumes username and the current cash usage
# It updates the column CURRENT_CASH in the user's table.
def update_current_cash(username, cash_usage):
    query = 'SELECT PORTFOLIO_VALUE,CURRENT_CASH,TICKER,SHARES FROM {}table'.format(username)
    df1 = pd.read_sql(query, conn)
    new_cash = df1['CURRENT_CASH'][0]
    df1['CURRENT_CASH'][0] = new_cash-cash_usage
    c.execute('DROP TABLE {}table'.format(username))
    conn.commit()
    df1.to_sql('{}table'.format(username), con=conn)

# function clean consumes a ticker
# It detects whether a ticker is in US market. If it is a stock listed in US, then it returns the ticker, otherwise, it returns None.
def clean(ticker):
    if (si.get_quote_data(ticker)['regularMarketPrice'] == None):
        return 
    elif (yf.Ticker(ticker).info['market'] == 'us_market'):
        return ticker
    else:
        return

def main():
    '''Stock Trading Simulation'''
    st.title = 'Stock Trading Simulation'

    # Three choices, either Home, Login, or Signup, and these choices will be displayed in the sidebar of the screen.
    menu = ['Home', 'Login', 'Signup']
    choice = st.sidebar.selectbox('Menu',menu)
    selection = None

    # If the user has already logged in, run the following code.
    if 'logged_in' in st.session_state and st.session_state.logged_in == True:

        # Set the navigation options to three choices.
        st.session_state.navopts = ['Portfolio', 'Buy', 'Sell']

        st.success('Logged In as {}'.format(st.session_state.username))

        # Display the options as a sidebar selection.
        selection = st.sidebar.radio("", st.session_state.navopts)

        # If the user clicks Portfolio button, run the following code.
        if selection == 'Portfolio':
            # Clear the page.
            st.empty().empty()

            st.subheader('{}\'s Portfolio'.format(st.session_state.username))

            # If the user clicks Logout button, change the logged_in state to False and rerun the entire program.
            if st.sidebar.button('Logout', key='1'):
                st.session_state.logged_in = False
                st.experimental_rerun()
            
            # Convert the sql table to a pandas dataframe and extracts the first portfolio value and cash value from the dataframe.
            query = 'SELECT * FROM {}table'.format(st.session_state.username)
            portfolio_df = pd.read_sql(query, conn)
            st.write('Your current portfolio value is: ${}'.format(str(portfolio_df['PORTFOLIO_VALUE'][0])))
            st.write('Your current cash is: ${}'.format(str(portfolio_df['CURRENT_CASH'][0])))
            
            # Demonstrate the entire user portfolio
            st.write('Your current portfolio is: ')
            st.dataframe(data = portfolio_df.iloc[1:,3:5])
            
            # If the user clicks Update button, run update_portfolio_value() and rebuild the page same as above.
            if st.button('Update', key='Update'):
                update_portfolio_value(st.session_state.username, portfolio_df['CURRENT_CASH'][0])
                st.experimental_rerun()
        
        # If the user clicks Buy button, run the following code.
        elif selection == 'Buy':
            # Clear the page
            st.empty().empty()
            st.subheader('Buy Stock')
            
            # If the user clicks Logout button, change the logged_in state to False and rerun the entire program.
            if st.sidebar.button('Logout', key='3'):
                st.session_state.logged_in = False
                st.experimental_rerun()
            
            # Create inputs that allows user to enter ticker and amount of share they want to buy.
            buy_ticker = st.text_input('Ticker').capitalize()
            buy_share = st.number_input('Share')

            query = 'SELECT * FROM {}table'.format(st.session_state.username)
            buy_df = pd.read_sql(query, conn)
            current_cash = buy_df['CURRENT_CASH'][0]
            initial = 100000

            # If the user clicks the Buy button, run the following code.
            if st.button('Buy', key='Buy'):
                # If the stock is not listed in US, warning.
                if clean(buy_ticker) == None:
                    st.warning('Incorrect ticker, please retry.')
                # If cash in the account is not enough for the purchase, warning.
                elif si.get_quote_data(buy_ticker)['regularMarketPrice'] * buy_share > current_cash:
                    st.warning('Not enough fund for the purchase, please try again')
                # otherwise, run addto_portfolio(), update_current_cash(), and update_portfolio_value to update the user table.
                else:
                    addto_portfolio(st.session_state.username, initial, initial, buy_ticker, buy_share)
                    update_current_cash(st.session_state.username, si.get_quote_data(buy_ticker)['regularMarketPrice'] * buy_share)
                    update_portfolio_df = pd.read_sql(query, conn)
                    new_cash = update_portfolio_df['CURRENT_CASH'][0]
                    update_portfolio_value(st.session_state.username, new_cash)
                    st.success('You have successfully bought {} shares of {}!'.format(buy_share,buy_ticker))
        
        # If the user clicks the Sell button, run the following code.
        elif selection == 'Sell':
            st.empty().empty()
            st.subheader('Sell Stock')
            if st.sidebar.button('Logout', key='4'):
                st.session_state.logged_in = False
                st.experimental_rerun()
            sell_ticker = st.text_input('Ticker')
            sell_share = st.number_input('Share')

            query = 'SELECT * FROM {}table'.format(st.session_state.username)
            sell_df = pd.read_sql(query, conn)
            current_cash = sell_df['CURRENT_CASH'][0]
            if st.button('Sell', key='Sell'):
                if clean(sell_ticker) == None:
                    st.warning('Incorrect ticker, please retry.')
                elif sell_ticker not in list(sell_df['TICKER']):
                    st.warning('Your current portfolio does not contain the stock, please try again.')
                else:
                    for i in range(1, len(sell_df.index)):
                        if sell_df['TICKER'][i] == sell_ticker:
                            current_share = sell_df['SHARES'][i]
                        else:
                            continue
                    if current_share < sell_share:
                        st.warning('You do not have sufficient shares, please enter a smaller value.')
                    elif current_share == sell_share:
                        delete_portfolio(st.session_state.username, sell_ticker)
                        update_current_cash(st.session_state.username, -si.get_quote_data(sell_ticker)['regularMarketPrice'] * sell_share)
                        update_portfolio_df = pd.read_sql(query, conn)
                        new_cash = update_portfolio_df['CURRENT_CASH'][0]
                        update_portfolio_value(st.session_state.username, new_cash)
                        st.success('You have successfully sold {} shares of {}!'.format(sell_share,sell_ticker))
                    else:
                        sell_portfolio(st.session_state.username, sell_ticker, sell_share)
                        update_current_cash(st.session_state.username, -si.get_quote_data(sell_ticker)['regularMarketPrice'] * sell_share)
                        update_portfolio_df = pd.read_sql(query, conn)
                        new_cash = update_portfolio_df['CURRENT_CASH'][0]
                        update_portfolio_value(st.session_state.username, new_cash)
                        st.success('You have successfully sold {} shares of {}!'.format(sell_share,sell_ticker))

    elif choice == 'Login':
        st.subheader('Login')
        st.session_state.username = st.text_input('Username')
        st.session_state.password = st.text_input('Password', type = 'password')

        if st.checkbox('Login'):
            create_usertable()
            result = login_user(st.session_state.username,st.session_state.password)
            if result:
                st.session_state.logged_in = True
                with st.spinner("Redirecting to application..."):
                    time.sleep(1)
                    st.experimental_rerun()
            else:
                st.warning('incorrect username or password. Please try again.')

    elif choice == 'Signup':
        st.subheader('Create a new account')
        new_user = st.text_input('Username')
        new_password = st.text_input('Password', type='password')
        query = 'SELECT * FROM usertable'
        if st.button('Signup', key='Signup'):
            create_usertable()
            signup_df = pd.read_sql(query, conn)
            for i in range(len(signup_df.index)):
                if new_user[0].isdigit():
                    st.warning('First character cannot be a number, please change it.')
                    st.experimental_rerun()
                if signup_df['username'][i] == new_user:
                    st.warning('This username is unavaliable, please change it.')
                    st.experimental_rerun()
                else:
                    continue
            initial = 100000
            add_userdata(new_user, new_password)
            create_portfoliotable(new_user)
            addto_portfolio(new_user, initial, initial, None, None)
            st.success('You have successfully created an account!')
            st.success("Go to the Login Menu to login")
    
    elif choice == 'Home':
        st.subheader('Stock Trading Simulation')
        st.write('Author: Tom Pan')
        st.write('This platform is only for trading in US market.')
        st.write('Every player gets $100000 after completing the signup step, and all players are given two options: buy or sell.')
        st.write('Enjoy Trading!')

if __name__ == '__main__':
    main()