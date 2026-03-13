import streamlit as st
from app.db.database import SessionLocal
from app.db.models import User

def init_auth():
    """
    Simple auth mechanism. For production, integrate with hashed passwords in DB.
    Here we mock a simple login or verify against DB (if users exist).
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["user_role"] = None
        st.session_state["username"] = None

    if st.session_state["authenticated"]:
        return True

    st.title("🔐 Login - Pipeline V2.1")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            db = SessionLocal()
            user = db.query(User).filter(User.username == username).first()
            db.close()
            
            # Temporary "Backdoor" for setup or until Users are added
            if (username == "admin" and password == "admin") or (user and user.hashed_password == password):
                st.session_state["authenticated"] = True
                st.session_state["user_role"] = "admin" if username == "admin" else user.role
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    
    return False

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user_role"] = None
    st.session_state["username"] = None
    st.rerun()
