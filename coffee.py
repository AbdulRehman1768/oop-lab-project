import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import os

st.set_page_config(page_title="☕ Coffee Shop App", layout="wide")


USERS_FILE = "users.xlsx"


if not os.path.exists(USERS_FILE):
    df = pd.DataFrame(columns=["Email", "Password"])
    df.to_excel(USERS_FILE, index=False)

def load_users():
    return pd.read_excel(USERS_FILE)

def save_user(email, password):
    df = load_users()
    if email in df["Email"].values:
        return False  # User exists
    new_user = pd.DataFrame([[email, password]], columns=["Email", "Password"])
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_excel(USERS_FILE, index=False)
    return True

class CoffeeFileHandler:
    def __init__(self):
        self.df = None
        self.coffee_names = []

    def load_file(self, uploaded_file):
        try:
            self.df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Failed to load file: {e}")
            return
        if 'Coffee' in self.df.columns:
            self.coffee_names = self.df['Coffee'].tolist()
        else:
            st.error("File must contain 'Coffee' column.")

    def get_price(self, selected_coffee):
        if self.df is not None and 'Coffee' in self.df.columns and 'Price' in self.df.columns:
            row = self.df[self.df['Coffee'] == selected_coffee]
            return float(row['Price'].values[0]) if not row.empty else 0.0
        return 0.0


def login_page():
    st.title("🔐 Login Here")

    if "show_signup" not in st.session_state:
        st.session_state.show_signup = False

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    users = load_users()

    if not st.session_state.show_signup:
        if st.button("Login"):
            if email in users["Email"].values:
                stored_password = users[users["Email"] == email]["Password"].values[0]
                if password == stored_password:
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            else:
                st.error("Email not found.")
        if st.button("Go to Sign Up"):
            st.session_state.show_signup = True
            st.rerun()
    else:
        if st.button("Sign Up"):
            if save_user(email, password):
                st.success("Registered successfully! Please login.")
                st.session_state.show_signup = False
                st.rerun()
            else:
                st.warning("User already exists.")
        if st.button("Back to Login"):
            st.session_state.show_signup = False
            st.rerun()

def coffee_app():
    coffee_handler = CoffeeFileHandler()
    pages = ["Upload Menu", "Place Order", "Update Order", "Delete Order", "Charts", "Reports", "Order Summary"]

    st.sidebar.title("☕ Menu")
    choice = st.sidebar.selectbox("Navigate", pages)

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.email = ""
        st.rerun()

    if "orders" not in st.session_state:
        st.session_state.orders = []

    if choice == "Upload Menu":
        st.subheader("📄 Upload Menu Excel (with 'Coffee' & 'Price')")
        uploaded_file = st.file_uploader("Choose Excel File", type=["xlsx"])
        if uploaded_file:
            coffee_handler.load_file(uploaded_file)
            st.session_state.menu = coffee_handler.df
            st.success("Menu uploaded!")
            st.dataframe(coffee_handler.df)

    elif choice == "Place Order":
        st.subheader("🛒 Place Order")
        if "menu" in st.session_state:
            coffee_handler.df = st.session_state.menu
            coffee_handler.coffee_names = coffee_handler.df['Coffee'].tolist()

            selected_coffee = st.selectbox("Choose Coffee", coffee_handler.coffee_names)
            quantity = st.number_input("Quantity", 1, 10, 1)
            size = st.radio("Size", ["Small", "Medium", "Large"])
            name = st.text_input("Customer Name")
            phone = st.text_input("Mobile Number")
            address = st.text_input("Delivery Address")
            tip = st.slider("Tip", 0, 20, 0)

            if st.button("Place Order"):
                if name:
                    price = coffee_handler.get_price(selected_coffee)
                    size_factor = {"Small": 1, "Medium": 1.25, "Large": 1.5}
                    total = price * size_factor[size] * quantity + tip
                    order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    order = {
                        "Customer": name,
                        "Mobile": phone,
                        "Address": address,
                        "Coffee": selected_coffee,
                        "Size": size,
                        "Qty": quantity,
                        "Price": price,
                        "Tip": tip,
                        "Total": total,
                        "Time": order_time,
                        "Status": "Pending",
                        "User": st.session_state.email
                    }

                    st.session_state.orders.append(order)

                    if os.path.exists("all_orders.xlsx"):
                        df = pd.read_excel("all_orders.xlsx")
                        df = pd.concat([df, pd.DataFrame([order])], ignore_index=True)
                    else:
                        df = pd.DataFrame([order])

                    df.to_excel("all_orders.xlsx", index=False)
                    st.success(f"{name}, your order is placed!")
                    st.info(f"Total: ${total:.2f}")
                else:
                    st.warning("Name required.")
        else:
            st.warning("Upload menu first.")

    elif choice == "Update Order":
        st.subheader("✅ Mark Order as Delivered")
        if os.path.exists("all_orders.xlsx"):
            df = pd.read_excel("all_orders.xlsx")
            df["Status"] = df.get("Status", "Pending")
            idx = st.selectbox("Select Order", df.index, format_func=lambda i: f"{df.loc[i, 'Customer']} - {df.loc[i, 'Coffee']}")
            if st.button("Mark Delivered"):
                df.at[idx, "Status"] = "Delivered"
                df.to_excel("all_orders.xlsx", index=False)
                st.success("Order status updated.")

    elif choice == "Delete Order":
        st.subheader("🗑 Delete Order")
        if os.path.exists("all_orders.xlsx"):
            df = pd.read_excel("all_orders.xlsx")
            idx = st.selectbox("Select Order", df.index, format_func=lambda i: f"{df.loc[i, 'Customer']} - {df.loc[i, 'Coffee']}")
            if st.button("Delete"):
                df = df.drop(idx).reset_index(drop=True)
                df.to_excel("all_orders.xlsx", index=False)
                st.success("Order deleted.")

    elif choice == "Charts":
        st.subheader("📊 Order Charts")
        if os.path.exists("all_orders.xlsx"):
            df = pd.read_excel("all_orders.xlsx")

            st.markdown("### Filter")
            user_filter = st.text_input("Filter by Customer (optional)")
            if user_filter:
                df = df[df["Customer"].str.contains(user_filter, case=False)]

            date_range = st.date_input("🗓 Filter by Date Range", value=(date.today(), date.today()))
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start, end = date_range
                df['Time'] = pd.to_datetime(df["Time"])
                df = df[(df['Time'].dt.date >= start) & (df['Time'].dt.date <= end)]

            fig = px.bar(df, x="Coffee", y="Qty", color="Customer", title="Coffee Orders")
            st.plotly_chart(fig)

    elif choice == "Reports":
        st.subheader("📋 Sales Report")
        if os.path.exists("all_orders.xlsx"):
            df = pd.read_excel("all_orders.xlsx")
            df["Time"] = pd.to_datetime(df["Time"])
            df["DateOnly"] = df["Time"].dt.date
            df["Month"] = df["Time"].dt.to_period("M")

            today = date.today()
            today_df = df[df["DateOnly"] == today]
            month_df = df[df["Time"].dt.month == today.month]

            today_sales = today_df["Total"].sum()
            month_sales = month_df["Total"].sum()

            st.success(f"💵 Today's Sales ({today}): ${today_sales:.2f}")
            st.info(f"📆 This Month's Sales: ${month_sales:.2f}")

            st.download_button("⬇ Download Daily Report", data=today_df.to_csv(index=False), file_name="daily_report.csv")
            st.download_button("⬇ Download Monthly Report", data=month_df.to_csv(index=False), file_name="monthly_report.csv")

    elif choice == "Order Summary":
        st.subheader("📦 Order Summary")
        if os.path.exists("all_orders.xlsx"):
            df = pd.read_excel("all_orders.xlsx")
            df["Time"] = pd.to_datetime(df["Time"])
            df["DateOnly"] = df["Time"].dt.date

            customer_filter = st.text_input("🔍 Filter by Customer Name")
            date_range = st.date_input("🗓 Date Range", value=(date.today(), date.today()))

            if customer_filter:
                df = df[df["Customer"].str.contains(customer_filter, case=False)]

            if isinstance(date_range, tuple) and len(date_range) == 2:
                start, end = date_range
                df = df[(df["DateOnly"] >= start) & (df["DateOnly"] <= end)]

            st.dataframe(df)
        else:
            st.warning("No orders found.")


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    st.sidebar.success(f"Welcome {st.session_state.email}!")
    coffee_app()
else:
    login_page()
