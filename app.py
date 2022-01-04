import streamlit as st
import sqlite3 as sql
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
import time

# DB management
conn = sql.connect('userdata.db')
c = conn.cursor()

def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS usertable(username TEXT,password TEXT)')

def add_userdata(username,password):
    c.execute('INSERT INTO usertable(username,password) VALUES (?,?)', (username,password))
    conn.commit()

def login_user(username,password):
    c.execute('SELECT * FROM usertable WHERE username=? AND password=?', (username,password))
    data=c.fetchall()
    return data

def all_user():
    c.execute('SELECT * FROM usertable')
    data=c.fetchall()
    return data

def create_portfoliotable(user):
    c.execute('CREATE TABLE IF NOT EXISTS {}table(PORTFOLIO_VALUE REAL,CURRENT_CASH REAL,TICKER TEXT,SHARES REAL)'.format(user))

def duplicates(user, ticker1):
    query = 'SELECT PORTFOLIO_VALUE,CURRENT_CASH,TICKER,SHARES FROM {}table'.format(user)
    df_add = pd.read_sql(query, conn)
    for m in range(1,len(df_add.index)):
        if df_add['TICKER'][m] == ticker1:
            return ticker1
        else: 
            return None

def addto_portfolio(user, portfolio_value, current_cash, ticker, shares):
    query = 'SELECT * FROM {}table'.format(user)
    addto_df = pd.read_sql(query, conn)
    if ticker == None and shares == None:
        c.execute('INSERT INTO {}table(PORTFOLIO_VALUE,CURRENT_CASH,TICKER,SHARES) VALUES (?,?,?,?)'.format(user), (portfolio_value,current_cash,ticker,shares))
        conn.commit()
    elif ticker == duplicates(user, ticker):
        for k in range(1, len(addto_df.index)):
            if addto_df['TICKER'][k] == ticker:
                addto_df['SHARES'][k] += shares
                break
            else:
                continue
        c.execute('DROP TABLE {}table'.format(user))
        conn.commit()
        addto_df.to_sql('{}table'.format(user), con=conn)
    else:
        c.execute('INSERT INTO {}table(PORTFOLIO_VALUE,CURRENT_CASH,TICKER,SHARES) VALUES (?,?,?,?)'.format(user), (portfolio_value,current_cash,ticker,shares))
        conn.commit()

def sell_portfolio(user, ticker, shares):
    query = 'SELECT * FROM {}table'.format(st.session_state.username)
    sell_df = pd.read_sql(query, conn)
    for k in range(1, len(sell_df.index)):
        if sell_df['TICKER'][k] == ticker:
            sell_df['SHARES'][k] -= shares
            break
        else:
            continue
    c.execute('DROP TABLE {}table'.format(user))
    conn.commit()
    sell_df.to_sql('{}table'.format(user), con=conn)

def delete_portfolio(user, ticker):
    query = 'SELECT * FROM {}table'.format(st.session_state.username)
    delete_df = pd.read_sql(query, conn)
    delete_df = delete_df[delete_df['TICKER'] != ticker]
    c.execute('DROP TABLE {}table'.format(user))
    conn.commit()
    delete_df.to_sql('{}table'.format(user), con=conn)

def update_portfolio_value(user, cash):
    query = 'SELECT PORTFOLIO_VALUE,CURRENT_CASH,TICKER,SHARES FROM {}table'.format(user)
    df = pd.read_sql(query, conn)
    new_value = 0
    for i in range(1,len(df.index)):
        new_value += df['SHARES'][i]*yf.Ticker(df['TICKER'][i]).info['regularMarketPrice']
    new_value += cash
    df['PORTFOLIO_VALUE'][0] = new_value
    c.execute('DROP TABLE {}table'.format(user))
    conn.commit()
    df.to_sql('{}table'.format(user), con=conn)

def update_current_cash(user, cash_usage):
    query = 'SELECT PORTFOLIO_VALUE,CURRENT_CASH,TICKER,SHARES FROM {}table'.format(user)
    df1 = pd.read_sql(query, conn)
    new_cash = df1['CURRENT_CASH'][0]
    df1['CURRENT_CASH'][0] = new_cash-cash_usage
    c.execute('DROP TABLE {}table'.format(user))
    conn.commit()
    df1.to_sql('{}table'.format(user), con=conn)

def clean(tic):
    if (yf.Ticker(tic).info['regularMarketPrice'] == None):
        return 
    elif (yf.Ticker(tic).info['market'] == 'us_market'):
        return tic
    else:
        return

def main():
    '''simple login'''
    st.title = 'simple login'

    menu = ['Home', 'Login', 'Signup']
    choice = st.sidebar.selectbox('Menu',menu)
    selection = None

    if 'logged_in' in st.session_state and st.session_state.logged_in == True:
        st.session_state.navopts = ['Portfolio', 'Buy', 'Sell']

        st.success('Logged In as {}'.format(st.session_state.username))

        selection = st.sidebar.radio("", st.session_state.navopts)

        if selection == 'Portfolio':
            st.empty().empty()
            st.subheader('{}\'s Portfolio'.format(st.session_state.username))

            if st.sidebar.button('Logout'):
                st.session_state.logged_in = False
                st.experimental_rerun()
            
            query = 'SELECT * FROM {}table'.format(st.session_state.username)
            portfolio_df = pd.read_sql(query, conn)
            st.write('Your current portfolio value is: {}'.format(str(portfolio_df['PORTFOLIO_VALUE'][0])))
            st.write('Your current cash is: {}'.format(str(portfolio_df['CURRENT_CASH'][0])))
            st.write('Your current portfolio is: ')
            st.dataframe(data = portfolio_df.iloc[1:,3:5])

            if st.button('Update'):
                update_portfolio_value(st.session_state.username, portfolio_df['CURRENT_CASH'][0])
                st.empty().empty()
                st.subheader('{}\'s Portfolio'.format(st.session_state.username))

                if st.sidebar.button('Logout'):
                    st.session_state.logged_in = False
                    st.experimental_rerun()

                st.write('Your current portfolio value is: ${}'.format(str(portfolio_df['PORTFOLIO_VALUE'][0])))
                st.write('Your current cash is: ${}'.format(str(portfolio_df['CURRENT_CASH'][0])))
                st.write('Your current portfolio is: ')
                st.dataframe(data = portfolio_df.loc[1:,3:4])
        
        elif selection == 'Buy':
            st.empty().empty()
            st.subheader('Buy Stock')
            if st.sidebar.button('Logout'):
                st.session_state.logged_in = False
                st.experimental_rerun()
            buy_ticker = st.text_input('Ticker')
            buy_share = st.number_input('Share')

            query = 'SELECT * FROM {}table'.format(st.session_state.username)
            buy_df = pd.read_sql(query, conn)
            current_cash = buy_df['CURRENT_CASH'][0]
            initial = 100000
            if st.button('Buy'):
                if clean(buy_ticker) == None:
                    st.warning('Incorrect ticker, please retry.')
                elif yf.Ticker(buy_ticker).info['regularMarketPrice'] * buy_share > current_cash:
                    st.warning('Not enough fund for the purchase, please try again')
                else:
                    addto_portfolio(st.session_state.username, initial, initial, buy_ticker, buy_share)
                    update_current_cash(st.session_state.username, yf.Ticker(buy_ticker).info['regularMarketPrice'] * buy_share)
                    update_portfolio_df = pd.read_sql(query, conn)
                    new_cash = update_portfolio_df['CURRENT_CASH'][0]
                    update_portfolio_value(st.session_state.username, new_cash)
                    st.success('You have successfully bought {} shares of {}!'.format(buy_share,buy_ticker))

        elif selection == 'Sell':
            st.empty().empty()
            st.subheader('Sell Stock')
            if st.sidebar.button('Logout'):
                st.session_state.logged_in = False
                st.experimental_rerun()
            sell_ticker = st.text_input('Ticker')
            sell_share = st.number_input('Share')

            query = 'SELECT * FROM {}table'.format(st.session_state.username)
            sell_df = pd.read_sql(query, conn)
            current_cash = sell_df['CURRENT_CASH'][0]
            if st.button('Sell'):
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
                        update_current_cash(st.session_state.username, -yf.Ticker(sell_ticker).info['regularMarketPrice'] * sell_share)
                        update_portfolio_df = pd.read_sql(query, conn)
                        new_cash = update_portfolio_df['CURRENT_CASH'][0]
                        update_portfolio_value(st.session_state.username, new_cash)
                        st.success('You have successfully sold {} shares of {}!'.format(sell_share,sell_ticker))
                    else:
                        sell_portfolio(st.session_state.username, sell_ticker, sell_share)
                        update_current_cash(st.session_state.username, -yf.Ticker(sell_ticker).info['regularMarketPrice'] * sell_share)
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

        if st.button('Signup'):
            st.success('You have successfully created an account!')
            st.success("Go to the Login Menu to login")
            initial = 100000
            create_usertable()
            add_userdata(new_user, new_password)
            create_portfoliotable(new_user)
            addto_portfolio(new_user, initial, initial, None, None)
    
    elif choice == 'Home':
        st.subheader('Stock Trading Simulation')
        st.write('Author: Tom Pan')
        st.write('This platform is only for trading in US market.')
        st.write('Every player gets $100000 after completing the signup step, and all players are given two options: buy or sell.')
        st.write('Enjoy Trading!')

if __name__ == '__main__':
    main()