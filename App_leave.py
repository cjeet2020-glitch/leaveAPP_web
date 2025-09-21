import streamlit as st
import pandas as pd
import datetime
import os

BALANCE_CSV = r"C:\Users\Chandrajeet\ERP\project_code\leaveBalance.csv"
HISTORY_CSV = r"C:\Users\Chandrajeet\ERP\project_code\leave_History.csv"

def load_leave_data():
    df = pd.read_csv(BALANCE_CSV)
    df['name'] = df['name'].str.lower().str.strip()
    return df

def load_history():
    expected_cols = [
        "name", "leave_type", "from_date", "to_date",
        "reason", "status", "manager_email", "applied_on"
    ]
    if os.path.exists(HISTORY_CSV):
        df = pd.read_csv(HISTORY_CSV)
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
        return df[expected_cols]
    else:
        return pd.DataFrame(columns=expected_cols)

def save_leave_data(df):
    df.to_csv(BALANCE_CSV, index=False)

def save_history(history_df):
    history_df.to_csv(HISTORY_CSV, index=False)

def count_leave_days(start_date, end_date):
    delta_days = (end_date - start_date).days + 1
    leave_days = 0
    for i in range(delta_days):
        day = start_date + datetime.timedelta(days=i)
        if day.weekday() != 6:  # Exclude Sundays
            leave_days += 1
    return leave_days

# ---------- App ----------
st.markdown(
    "<h2 style='background-color:#d8efd8; text-align:center; padding:10px;'>"
    "<span style='color:#2b2b2b;'><b>leave</b></span><span style='color:#1a7e1a; font-style:italic;'><b>APP</b></span> Dashboard</h2>",
    unsafe_allow_html=True
)

df = load_leave_data()
history_df = load_history()

# --- Layout Sequence ---
# 1. Name
st.markdown("<div style='border:1px solid #222; padding:8px; background-color:#f5f5f5;'><b>Name</b></div>", unsafe_allow_html=True)
selected_name = st.selectbox("", df['name'].tolist(), key="employee_name")

# 2. Show Leave Balance (updates after apply)
if "current_balance" not in st.session_state or st.session_state.get("last_name") != selected_name:
    emp_row = df[df['name'] == selected_name].iloc[0]
    st.session_state.current_balance = {
        "CL": emp_row["CL"],
        "SL": emp_row["SL"],
        "EL": emp_row["EL"]
    }
    st.session_state.last_name = selected_name

cb = st.session_state.current_balance
st.markdown("<div style='border:1px solid #222; padding:8px; background-color:#f5f5f5;'><b>Current Leave Balance</b></div>", unsafe_allow_html=True)
st.markdown(
    f"""
    <table style='width:100%;text-align:center;'>
        <tr>
            <th>CL</th><th>SL</th><th>EL</th>
        </tr>
        <tr>
            <td>{cb['CL']}</td><td>{cb['SL']}</td><td>{cb['EL']}</td>
        </tr>
    </table>
    """, unsafe_allow_html=True
)

# 3. Leave Type, From Date, To Date, Apply Button, Reason in one row
row = st.columns([2, 2, 2, 2])
with row[0]:
    st.markdown("<div style='border:1px solid #222; padding:8px; background-color:#f5f5f5;'><b>Leave Type</b></div>", unsafe_allow_html=True)
    leave_types = [lt for lt in ["CL", "SL", "EL"] if cb[lt] > 0]
    leave_type = st.selectbox("", leave_types, key="leave_type")
with row[1]:
    st.markdown("<div style='border:1px solid #222; padding:8px; background-color:#f5f5f5;'><b>From Date</b></div>", unsafe_allow_html=True)
    from_date = st.date_input("", datetime.date.today(), key="from_date")
with row[2]:
    st.markdown("<div style='border:1px solid #222; padding:8px; background-color:#f5f5f5;'><b>To Date</b></div>", unsafe_allow_html=True)
    to_date = st.date_input("", datetime.date.today(), key="to_date")
with row[3]:
    st.markdown("<div style='border:1px solid #222; padding:8px; background-color:#f5f5f5; height:50px; display:flex; align-items:center; justify-content:center;'>", unsafe_allow_html=True)
    apply_clicked = st.button("Apply", key="apply_btn")
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #e60000;
            color: white;
            font-weight: bold;
            height: 80px;
            width: 200%;
            font-size: 24px;
            border-radius: 6px;
        }
        </style>
        """, unsafe_allow_html=True
    )

# Reason input (same width as To Date)
reason_row = st.columns([6, 2])
with reason_row[0]:
    st.markdown("<div style='border:1px solid #222; padding:1px; background-color:#f5f5f5;'><b>Reason</b></div>", unsafe_allow_html=True)
    reason = st.text_input("", key="reason")
with reason_row[1]:
    st.markdown("")  # Empty to keep alignment

# 4. Apply Logic & Update Balance
if apply_clicked:
    if from_date > to_date:
        st.error("From Date cannot be after To Date")
        st.stop()

    start_date = datetime.datetime.combine(from_date, datetime.time())
    end_date = datetime.datetime.combine(to_date, datetime.time())
    leave_days = count_leave_days(start_date, end_date)
    closing_balance = cb[leave_type] - leave_days

    if closing_balance < 0:
        st.error("Insufficient Leave Balance")
        status = "Rejected"
    else:
        status = "Approved"
        st.success("Leave request submitted and approved.")

        # Update leave balance in CSV and session state
        df.loc[df['name'] == selected_name, leave_type] = closing_balance
        save_leave_data(df)
        st.session_state.current_balance[leave_type] = closing_balance

    # Save to history
    emp_row = df[df['name'] == selected_name].iloc[0]
    new_row = {
        "name": selected_name,
        "leave_type": leave_type,
        "from_date": from_date.strftime("%d-%m-%Y"),
        "to_date": to_date.strftime("%d-%m-%Y"),
        "reason": reason,
        "status": status,
        "manager_email": emp_row['manager_email'],
        "applied_on": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    history_df = pd.concat([history_df, pd.DataFrame([new_row])], ignore_index=True)
    save_history(history_df)
    st.rerun()

# 6. Leave History (last 10 for selected employee)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div style='background-color:#eaeaea; padding:10px; border:1px solid #222;'><b>Leave History</b></div>", unsafe_allow_html=True)
emp_history = history_df[history_df['name'] == selected_name].sort_values("applied_on", ascending=False).head(10)
if not emp_history.empty:
    show_df_display = emp_history[["leave_type", "from_date", "to_date", "reason", "status", "applied_on"]]
    st.dataframe(show_df_display, width='stretch')
else:
    st.info("No leave history records found for this employee.")