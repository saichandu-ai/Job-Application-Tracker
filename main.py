import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, csv, webbrowser
from datetime import date, datetime

DB = "jobtrack.db"


class JobTrack:
    def __init__(self, root):
        self.root = root
        root.title("JobTrack - Career Manager")
        root.geometry("1150x700")
        root.configure(bg="#f5f6f8")

        self.db()
        self.menu()
        self.dashboard()

    # ---------- DATABASE ----------

    def db(self):
        con = sqlite3.connect(DB)
        con.execute("""
            CREATE TABLE IF NOT EXISTS jobs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT, role TEXT, location TEXT, salary TEXT,
                url TEXT, status TEXT, priority TEXT, applied TEXT,
                interview TEXT, followup TEXT, notes TEXT
            )
        """)
        con.commit()
        con.close()

    def get_jobs(self):
        con = sqlite3.connect(DB)
        data = con.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
        con.close()
        return data

    # ---------- UI ----------

    def menu(self):
        self.side = tk.Frame(self.root, bg="#202d3d", width=210)
        self.side.pack(side="left", fill="y")
        self.side.pack_propagate(False)

        tk.Label(self.side, text="JOBTRACK", bg="#202d3d", fg="white",
                 font=("Arial", 20, "bold")).pack(pady=(30, 2))
        tk.Label(self.side, text="CAREER MANAGER", bg="#202d3d",
                 fg="#aebbc8").pack(pady=(0, 30))

        for name, cmd in [
            ("Dashboard", self.dashboard),
            ("My Applications", self.applications),
            ("Interview Calendar", self.interviews),
            ("Analytics", self.analytics),
            ("Job Opportunities", self.opportunities)
        ]:
            self.nav(name, cmd)

        tk.Button(self.side, text="+ Add Application", command=self.add,
                  bg="#00a896", fg="white", relief="flat",
                  pady=10).pack(fill="x", padx=20, pady=25)

        self.main = tk.Frame(self.root, bg="#f5f6f8")
        self.main.pack(side="left", fill="both", expand=True)

    def nav(self, text, command):
        tk.Button(self.side, text=text, command=command,
                  bg="#202d3d", fg="white", relief="flat",
                  anchor="w", padx=25, pady=11).pack(fill="x")

    def clear(self):
        for w in self.main.winfo_children():
            w.destroy()

    # ---------- DASHBOARD ----------

    def dashboard(self):
        self.clear()
        jobs = self.get_jobs()

        self.title("Dashboard")

        cards = [
            ("Applications", len(jobs)),
            ("Interviews", sum(j[6] == "Interview" for j in jobs)),
            ("Offers", sum(j[6] == "Offer" for j in jobs)),
            ("Follow-ups", self.followups(jobs)),
            ("Rejected", sum(j[6] == "Rejected" for j in jobs))
        ]

        row = tk.Frame(self.main, bg="#f5f6f8")
        row.pack(fill="x", padx=25)

        for name, value in cards:
            box = tk.Frame(row, bg="white", padx=18, pady=15)
            box.pack(side="left", fill="x", expand=True, padx=5)
            tk.Label(box, text=name, bg="white", fg="#777").pack(anchor="w")
            tk.Label(box, text=value, bg="white", fg="#202d3d",
                     font=("Arial", 20, "bold")).pack(anchor="w")

        tk.Label(self.main, text="Application Pipeline", bg="#f5f6f8",
                 fg="#202d3d", font=("Arial", 15, "bold")
                 ).pack(anchor="w", padx=30, pady=(25, 10))

        pipe = tk.Frame(self.main, bg="white")
        pipe.pack(fill="x", padx=30)

        for s in ["Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected"]:
            n = sum(j[6] == s for j in jobs)
            tk.Label(pipe, text=f"{s}\n{n}", bg="white", fg="#333",
                     font=("Arial", 11, "bold"), width=13, pady=15).pack(side="left")

        tk.Label(self.main, text="Next Interviews", bg="#f5f6f8",
                 fg="#202d3d", font=("Arial", 15, "bold")
                 ).pack(anchor="w", padx=30, pady=(25, 8))

        upcoming = []
        for j in jobs:
            if j[9]:
                try:
                    if datetime.strptime(j[9], "%Y-%m-%d").date() >= date.today():
                        upcoming.append(j)
                except ValueError:
                    pass

        if not upcoming:
            tk.Label(self.main, text="No upcoming interviews.",
                     bg="#f5f6f8", fg="#777").pack(anchor="w", padx=35)
        else:
            for j in upcoming[:4]:
                tk.Label(self.main, text=f"{j[1]}  |  {j[2]}  |  {j[9]}",
                         bg="#f5f6f8", fg="#555").pack(anchor="w", padx=35, pady=3)

    def title(self, text):
        tk.Label(self.main, text=text, bg="#f5f6f8", fg="#202d3d",
                 font=("Arial", 23, "bold")).pack(anchor="w", padx=30, pady=25)

    def followups(self, jobs):
        today = date.today()
        count = 0
        for j in jobs:
            if j[10]:
                try:
                    d = datetime.strptime(j[10], "%Y-%m-%d").date()
                    count += d <= today and j[6] not in ["Offer", "Rejected"]
                except ValueError:
                    pass
        return count

    # ---------- APPLICATIONS ----------

    def applications(self):
        self.clear()
        self.title("My Applications")

        top = tk.Frame(self.main, bg="#f5f6f8")
        top.pack(fill="x", padx=30)

        search = tk.Entry(top)
        search.pack(side="left", fill="x", expand=True, ipady=7)
        search.insert(0, "Search company or role...")

        status = ttk.Combobox(
            top,
            values=["All", "Saved", "Applied", "Assessment",
                    "Interview", "Offer", "Rejected"],
            state="readonly", width=14
        )
        status.set("All")
        status.pack(side="left", padx=10)

        table = ttk.Treeview(
            self.main,
            columns=("Company", "Role", "Status", "Priority", "Applied", "Interview"),
            show="headings"
        )

        for c in table["columns"]:
            table.heading(c, text=c)
            table.column(c, width=125)

        table.pack(fill="both", expand=True, padx=30, pady=15)

        def refresh(event=None):
            table.delete(*table.get_children())
            q = search.get().lower()
            if q == "search company or role...":
                q = ""

            for j in self.get_jobs():
                if q and q not in f"{j[1]} {j[2]}".lower():
                    continue
                if status.get() != "All" and j[6] != status.get():
                    continue

                table.insert("", "end", iid=j[0],
                             values=(j[1], j[2], j[6], j[7], j[8], j[9]))

        search.bind("<KeyRelease>", refresh)
        status.bind("<<ComboboxSelected>>", refresh)
        refresh()

        bar = tk.Frame(self.main, bg="#f5f6f8")
        bar.pack(fill="x", padx=30)

        for text, cmd, bg in [
            ("Open Job", lambda: self.open_job(table), "#526777"),
            ("Export CSV", self.export, "#526777"),
        ]:
            tk.Button(bar, text=text, command=cmd, bg=bg, fg="white",
                      relief="flat", padx=15).pack(side="left", padx=2)

        tk.Button(bar, text="Delete", command=lambda: self.delete(table),
                  bg="#d64545", fg="white", relief="flat",
                  padx=18).pack(side="right")

        tk.Button(bar, text="Edit", command=lambda: self.edit(table),
                  bg="#202d3d", fg="white", relief="flat",
                  padx=18).pack(side="right", padx=5)

        table.bind("<Double-1>", lambda e: self.edit(table))

    # ---------- ADD / EDIT ----------

    def add(self, old=None):
        win = tk.Toplevel(self.root)
        win.title("Application")
        win.geometry("430x650")
        win.configure(bg="#f5f6f8")

        fields = [
            ("Company", "company"), ("Role", "role"),
            ("Location", "location"), ("Salary", "salary"),
            ("Job URL", "url"), ("Applied Date", "applied"),
            ("Interview Date", "interview"), ("Follow-up Date", "followup")
        ]

        indexes = {
            "company": 1, "role": 2, "location": 3, "salary": 4,
            "url": 5, "applied": 8, "interview": 9, "followup": 10
        }

        entries = {}

        for label, key in fields:
            tk.Label(win, text=label, bg="#f5f6f8").pack(
                anchor="w", padx=25, pady=(5, 1))
            e = tk.Entry(win)
            e.pack(fill="x", padx=25, ipady=4)

            if old:
                e.insert(0, old[indexes[key]] or "")
            elif key == "applied":
                e.insert(0, str(date.today()))

            entries[key] = e

        def combo(label, values, current):
            tk.Label(win, text=label, bg="#f5f6f8").pack(
                anchor="w", padx=25, pady=(7, 1))
            c = ttk.Combobox(win, values=values, state="readonly")
            c.pack(fill="x", padx=25)
            c.set(current)
            return c

        status = combo(
            "Status",
            ["Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected"],
            old[6] if old else "Applied"
        )

        priority = combo(
            "Priority",
            ["High", "Medium", "Low"],
            old[7] if old else "Medium"
        )

        tk.Label(win, text="Notes", bg="#f5f6f8").pack(
            anchor="w", padx=25, pady=(7, 1))

        notes = tk.Text(win, height=4)
        notes.pack(fill="x", padx=25)

        if old:
            notes.insert("1.0", old[11] or "")

        def save():
            if not entries["company"].get().strip():
                messagebox.showwarning("Error", "Company is required.")
                return
            if not entries["role"].get().strip():
                messagebox.showwarning("Error", "Role is required.")
                return

            values = tuple(e.get() for e in entries.values()) + (
                status.get(), priority.get(),
                notes.get("1.0", "end").strip()
            )

            # reorder to match database
            v = (
                values[0], values[1], values[2], values[3], values[4],
                values[8], values[9], values[5], values[6], values[7], values[10]
            )

            con = sqlite3.connect(DB)

            if old:
                con.execute("""
                    UPDATE jobs SET company=?, role=?, location=?, salary=?,
                    url=?, status=?, priority=?, applied=?, interview=?,
                    followup=?, notes=? WHERE id=?
                """, v + (old[0],))
            else:
                con.execute("""
                    INSERT INTO jobs
                    (company, role, location, salary, url, status,
                     priority, applied, interview, followup, notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, v)

            con.commit()
            con.close()
            win.destroy()
            self.applications()

        tk.Button(win, text="Save Application", command=save,
                  bg="#00a896", fg="white", relief="flat",
                  pady=8).pack(pady=15)

    def selected_job(self, table):
        s = table.selection()
        if not s:
            return None

        con = sqlite3.connect(DB)
        job = con.execute(
            "SELECT * FROM jobs WHERE id=?", (int(s[0]),)
        ).fetchone()
        con.close()
        return job

    def edit(self, table):
        job = self.selected_job(table)
        if job:
            self.add(job)

    def delete(self, table):
        job = self.selected_job(table)
        if not job:
            return

        if messagebox.askyesno("Delete", "Delete this application?"):
            con = sqlite3.connect(DB)
            con.execute("DELETE FROM jobs WHERE id=?", (job[0],))
            con.commit()
            con.close()
            self.applications()

    def open_job(self, table):
        job = self.selected_job(table)

        if not job:
            return

        if job[5]:
            webbrowser.open(job[5])
        else:
            messagebox.showinfo("Job URL", "No URL was saved.")

    # ---------- INTERVIEWS ----------

    def interviews(self):
        self.clear()
        self.title("Interview Calendar")

        jobs = [j for j in self.get_jobs() if j[9]]

        if not jobs:
            tk.Label(self.main, text="No interview dates added yet.",
                     bg="#f5f6f8", fg="#777").pack(anchor="w", padx=35)
            return

        for j in jobs:
            box = tk.Frame(self.main, bg="white", padx=20, pady=12)
            box.pack(fill="x", padx=30, pady=5)

            tk.Label(box, text=f"{j[1]} - {j[2]}", bg="white",
                     fg="#202d3d", font=("Arial", 11, "bold")).pack(anchor="w")
            tk.Label(box, text=f"Interview: {j[9]}   Priority: {j[7]}",
                     bg="white", fg="#666").pack(anchor="w")

            if j[11]:
                tk.Label(box, text="Notes: " + j[11],
                         bg="white", fg="#777").pack(anchor="w")

    # ---------- ANALYTICS ----------

    def analytics(self):
        self.clear()
        self.title("Analytics")

        jobs = self.get_jobs()
        total = len(jobs)

        if not total:
            tk.Label(self.main, text="Add applications to see analytics.",
                     bg="#f5f6f8", fg="#777").pack(anchor="w", padx=35)
            return

        applied = sum(j[6] in [
            "Applied", "Assessment", "Interview", "Offer", "Rejected"
        ] for j in jobs)

        interviews = sum(j[6] == "Interview" for j in jobs)
        offers = sum(j[6] == "Offer" for j in jobs)

        rate = lambda n: f"{round(n / applied * 100) if applied else 0}%"

        data = [
            ("Total Applications", total),
            ("Applications Submitted", applied),
            ("Interview Rate", rate(interviews)),
            ("Response Rate", rate(interviews + offers)),
            ("Offer Rate", rate(offers))
        ]

        for name, value in data:
            box = tk.Frame(self.main, bg="white", padx=20, pady=15)
            box.pack(fill="x", padx=30, pady=5)

            tk.Label(box, text=name, bg="white",
                     fg="#666").pack(side="left")
            tk.Label(box, text=value, bg="white", fg="#202d3d",
                     font=("Arial", 12, "bold")).pack(side="right")

    # ---------- OPPORTUNITIES ----------

    def opportunities(self):
        self.clear()
        self.title("Job Opportunities")

        tk.Label(
            self.main,
            text="Real opportunities can be loaded from a job API.",
            bg="#f5f6f8", fg="#666"
        ).pack(anchor="w", padx=35)

        tk.Label(
            self.main,
            text="No fake companies or jobs are shown.",
            bg="#f5f6f8", fg="#888"
        ).pack(anchor="w", padx=35, pady=8)

        tk.Button(
            self.main, text="Add Opportunity Manually",
            command=self.add, bg="#00a896", fg="white",
            relief="flat", padx=20, pady=8
        ).pack(anchor="w", padx=35, pady=15)

    # ---------- EXPORT ----------

    def export(self):
        jobs = self.get_jobs()

        if not jobs:
            messagebox.showinfo("Export", "No applications to export.")
            return

        with open("jobtrack_export.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Company", "Role", "Location", "Salary",
                "Status", "Priority", "Applied",
                "Interview", "Follow-up", "Notes"
            ])

            for j in jobs:
                writer.writerow([
                    j[1], j[2], j[3], j[4], j[6],
                    j[7], j[8], j[9], j[10], j[11]
                ])

        messagebox.showinfo("Export", "Applications exported to CSV.")


root = tk.Tk()
JobTrack(root)
root.mainloop()