import streamlit as st
import sqlite3 as sql
import time
import yfinance as yf

# DB management
conn = sql.connect('userdata.db')
c = conn.cursor()

def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS usertable(username TEXT,password TEXT)')

def create_portfoliotable(user):
    c.execute('CREATE TABLE IF NOT EXISTS {}table(username TEXT,portfolio_value REAL)'.format(user))

def addto_portfolio(user, ticker, share):
    c.execute('ALTER TABLE {}table ADD {} {}'.format(user, ticker, share))

def add_portfolio(user, value):
    c.execute('INSERT INTO {}table(username,portfolio_value) VALUES (?,?)'.format(user), (user,value))
    conn.commit()

def add_userdata(username,password):
    c.execute('INSERT INTO usertable(username,password) VALUES (?,?)', (username,password))
    conn.commit()

def login_user(username,password):
    c.execute('SELECT * FROM usertable WHERE username=? AND password=?', (username,password))
    data=c.fetchall()
    return data

def all_user(username,password):
    c.execute('SELECT * FROM usertable')
    data=c.fetchall()
    return data

def main():
    '''simple login'''
    st.title = 'simple login'

    menu = ['Home', 'Login', 'Signup']
    choice = st.sidebar.selectbox('Menu',menu)
    selection = None

    if 'logged_in' in st.session_state and st.session_state.logged_in == True:
        st.session_state.navopts = ['portfolio', 'trading']

        st.success('Logged In as {}'.format(st.session_state.username))

        selection = st.sidebar.radio("", st.session_state.navopts)

        if selection == 'portfolio':
            st.empty().empty()
            st.subheader('{}\'s Portfolio'.format(st.session_state.username))

            if st.sidebar.button('Logout'):
                st.session_state.logged_in = False
                st.experimental_rerun()
        if selection == 'trading':
            st.empty().empty()
            st.subheader('Stock Trading Platform')
            if st.sidebar.button('Logout'):
                st.session_state.logged_in = False
                st.experimental_rerun()

    elif 'logged_in' in st.session_state and st.session_state.logged_in == True and choice == 'Home':
        st.subheader('Home') 
        if st.sidebar.button('Logout'):
            st.session_state.logged_in = False
            st.experimental_rerun()

    elif 'logged_in' in st.session_state and st.session_state.logged_in == True and choice == 'Login':
            task = st.selectbox('Task', ['Portfolio', 'Stock Trading'])
            if task == 'Portfolio':
                st.subheader('Portfolio')
            
            elif task == 'Stock Trading':
                st.subheader('Stock Trading Platform')

            if st.sidebar.button('Logout'):
                st.session_state.logged_in = False
                st.experimental_rerun()

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
            initial = '100000'
            create_usertable()
            add_userdata(new_user, new_password)
            create_portfoliotable(new_user)
            add_portfolio(new_user, initial)
            
if __name__ == '__main__':
    main()

