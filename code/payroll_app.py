"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignment 03. README Step 8 has
# the exact widgets, keys and labels; the tests in tests/test_pipeline.py -k app
# check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster  <- load_employees()                      (fixed; not uploaded)
#   upload  <- st.file_uploader, key="timesheet"     (returns None until chosen)
#   if there is an upload:
#       timesheet <- load_timesheet(upload)
#       payroll   <- build_payroll(timesheet, roster)   one call does all the work
#       the pay period (payroll_date) as a subheader
#       four st.metric cards in st.columns(4) — totals are .sum() on a Series,
#           counts are len() of a boolean-indexed frame
#       st.warning naming the unmatched employee_ids, or st.success if none
#       st.dataframe(payroll) — the lineage table, raw and computed side by side
#       st.download_button, key="download": payroll_export(payroll).to_csv(index=False)
#
# What the page does NOT do: arithmetic on rows, cleaning, merging. If you find
# yourself writing a loop or an apply here, that logic belongs in the package.

import streamlit as st
from payroll.extract import load_employees, load_timesheet
from payroll.compute import build_payroll, payroll_export

roster = load_employees()

st.title("Salt City Coffee Weekly Payroll")

upload = st.file_uploader("Upload weekly timesheet (CSV)", key="timesheet")

if upload:

    # Extract Timesheet + Build Payroll
    timesheet = load_timesheet(upload)
    payroll = build_payroll(timesheet, roster)
    payroll_date = payroll["payroll_date"].max()

    # Payroll Summary
    st.subheader(f"Pay Period Ending {payroll_date}")
    unmatched = payroll[payroll["first_name"].isna()]
    unmatched_employees = unmatched["employee_id"].tolist()
    total_unmatched = len(unmatched_employees)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Employees paid", len(payroll) - len(unmatched))
    col2.metric("Total hours", payroll["hours_worked"].sum())
    col3.metric("Total gross pay", f"${payroll["gross_pay"].sum():,.2f}")
    ot_weeks = (payroll["hours_worked"] > 40).sum()
    col4.metric("Overtime weeks", ot_weeks)

    # Unmatched Employee ID Warning
    if total_unmatched > 0:
        unmatched_ids = ", ".join(
            str(employee) for employee in unmatched_employees
        )
        st.warning(
            f"{total_unmatched} timesheet rows have an employee_id that is not "
            f"on the roster: {unmatched_ids}. "
            "They are NOT in the export -- Add them to HR's roster and re-upload."
        )
    else:
        st.success("All Employee IDs matched successfully.")

    # Display Payroll Table
    st.subheader("Payroll table")
    st.dataframe(payroll, hide_index=True)

    st.download_button("Download payroll CSV for the provider",
                       key="download",
                       data=payroll_export(payroll).to_csv(index=False),
                       file_name=f"payroll_{payroll_date}.csv",
                       mime="text/csv")
